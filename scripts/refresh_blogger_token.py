"""
Blogger OAuth Token Refresher (Auto)
=====================================
当 BLOGGER_REFRESH_TOKEN 失效时运行此脚本，全自动完成：
1. 本地起 HTTP 服务器捕获 OAuth 回调
2. 打开浏览器授权 Google 账号
3. 自动提取授权码、换取新 refresh_token
4. 更新本地 blogger_tokens.json
5. 推送到 GitHub Actions Secret

Usage（设置好 GITHUB_TOKEN 后直接运行）：
    $env:GITHUB_TOKEN="ghp_xxxx"
    cd D:\小程序\aitoolbits-blogger
    python scripts/refresh_blogger_token.py
"""

import json
import sys
import os
import webbrowser
import urllib.request
import urllib.parse
import ssl
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKENS_FILE = PROJECT_ROOT / "blogger_tokens.json"

# 本地回调服务器端口
PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER = "iambuluo"
REPO_NAME = "aitoolbits-blogger"

# 全局变量：收到回调后存储授权码
auth_code = None
auth_event = threading.Event()


class OAuthHandler(BaseHTTPRequestHandler):
    """处理 Google OAuth 回调：提取 code 参数"""

    def do_GET(self):
        global auth_code

        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding-top: 80px;">
            <h2 style="color: #34A853;">授权成功 ✓</h2>
            <p>正在自动更新 Refresh Token...</p>
            <p style="color: #999;">可以关闭此页面了</p>
            </body></html>
            """.encode())
            auth_event.set()
        else:
            error = params.get("error", ["unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h2>授权失败</h2><p>{error}</p>".encode())
            auth_event.set()

    def log_message(self, format, *args):
        pass  # 不打印 HTTP 日志


def load_tokens():
    if not TOKENS_FILE.exists():
        print(f"ERROR: {TOKENS_FILE} not found!")
        sys.exit(1)
    with open(TOKENS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_tokens(tokens: dict):
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {TOKENS_FILE}")


def get_auth_url(client_id: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/blogger",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"ERROR exchanging code: HTTP {e.code}")
        print(f"Response: {body}")
        sys.exit(1)


def update_github_secret(name: str, value: str):
    """Update a single GitHub Actions Secret."""
    import base64

    try:
        from nacl import encoding, public
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynacl", "--quiet"])
        from nacl import encoding, public

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "aitoolbits-blogger",
    }

    # Get public key
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/public-key"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        pubkey_data = json.loads(resp.read().decode())

    # Encrypt
    pubkey_bytes = base64.b64decode(pubkey_data["key"])
    sealed_box = public.SealedBox(public.PublicKey(pubkey_bytes))
    encrypted = base64.b64encode(sealed_box.encrypt(value.encode("utf-8"))).decode("utf-8")

    # Put
    payload = json.dumps({
        "encrypted_value": encrypted,
        "key_id": pubkey_data["key_id"],
    }).encode("utf-8")

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/{name}"
    put_req = urllib.request.Request(url, data=payload, headers=headers, method="PUT")
    put_req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(put_req, timeout=15) as resp:
            print(f"  GitHub Secret {name} updated OK")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  ERROR updating {name}: HTTP {e.code} {body[:200]}")
        return False


def main():
    global auth_code

    print("=" * 55)
    print("  Blogger OAuth Token Refresher (Auto)")
    print("=" * 55)
    print()

    # Load existing tokens
    tokens = load_tokens()
    client_id = tokens.get("BLOGGER_CLIENT_ID", "")
    client_secret = tokens.get("BLOGGER_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        print("ERROR: BLOGGER_CLIENT_ID or BLOGGER_CLIENT_SECRET missing in blogger_tokens.json")
        sys.exit(1)

    print(f"Client ID: {client_id[:30]}...")
    print()

    # 启动本地 HTTP 服务器捕获回调
    print(f"Starting local callback server on http://localhost:{PORT} ...")
    server = HTTPServer(("127.0.0.1", PORT), OAuthHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    # 打开浏览器
    auth_url = get_auth_url(client_id)
    print()
    print("Opening browser for Google authorization...")
    print(f"  Redirect: {REDIRECT_URI}")
    print()
    webbrowser.open(auth_url)

    print("  Waiting for authorization... (timeout: 120s)")
    print()

    # 等用户授权
    if not auth_event.wait(timeout=120):
        print("ERROR: Authorization timeout! No response in 120 seconds.")
        server.shutdown()
        sys.exit(1)

    server.shutdown()

    if not auth_code:
        print("ERROR: No authorization code received!")
        sys.exit(1)

    print("  Authorization code received!")
    print()

    # 兑换 token
    print("Exchanging code for new tokens...")
    result = exchange_code(client_id, client_secret, auth_code)

    new_refresh_token = result.get("refresh_token", "")
    access_token = result.get("access_token", "")

    if not new_refresh_token:
        print("ERROR: No refresh_token in response!")
        print(f"Response keys: {list(result.keys())}")
        sys.exit(1)

    print(f"  New refresh_token: {new_refresh_token[:20]}...")
    print(f"  Access token: {access_token[:20]}...")
    print()

    # 更新本地文件
    print("Updating blogger_tokens.json...")
    tokens["BLOGGER_REFRESH_TOKEN"] = new_refresh_token
    save_tokens(tokens)
    print()

    # 推送到 GitHub
    if GITHUB_TOKEN:
        print("Pushing new token to GitHub Actions Secret...")
        ok = update_github_secret("BLOGGER_REFRESH_TOKEN", new_refresh_token)
    else:
        print("WARNING: GITHUB_TOKEN env var not set. Skipping GitHub Secret update.")
        print("Set it first: $env:GITHUB_TOKEN=\"ghp_xxxx\"")
        ok = False

    print()
    print("=" * 55)
    if ok:
        print("  Done! New refresh token is active (production mode).")
        print()
        print("  Workflows should now run without re-auth.")
        print("  https://github.com/iambuluo/aitoolbits-blogger/actions")
    else:
        print("  Token saved locally.")
        print("  Run again with GITHUB_TOKEN set to push to GitHub:")
        print("    $env:GITHUB_TOKEN=\"ghp_xxxx\"")
        print("    python scripts/refresh_blogger_token.py")
    print("=" * 55)


if __name__ == "__main__":
    main()

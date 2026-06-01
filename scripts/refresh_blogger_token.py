"""
Blogger OAuth Token Refresher
==============================
当 BLOGGER_REFRESH_TOKEN 失效（HTTP 400）时运行此脚本。

步骤：
1. 读取 blogger_tokens.json 中的 client_id / client_secret
2. 打开浏览器让你重新授权 Google 账号
3. 用授权码换取新的 refresh_token
4. 更新 blogger_tokens.json
5. 自动把新 token 推送到 GitHub Actions Secret

Usage:
    cd D:\\小程序\\aitoolbits-blogger
    python scripts/refresh_blogger_token.py
"""

import json
import sys
import os
import webbrowser
import urllib.request
import urllib.parse
import ssl
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOKENS_FILE = PROJECT_ROOT / "blogger_tokens.json"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # set via env: $env:GITHUB_TOKEN="your_pat"
REPO_OWNER = "iambuluo"
REPO_NAME = "aitoolbits-blogger"


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
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/blogger",
        "access_type": "offline",
        "prompt": "consent",  # force new refresh_token
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
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
    print("=" * 55)
    print("  Blogger OAuth Token Refresher")
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

    # Step 1: Open browser for re-auth
    auth_url = get_auth_url(client_id)
    print("Step 1: Opening browser for Google authorization...")
    print()
    print(f"  URL: {auth_url}")
    print()
    webbrowser.open(auth_url)

    print("  A browser window should have opened.")
    print("  Log in with your Google account (the one that owns aitoolbits.blogspot.com)")
    print("  Click 'Allow', then copy the authorization code shown on the page.")
    print()

    code = input("  Paste the authorization code here: ").strip()
    if not code:
        print("No code entered. Aborting.")
        sys.exit(1)

    # Step 2: Exchange code for tokens
    print()
    print("Step 2: Exchanging code for new tokens...")
    result = exchange_code(client_id, client_secret, code)

    new_refresh_token = result.get("refresh_token", "")
    access_token = result.get("access_token", "")

    if not new_refresh_token:
        print("ERROR: No refresh_token in response!")
        print(f"Response keys: {list(result.keys())}")
        sys.exit(1)

    print(f"  New refresh_token: {new_refresh_token[:20]}...")
    print(f"  Access token: {access_token[:20]}...")

    # Step 3: Update blogger_tokens.json
    print()
    print("Step 3: Updating blogger_tokens.json...")
    tokens["BLOGGER_REFRESH_TOKEN"] = new_refresh_token
    save_tokens(tokens)

    # Step 4: Push to GitHub Secret
    print()
    print("Step 4: Pushing new token to GitHub Actions Secret...")
    ok = update_github_secret("BLOGGER_REFRESH_TOKEN", new_refresh_token)

    print()
    print("=" * 55)
    if ok:
        print("  Done! New refresh token is active.")
        print()
        print("  Next: Go to GitHub Actions and re-run the failed workflow:")
        print("  https://github.com/iambuluo/aitoolbits-blogger/actions")
    else:
        print("  Token saved locally but GitHub Secret update failed.")
        print("  Please manually update BLOGGER_REFRESH_TOKEN in GitHub Secrets.")
    print("=" * 55)


if __name__ == "__main__":
    main()

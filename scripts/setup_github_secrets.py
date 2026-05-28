"""
GitHub Secrets Setup — one-shot configuration for aitoolbits-blogger.

Reads local credentials and pushes them to GitHub Actions Secrets via REST API.
Requires: pip install pynacl requests

Usage:
    python scripts/setup_github_secrets.py
"""

import json
import os
import sys
import base64
import re
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests

try:
    from nacl import encoding, public
except ImportError:
    print("Installing PyNaCl...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pynacl", "--quiet"])
    from nacl import encoding, public


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_OWNER = "iambuluo"
REPO_NAME = "aitoolbits-blogger"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"


def encrypt_secret(public_key_str: str, secret_value: str) -> str:
    """Encrypt a secret value using the repo's public key (libsodium sealed box)."""
    public_key_bytes = base64.b64decode(public_key_str)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def get_github_token() -> str:
    """Try to get a GitHub token via multiple methods."""
    # Method 1: Environment variable
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        print("  Using GITHUB_TOKEN from environment")
        return token

    # Method 2: gh CLI
    import subprocess
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            print("  Using token from gh CLI")
            return result.stdout.strip()
    except Exception:
        pass

    return None


def set_secret(token: str, name: str, value: str) -> bool:
    """Set a single GitHub Actions secret."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Get public key
    resp = requests.get(f"{API_BASE}/actions/secrets/public-key", headers=headers)
    if resp.status_code != 200:
        print(f"  ERROR: Cannot get public key: {resp.status_code} {resp.text[:200]}")
        return False

    pubkey = resp.json()
    encrypted = encrypt_secret(pubkey["key"], value)

    # Set secret
    resp = requests.put(
        f"{API_BASE}/actions/secrets/{name}",
        headers=headers,
        json={"encrypted_value": encrypted, "key_id": pubkey["key_id"]},
    )
    if resp.status_code in (201, 204):
        return True
    else:
        print(f"  ERROR setting {name}: {resp.status_code} {resp.text[:200]}")
        return False


def main():
    print("=" * 55)
    print("  aitoolbits-blogger — GitHub Secrets Setup")
    print("=" * 55)
    print()

    # ── Step 1: Get GitHub token ──
    print("Step 1: GitHub authentication")
    token = get_github_token()

    if not token:
        print()
        print("  No GitHub token found. You need a Personal Access Token.")
        print()
        print("  Create one now:")
        print("  1. Open https://github.com/settings/tokens")
        print("  2. Click 'Generate new token' → 'Generate new token (classic)'")
        print("  3. Note: 'Fine-grained tokens' with 'Actions' → 'Read and write' also work")
        print("  3. Check 'repo' scope (for classic) or select repository access (for fine-grained)")
        print("  4. Copy the generated token")
        print()
        token = input("  Paste your GitHub token: ").strip()

    if not token:
        print("  No token provided. Aborting.")
        return

    # Validate token
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(f"{API_BASE}", headers=headers)
    if resp.status_code != 200:
        print(f"  Token validation failed: {resp.status_code}")
        print(f"  Response: {resp.text[:300]}")
        return
    print(f"  Authenticated as: {resp.json().get('owner', {}).get('login', 'unknown')}")
    print()

    # ── Step 2: Read credentials ──
    print("Step 2: Reading local credentials")

    # Read Blogger tokens
    tokens_file = PROJECT_ROOT / "blogger_tokens.json"
    if not tokens_file.exists():
        print(f"  ERROR: {tokens_file} not found!")
        return

    with open(tokens_file) as f:
        tokens = json.load(f)

    # Read Pexels key
    env_file = PROJECT_ROOT / ".env.local"
    pexels_key = ""
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                m = re.match(r"PEXELS_API_KEY=(.+)", line.strip())
                if m:
                    pexels_key = m.group(1).strip()
                    break

    # Define all secrets to set
    secrets = {
        "BLOGGER_CLIENT_ID": tokens.get("BLOGGER_CLIENT_ID", ""),
        "BLOGGER_CLIENT_SECRET": tokens.get("BLOGGER_CLIENT_SECRET", ""),
        "BLOGGER_REFRESH_TOKEN": tokens.get("BLOGGER_REFRESH_TOKEN", ""),
        "BLOGGER_BLOG_ID": tokens.get("BLOGGER_BLOG_ID", ""),
        "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
        "AD_PROVIDER": "monetag",
        "AD_ZONE_ID": "229646",
        "PEXELS_API_KEY": pexels_key,
    }

    # Check for DeepSeek key
    if not secrets["DEEPSEEK_API_KEY"]:
        print()
        print("  DeepSeek API key not found in environment.")
        deepseek_key = input("  Enter your DEEPSEEK_API_KEY: ").strip()
        if deepseek_key:
            secrets["DEEPSEEK_API_KEY"] = deepseek_key

    print(f"  Found {sum(1 for v in secrets.values() if v)} / {len(secrets)} secrets to set")
    print()

    # ── Step 3: Push secrets ──
    print("Step 3: Setting GitHub Secrets")
    success = 0
    failed = 0

    for name, value in secrets.items():
        if not value:
            print(f"  SKIP {name}: empty value")
            continue

        print(f"  Setting {name}...", end=" ")
        if set_secret(token, name, value):
            print("OK")
            success += 1
        else:
            print("FAILED")
            failed += 1

    print()
    print("=" * 55)
    print(f"  Done: {success} set, {failed} failed")
    print()
    if success >= 5:
        print("  GitHub Actions automation is now ready!")
        print()
        print("  Next steps:")
        print("  1. Go to https://github.com/iambuluo/aitoolbits-blogger/actions")
        print('  2. Click "Auto Publish Blog Articles" → "Run workflow"')
        print("  3. Set article_count=1 and click Run")
        print()
        print("  The first automated article will also run at:")
        print("    Beijing 08:17, 14:42, or 21:08")
    else:
        print("  WARNING: Some secrets failed. Check the errors above.")
    print("=" * 55)


if __name__ == "__main__":
    main()

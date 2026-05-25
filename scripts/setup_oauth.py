"""
One-time OAuth setup script for Blogger API.
Run this locally to get your tokens, then add them to GitHub Secrets.
"""

import json
import os
import sys
import webbrowser

try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    print("ERROR: This script requires Python 3 with urllib support.")
    sys.exit(1)

# OAuth configuration
SCOPES = "https://www.googleapis.com/auth/blogger"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
BLOGGER_API_URL = "https://www.googleapis.com/blogger/v3/blogs/byurl"


def create_auth_url(client_id: str) -> str:
    """Generate OAuth authorization URL."""
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    })
    return f"{AUTH_URL}?{params}"


def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange authorization code for tokens."""
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_blog_id(access_token: str, blog_url: str) -> str:
    """Get blog ID from blog URL."""
    url = f"{BLOGGER_API_URL}?url={urllib.parse.quote(blog_url)}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["id"]


def main():
    print("=" * 60)
    print("  Blogger API - OAuth Setup Wizard")
    print("  For: aitoolbits.blogspot.com")
    print("=" * 60)
    print()

    print("STEP 1: Enter your Google OAuth credentials")
    print("-" * 40)
    print("If you haven't created them yet, follow these steps:")
    print("  1. Go to https://console.cloud.google.com")
    print("  2. Create a new project (or select existing)")
    print("  3. Go to 'APIs & Services' > 'Library'")
    print("  4. Search for 'Blogger API' and ENABLE it")
    print("  5. Go to 'APIs & Services' > 'Credentials'")
    print("  6. Click 'Create Credentials' > 'OAuth client ID'")
    print("  7. Application type: 'Desktop app'")
    print("  8. Name: 'Blogger Auto Publisher'")
    print("  9. Click 'Create' and copy Client ID + Secret")
    print()

    client_id = input("  Client ID: ").strip()
    client_secret = input("  Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\nERROR: Client ID and Secret are required!")
        sys.exit(1)

    # Step 2: Authorization
    print()
    print("STEP 2: Authorize your Google account")
    print("-" * 40)

    auth_url = create_auth_url(client_id)
    print(f"\n  Opening browser for authorization...")
    print(f"  URL: {auth_url}")
    print()

    try:
        webbrowser.open(auth_url)
    except Exception:
        print("  Could not open browser. Please copy the URL above and open it manually.")

    print("\n  After granting permission, you'll see an authorization code.")
    print("  Copy and paste it below:")
    print()

    code = input("  Authorization code: ").strip()

    if not code:
        print("\nERROR: Authorization code is required!")
        sys.exit(1)

    # Step 3: Exchange tokens
    print()
    print("STEP 3: Exchanging code for tokens...")
    print("-" * 40)

    try:
        tokens = exchange_code(client_id, client_secret, code)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"\nERROR: Token exchange failed (HTTP {e.code})")
        print(f"  {body}")
        print("\nMake sure:")
        print("  - Blogger API is enabled in Google Cloud Console")
        print("  - The authorization code is correct (not expired)")
        print("  - Client ID and Secret match")
        sys.exit(1)

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        print("\nERROR: No access token received!")
        print(f"  Response: {json.dumps(tokens, indent=2)}")
        sys.exit(1)

    print(f"  Access token:  {access_token[:20]}...")
    print(f"  Refresh token: {refresh_token[:20]}..." if refresh_token else "  WARNING: No refresh token received!")

    if not refresh_token:
        print("\n  CRITICAL: Without a refresh token, the automation won't work!")
        print("  Make sure you used 'access_type=offline' and 'prompt=consent'.")
        sys.exit(1)

    # Step 4: Get blog ID
    print()
    print("STEP 4: Getting blog ID...")
    print("-" * 40)

    try:
        blog_id = get_blog_id(access_token, "https://aitoolbits.blogspot.com/")
        print(f"  Blog ID: {blog_id}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"\nERROR: Could not get blog ID (HTTP {e.code})")
        print(f"  {body}")
        print("\nMake sure:")
        print("  - The blog 'aitoolbits' exists and is accessible")
        print("  - Blogger API is enabled")
        sys.exit(1)

    # Step 5: Summary
    print()
    print("=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Add these as GitHub Repository Secrets:")
    print("(Go to: GitHub repo > Settings > Secrets and variables > Actions)")
    print()
    print(f"  BLOGGER_CLIENT_ID     = {client_id}")
    print(f"  BLOGGER_CLIENT_SECRET = {client_secret}")
    print(f"  BLOGGER_REFRESH_TOKEN = {refresh_token}")
    print(f"  BLOGGER_BLOG_ID       = {blog_id}")
    print()
    print("You also need:")
    print(f"  DEEPSEEK_API_KEY      = your_deepseek_api_key")
    print()
    print("Get your DeepSeek API key from: https://platform.deepseek.com/api_keys")
    print()
    print("After setting secrets, push to GitHub and the automation will run!")
    print("=" * 60)

    # Save locally for reference (do NOT commit this!)
    config = {
        "blog_id": blog_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "token.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"\nConfig saved to: {config_path}")
    print("IMPORTANT: This file is in .gitignore and will NOT be committed.")


if __name__ == "__main__":
    main()

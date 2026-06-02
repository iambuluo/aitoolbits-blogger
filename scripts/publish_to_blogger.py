"""
Blogger API v3 publisher.
Posts articles to aitoolbits.blogspot.com using OAuth 2.0.
"""

import os
import json
import time
import random
from datetime import datetime


# ==================== OAuth 2.0 Helpers ====================

def get_access_token(
    client_id: str, client_secret: str, refresh_token: str,
    on_new_refresh: callable = None,
) -> str:
    """
    Exchange refresh token for a new access token.
    
    Handles Google OAuth token rotation: if Google returns a new refresh_token
    in the response (token rotation), calls on_new_refresh(new_token) to persist it.
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        refresh_token: Current refresh token
        on_new_refresh: Callback(new_refresh_token) when Google rotates the token.
                        If not provided, prints a warning.
    """
    import urllib.request
    import urllib.parse
    import ssl

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        
        # Handle token rotation: Google may return a NEW refresh_token.
        # If we don't save it, the old one will be invalidated next time.
        new_refresh = result.get("refresh_token")
        if new_refresh:
            if on_new_refresh:
                on_new_refresh(new_refresh)
            else:
                print("  ⚠ WARNING: Google returned a new refresh_token (token rotation).")
                print("  ⚠ The old refresh_token will become invalid!")
                print(f"  ⚠ Please update BLOGGER_REFRESH_TOKEN to: {new_refresh[:20]}...")
        
        return result["access_token"]


def _try_auto_save_refresh_token(new_token: str) -> bool:
    """
    Attempt to auto-save a rotated refresh token.
    
    Tries in order:
    1. Update GitHub Actions Secret (if GITHUB_TOKEN env var is set)
    2. Save to blogger_tokens.json locally
    
    Returns True if saved successfully.
    """
    github_token = os.environ.get("GITHUB_TOKEN", "")
    
    # Strategy 1: Update GitHub Actions Secret
    if github_token:
        import base64
        try:
            _update_github_secret("BLOGGER_REFRESH_TOKEN", new_token, github_token)
            print("  ✅ Refresh token auto-saved to GitHub Secrets!")
            return True
        except Exception as e:
            print(f"  ⚠ Failed to update GitHub Secret: {e}")
    
    # Strategy 2: Save to local token file
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json")
    try:
        if os.path.exists(token_file):
            with open(token_file, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            tokens["BLOGGER_REFRESH_TOKEN"] = new_token
            with open(token_file, "w", encoding="utf-8") as f:
                json.dump(tokens, f, indent=2)
            print(f"  ✅ Refresh token saved to {token_file}")
            return True
    except Exception:
        pass
    
    # Fallback: print token for manual update
    print(f"  ⚠ Could not auto-save. Please manually update BLOGGER_REFRESH_TOKEN:")
    print(f"  ⚠   {new_token}")
    return False


def _update_github_secret(secret_name: str, secret_value: str, github_token: str):
    """Update a GitHub Actions secret via the API."""
    import base64
    
    repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "iambuluo")
    repo_name = "aitoolbits-blogger"
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "aitoolbits-blogger",
    }
    
    # Step 1: Get public key
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/public-key"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        pubkey = json.loads(resp.read().decode())
    
    # Step 2: Encrypt with PyNaCl
    from nacl import encoding, public
    pubkey_bytes = base64.b64decode(pubkey["key"])
    sealed_box = public.SealedBox(public.PublicKey(pubkey_bytes))
    encrypted = base64.b64encode(
        sealed_box.encrypt(secret_value.encode("utf-8"))
    ).decode("utf-8")
    
    # Step 3: Update secret
    payload = json.dumps({
        "encrypted_value": encrypted,
        "key_id": pubkey["key_id"],
    }).encode("utf-8")
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"
    put_req = urllib.request.Request(url, data=payload, headers=headers, method="PUT")
    put_req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(put_req, timeout=15):
        pass


def create_auth_url(client_id: str) -> str:
    """Generate the OAuth authorization URL for first-time setup."""
    params = {
        "client_id": client_id,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/blogger",
        "access_type": "offline",
        "prompt": "consent",
    }
    import urllib.parse
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    import urllib.request
    import urllib.parse

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

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ==================== Blogger API ====================

BLOG_URL = "https://www.googleapis.com/blogger/v3/blogs"


def publish_article(
    access_token: str,
    blog_id: str,
    title: str,
    content: str,
    labels: list = None,
    search_description: str = None,
    is_draft: bool = False,
) -> dict:
    """Publish an article to Blogger.

    Args:
        access_token: Valid OAuth access token
        blog_id: Blogger blog ID
        title: Article title
        content: HTML content
        labels: List of label strings
        search_description: Meta description for SEO (150-160 chars)
        is_draft: If True, save as draft

    Returns:
        API response dict
    """
    import urllib.request

    url = f"{BLOG_URL}/{blog_id}/posts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "kind": "blogger#post",
        "title": title,
        "content": content,
        "labels": labels or [],
    }
    # Add search description if provided (SEO meta description)
    if search_description:
        payload["searchDescription"] = search_description

    if is_draft:
        url += "?isDraft=true"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        import ssl
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "post_id": result.get("id"),
                "url": result.get("url"),
                "title": title,
            }
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            error_msg = e.read().decode("utf-8") if e.fp else error_msg
        return {
            "success": False,
            "title": title,
            "error": error_msg,
        }


def get_blog_id(access_token: str) -> str:
    """Get the blog ID for the authenticated user's blog."""
    import urllib.request

    url = f"{BLOG_URL}/byurl?url=https://aitoolbits.blogspot.com/"
    headers = {"Authorization": f"Bearer {access_token}"}
    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["id"]


# ==================== Main Pipeline ====================

def run_pipeline(count: int = 1, is_draft: bool = False):
    """Main pipeline: generate articles and publish to Blogger."""

    # Load credentials from environment
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    missing = []
    if not client_id:
        missing.append("BLOGGER_CLIENT_ID")
    if not client_secret:
        missing.append("BLOGGER_CLIENT_SECRET")
    if not refresh_token:
        missing.append("BLOGGER_REFRESH_TOKEN")
    if not deepseek_key:
        missing.append("DEEPSEEK_API_KEY")
    if not blog_id:
        missing.append("BLOGGER_BLOG_ID")

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        raise SystemExit(1)

    # Get fresh access token (with auto token-rotation handling)
    print("Authenticating with Blogger API...")
    
    def _handle_token_rotation(new_token: str):
        """Auto-save rotated refresh token to GitHub Secrets when possible."""
        print(f"  🔄 Google rotated the refresh token. Auto-saving...")
        _try_auto_save_refresh_token(new_token)
    
    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_handle_token_rotation,
    )
    print("  Access token obtained.")

    # Generate articles
    print(f"\nGenerating {count} article(s)...")
    from generate_article import generate_multiple, insert_images
    articles = generate_multiple(count, deepseek_key)

    # Fetch and insert images (requires PEXELS_API_KEY, optional)
    pexels_key = os.environ.get("PEXELS_API_KEY")
    if pexels_key:
        print("\nFetching article images...")
        from image_fetcher import fetch_article_images
        for article in articles:
            topic_info = {
                "title": article["title"],
                "category": article["category"],
                "keywords": article["keywords"],
            }
            images = fetch_article_images(topic_info, count=3)
            if images:
                article["content"] = insert_images(article["content"], images)
                print(f"  Images added: {len(images)} for \"{article['title'][:40]}...\"")
            else:
                print(f"  No images found for: \"{article['title'][:40]}...\"")
    else:
        print("\n  No PEXELS_API_KEY set, skipping images (articles will be text-only)")

    # Publish with randomized delay between posts
    results = []
    for i, article in enumerate(articles):
        if i > 0:
            delay = random.randint(10, 30)  # 10-30s between posts for CI
            print(f"\n  Waiting {delay}s before publishing next article...")
            time.sleep(delay)

        print(f"\nPublishing: {article['title']}")
        result = publish_article(
            access_token=access_token,
            blog_id=blog_id,
            title=article["title"],
            content=article["content"],
            labels=article["labels"],
            search_description=article.get("search_description", ""),
            is_draft=is_draft,
        )
        results.append(result)

        if result["success"]:
            print(f"  Published: {result['url']}")
        else:
            print(f"  FAILED: {result['error']}")

    # Summary
    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'='*50}")
    print(f"Published: {success_count}/{count}")
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        print(f"  [{status}] {r['title']}")
    print(f"{'='*50}")

    # Auto-cleanup spam comments after publishing
    try:
        print("\nRunning spam comment cleanup...")
        from comment_manager import delete_spam_comments
        spam_stats = delete_spam_comments(access_token, blog_id, dry_run=False)
        if spam_stats["found"] > 0:
            print(f"  Spam cleanup: {spam_stats['deleted']}/{spam_stats['found']} deleted")
        else:
            print("  No spam comments found")
    except Exception as e:
        print(f"  Comment cleanup skipped: {e}")

    return results


def setup_oauth():
    """Interactive OAuth setup for first-time configuration."""
    print("=" * 50)
    print("Blogger OAuth Setup - First Time Configuration")
    print("=" * 50)

    client_id = input("Enter your Google Client ID: ").strip()
    client_secret = input("Enter your Google Client Secret: ").strip()

    auth_url = create_auth_url(client_id)
    print(f"\n1. Open this URL in your browser:\n   {auth_url}")
    print("\n2. Sign in with your Google account and grant permission")
    print("3. Copy the authorization code from the page")

    code = input("\n4. Paste the authorization code here: ").strip()

    print("\nExchanging code for tokens...")
    tokens = exchange_code_for_tokens(client_id, client_secret, code)

    blog_id = get_blog_id(tokens["access_token"])

    print(f"\nSetup complete!")
    print(f"  Blog ID: {blog_id}")
    print(f"\nAdd these to your GitHub Secrets:")
    print(f"  BLOGGER_CLIENT_ID={client_id}")
    print(f"  BLOGGER_CLIENT_SECRET={client_secret}")
    print(f"  BLOGGER_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"  BLOGGER_BLOG_ID={blog_id}")
    print(f"\nAlso add:")
    print(f"  DEEPSEEK_API_KEY=your_deepseek_api_key")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": tokens["refresh_token"],
        "blog_id": blog_id,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_oauth()
    else:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        is_draft = "--draft" in sys.argv
        run_pipeline(count=count, is_draft=is_draft)

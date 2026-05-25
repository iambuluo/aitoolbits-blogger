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

def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange refresh token for a new access token."""
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

    # Use system proxy but handle SSL properly
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["access_token"]


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

    # Get fresh access token
    print("Authenticating with Blogger API...")
    access_token = get_access_token(client_id, client_secret, refresh_token)
    print("  Access token obtained.")

    # Generate articles
    print(f"\nGenerating {count} article(s)...")
    from generate_article import generate_multiple
    articles = generate_multiple(count, deepseek_key)

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

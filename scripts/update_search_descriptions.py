"""
Batch update search descriptions for existing Blogger posts.

This script:
1. Fetches all published posts from Blogger API
2. Identifies posts missing searchDescription (meta description)
3. Generates SEO-optimized search descriptions using DeepSeek AI
4. Updates each post via Blogger PATCH API

Usage:
    # In GitHub Actions (env vars)
    python scripts/update_search_descriptions.py

    # Local (needs blogger_tokens.json)
    python scripts/update_search_descriptions.py
"""
import os
import sys
import json
import time
import random
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "published_urls.json"
CTX = ssl.create_default_context()

BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"


def load_credentials():
    """Load Blogger credentials from env vars or local file."""
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")

    if not all([client_id, client_secret, refresh_token, blog_id]):
        tokens_path = BASE_DIR / "blogger_tokens.json"
        if tokens_path.exists():
            with open(tokens_path, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = client_id or tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = client_secret or tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = refresh_token or tokens.get("BLOGGER_REFRESH_TOKEN", "")
            blog_id = blog_id or tokens.get("BLOGGER_BLOG_ID", "")

    return client_id, client_secret, refresh_token, blog_id


def get_access_token(client_id, client_secret, refresh_token):
    """Exchange refresh token for access token."""
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data, method="POST"
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]


def get_all_posts(access_token, blog_id):
    """Fetch all published posts with full details."""
    all_posts = []
    page_token = None
    api_base = f"{BLOGGER_API}/{blog_id}/posts"

    for _ in range(10):
        params = {"maxResults": "500", "status": "live", "fields": "items(id,title,url,searchDescription,content,labels),nextPageToken"}
        if page_token:
            params["pageToken"] = page_token

        url = f"{api_base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {access_token}")

        try:
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                posts = data.get("items", [])
                all_posts.extend(posts)
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"  Error fetching posts page {_}: {e}")
            break

    return all_posts


def generate_search_description(title, content, labels=None):
    """Use DeepSeek AI to generate an SEO-optimized search description (150-160 chars).

    Falls back to a simple heuristic if DeepSeek API is unavailable.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return _generate_heuristic_description(title, content, labels)

    # Strip HTML tags for a cleaner summary prompt
    import re
    plain_text = re.sub(r"<[^>]+>", " ", content)
    plain_text = re.sub(r"\s+", " ", plain_text).strip()
    # Take first 800 chars for context
    plain_text = plain_text[:800]

    prompt = (
        f"Generate a compelling SEO meta description (exactly 150-160 characters) "
        f"for the following blog article. The description should be engaging, "
        f"include relevant keywords, and encourage clicks. "
        f"Output ONLY the description text, no quotes, no explanation.\n\n"
        f"Title: {title}\n"
        f"Labels: {', '.join(labels) if labels else 'N/A'}\n"
        f"Content preview: {plain_text}"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are an SEO expert who writes compelling meta descriptions. "
                "Output ONLY the description text, no quotes, no markdown, no explanation. "
                "Keep it exactly 150-160 characters.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            desc = result["choices"][0]["message"]["content"].strip()
            # Remove any quotes or markdown
            desc = desc.strip("\"'`")
            if len(desc) > 165:
                desc = desc[:157] + "..."
            return desc
    except Exception as e:
        print(f"  DeepSeek API error: {e}")
        return _generate_heuristic_description(title, content, labels)


def _generate_heuristic_description(title, content, labels=None):
    """Fallback: generate a simple search description from title and labels."""
    if labels and len(labels) > 0:
        desc = f"Expert review and comparison of {title.lower()}. "
        desc += f"Discover top {labels[0].lower()} tools with features, pricing, and recommendations."
    else:
        desc = f"{title}. Expert analysis, practical tips, and recommendations for AI tools and technology."

    if len(desc) > 160:
        desc = desc[:157] + "..."
    return desc


def update_post_search_description(access_token, blog_id, post_id, search_description):
    """Update a post's searchDescription via Blogger PATCH API."""
    url = f"{BLOGGER_API}/{blog_id}/posts/{post_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"searchDescription": search_description}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="PATCH")

    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return True, result.get("searchDescription", "")
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            error_msg = e.read().decode("utf-8") if e.fp else error_msg
        return False, error_msg


def main():
    print("=" * 60)
    print("  Batch Update Search Descriptions")
    print("=" * 60)

    # Load credentials
    client_id, client_secret, refresh_token, blog_id = load_credentials()
    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing Blogger API credentials")
        sys.exit(1)

    # Get access token
    print("\n[1/4] Authenticating with Blogger API...")
    access_token = get_access_token(client_id, client_secret, refresh_token)
    print(f"  Token obtained: {access_token[:20]}...")

    # Fetch all posts
    print("\n[2/4] Fetching all published posts...")
    posts = get_all_posts(access_token, blog_id)
    print(f"  Total posts: {len(posts)}")

    # Identify posts missing searchDescription
    missing = [p for p in posts if not p.get("searchDescription")]
    has_desc = [p for p in posts if p.get("searchDescription")]
    print(f"  With search description: {len(has_desc)}")
    print(f"  Missing search description: {len(missing)}")

    if not missing:
        print("\n  All posts already have search descriptions. Nothing to do!")
        return

    # Generate and update search descriptions
    print(f"\n[3/4] Updating {len(missing)} posts with new search descriptions...")
    success_count = 0
    fail_count = 0

    for i, post in enumerate(missing):
        post_id = post["id"]
        title = post.get("title", "Unknown")
        content = post.get("content", "")
        labels = post.get("labels", [])
        url = post.get("url", "")

        print(f"\n  [{i+1}/{len(missing)}] {title[:60]}")
        print(f"       URL: {url}")

        # Generate search description
        desc = generate_search_description(title, content, labels)
        print(f"       Generated ({len(desc)} chars): {desc}")

        # Update post
        ok, result = update_post_search_description(
            access_token, blog_id, post_id, desc
        )
        if ok:
            print(f"       Status: UPDATED")
            success_count += 1
        else:
            print(f"       Status: FAILED - {result[:100]}")
            fail_count += 1

        # Rate limiting: wait 2-5 seconds between API calls
        if i < len(missing) - 1:
            delay = random.randint(2, 5)
            print(f"       Waiting {delay}s...")
            time.sleep(delay)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Summary")
    print(f"{'=' * 60}")
    print(f"  Total posts:       {len(posts)}")
    print(f"  Already had desc:  {len(has_desc)}")
    print(f"  Updated:           {success_count}")
    print(f"  Failed:            {fail_count}")
    print(f"{'=' * 60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

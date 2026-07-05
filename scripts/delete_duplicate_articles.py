"""
Delete duplicate articles from Blogger blog.

This script:
1. Fetches all published posts from Blogger API
2. Groups posts by title (case-insensitive)
3. For each group with duplicates, keeps the earliest published post
4. Deletes the rest via Blogger DELETE API
5. Updates published_urls.json to remove deleted URLs

Usage:
    # In GitHub Actions (env vars)
    python scripts/delete_duplicate_articles.py

    # Local (needs blogger_tokens.json)
    python scripts/delete_duplicate_articles.py
"""
import os
import sys
import json
import time
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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
        params = {"maxResults": "500", "status": "live"}
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


def delete_post(access_token, blog_id, post_id):
    """Delete a post via Blogger DELETE API."""
    url = f"{BLOGGER_API}/{blog_id}/posts/{post_id}"
    req = urllib.request.Request(url, method="DELETE")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            # 204 No Content on success
            return True, f"Deleted (HTTP {resp.status})"
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            try:
                error_msg = e.read().decode("utf-8") if e.fp else error_msg
            except Exception:
                pass
        return False, error_msg


def parse_date(date_str):
    """Parse Blogger date string to datetime for comparison."""
    try:
        # Blogger format: 2026-06-15T10:30:00.123-07:00
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def update_published_urls(deleted_urls, deleted_titles):
    """Update published_urls.json to remove deleted entries."""
    if not DATA_FILE.exists():
        print("  Warning: published_urls.json not found, skipping update")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_count = len(data.get("urls", []))
    deleted_url_set = set(deleted_urls)

    # Keep URLs not in deleted set
    data["urls"] = [
        entry for entry in data.get("urls", [])
        if entry.get("url") not in deleted_url_set
    ]

    # Update timestamp
    data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  published_urls.json updated: {original_count} -> {len(data['urls'])} URLs")


def main():
    print("=" * 60)
    print("  Delete Duplicate Articles")
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
    print(f"  Total posts found: {len(posts)}")

    if not posts:
        print("  No posts found. Exiting.")
        return

    # Group by title (case-insensitive)
    print("\n[3/4] Analyzing duplicates...")
    title_groups = defaultdict(list)
    for post in posts:
        title = post.get("title", "").strip()
        # Use lowercase title as key for deduplication
        key = title.lower()
        title_groups[key].append(post)

    # Find duplicates
    duplicate_groups = {
        key: group for key, group in title_groups.items()
        if len(group) > 1
    }

    if not duplicate_groups:
        print("  No duplicate articles found. Nothing to do!")
        return

    total_duplicates = sum(len(g) - 1 for g in duplicate_groups.values())
    print(f"  Found {len(duplicate_groups)} titles with duplicates")
    print(f"  Total duplicate posts to delete: {total_duplicates}")
    print()

    # Print duplicate details
    for key, group in sorted(duplicate_groups.items()):
        title = group[0].get("title", "Unknown")
        count = len(group)
        print(f"  [{count}x] {title[:70]}")
        for p in sorted(group, key=lambda x: parse_date(x.get("published", ""))):
            pub_date = p.get("published", "")[:19]
            print(f"       {pub_date} | ID: {p['id']} | {p.get('url', '')[-60:]}")
        print()

    # Delete duplicates
    print("[4/4] Deleting duplicate posts...")
    deleted_urls = []
    deleted_titles = []
    success_count = 0
    fail_count = 0

    for key, group in duplicate_groups.items():
        # Sort by published date ascending - keep the earliest one
        sorted_posts = sorted(group, key=lambda x: parse_date(x.get("published", "")))
        keep_post = sorted_posts[0]
        delete_posts = sorted_posts[1:]

        title = keep_post.get("title", "Unknown")
        keep_date = keep_post.get("published", "")[:19]
        print(f"\n  Keeping: {title[:60]}")
        print(f"    Published: {keep_date} | ID: {keep_post['id']}")

        for i, post in enumerate(delete_posts):
            post_id = post["id"]
            post_url = post.get("url", "")
            post_title = post.get("title", "Unknown")
            pub_date = post.get("published", "")[:19]

            print(f"  Deleting duplicate #{i+1}: {post_title[:50]}")
            print(f"    Published: {pub_date} | URL: {post_url}")

            ok, result = delete_post(access_token, blog_id, post_id)
            if ok:
                print(f"    Status: DELETED")
                deleted_urls.append(post_url)
                deleted_titles.append(post_title)
                success_count += 1
            else:
                print(f"    Status: FAILED - {result[:100]}")
                fail_count += 1

            # Rate limiting
            time.sleep(1)

    # Update published_urls.json
    if deleted_urls:
        print("\nUpdating published_urls.json...")
        update_published_urls(deleted_urls, deleted_titles)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Summary")
    print(f"{'=' * 60}")
    print(f"  Total posts before:    {len(posts)}")
    print(f"  Duplicates found:      {total_duplicates}")
    print(f"  Successfully deleted:  {success_count}")
    print(f"  Failed to delete:      {fail_count}")
    print(f"  Remaining posts:       {len(posts) - success_count}")
    print(f"{'=' * 60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

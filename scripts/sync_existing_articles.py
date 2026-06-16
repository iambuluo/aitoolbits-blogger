"""
Sync existing Blogger articles to published_urls.json for anti-duplicate protection.
This script fetches all published articles from Blogger API and populates the local database.
"""

import os
import sys
import json
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

from publish_to_blogger import get_access_token


def sync_existing_articles():
    """Fetch all Blogger articles and save to published_urls.json."""
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    if not all([client_id, client_secret, refresh_token]):
        print("ERROR: Missing Blogger credentials in environment variables")
        print("Please set BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, and BLOGGER_REFRESH_TOKEN")
        return

    print("Authenticating with Blogger API...")
    access_token = get_access_token(client_id, client_secret, refresh_token)
    print("Access token obtained.")

    blog_id = blog_id or os.environ.get("BLOGGER_BLOG_ID")
    if not blog_id:
        # Try to get blog ID from URL
        blog_id_url = "https://www.googleapis.com/blogger/v3/blogs/byurl?url=https://aitoolbits.blogspot.com/"
        import urllib.request
        req = urllib.request.Request(blog_id_url, headers={"Authorization": f"Bearer {access_token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            blog_data = json.loads(resp.read().decode())
            blog_id = blog_data["id"]
        print(f"Blog ID retrieved: {blog_id}")

    # Fetch all posts (Blogger API returns max 100 per page)
    print(f"\nFetching articles from blog ID: {blog_id}")
    import urllib.request

    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=100"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    })

    all_posts = []
    page_token = None
    while True:
        if page_token:
            url_with_token = f"{url}&pageToken={page_token}"
        else:
            url_with_token = url

        req = urllib.request.Request(url_with_token, headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            posts = data.get("items", [])
            all_posts.extend(posts)
            page_token = data.get("nextPageToken")

        if not page_token or not posts:
            break

    print(f"Fetched {len(all_posts)} articles from Blogger.")

    # Build published_urls.json
    from published_urls import load_published_urls, save_published_urls

    db = load_published_urls()
    existing_urls = {item["url"] for item in db["urls"]} if db["urls"] else set()
    existing_titles = {item["title"] for item in db["urls"]} if db["urls"] else set()

    new_count = 0
    for post in all_posts:
        post_url = post.get("url", "")
        post_title = post.get("title", "")

        if post_url and post_url not in existing_urls:
            db["urls"].append({"url": post_url, "title": post_title})
            existing_urls.add(post_url)
            new_count += 1

    save_published_urls(db)
    print(f"\nAdded {new_count} new articles to published_urls.json")
    print(f"Total tracked articles: {len(db['urls'])}")

    # Print first 10 titles for verification
    print("\nFirst 10 tracked articles:")
    for i, item in enumerate(sorted(db["urls"], key=lambda x: x["url"], reverse=True)[:10], 1):
        print(f"  {i}. {item['title'][:80]}")
        print(f"     URL: {item['url']}")

    print("\nSync complete!")


if __name__ == "__main__":
    sync_existing_articles()

"""
Publish original (hand-written) articles to Blogger as regular posts.

These articles are NOT auto-generated tool lists — they are first-hand
experience / opinion pieces written to address AdSense "low value content".
They include author byline, real testing data, and FAQ sections.

Usage:
    python scripts/publish_original_articles.py
"""
import os
import sys
import json
import re
import glob
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publish_to_blogger import get_access_token, _try_auto_save_refresh_token, publish_article

BASE_DIR = Path(__file__).parent.parent
ARTICLES_DIR = BASE_DIR / "articles"
BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"


# Metadata for each original article: file -> (labels, search_description)
ORIGINAL_ARTICLES = {
    "original_i_tested_10_bg_removers.html": {
        "labels": ["Hands-on Testing", "AI Tools", "Original"],
        "search_description": "I ran one photo through 10 AI background removers. Only 3 were usable. Full method, scoring table, and tool-by-tool notes.",
    },
    "original_my_ai_writing_pipeline.html": {
        "labels": ["Behind the Scenes", "AI Writing", "Original"],
        "search_description": "How I publish 3 original posts a day using 5 AI tools. My full pipeline, daily timeline, and the mistakes I paid for.",
    },
}

# Old Chinese post titles (and their new English titles) to delete before
# republishing, so we don't leave stale/duplicate posts on the blog.
OLD_TITLES_TO_DELETE = [
    "我把同一张图塞进 10 个 AI 抠图工具，只有 3 个能用",
    "我的 AI 写作流水线：5 个工具如何让我一天发 3 篇",
    "I Ran the Same Photo Through 10 AI Background Removers. Only 3 Were Worth Using.",
    "My AI Writing Pipeline: How 5 Tools Let Me Publish 3 Posts a Day",
]


def fetch_all_posts(access_token: str, blog_id: str):
    """Fetch all live posts (id, title, url)."""
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    posts = []
    page_token = None
    while True:
        url = f"{BLOGGER_API}/{blog_id}/posts?maxResults=500&status=live&fetchBodies=false"
        if page_token:
            url += f"&pageToken={page_token}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        posts.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return posts


def delete_post(access_token: str, blog_id: str, post_id: str):
    """Delete a single post by id."""
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    url = f"{BLOGGER_API}/{blog_id}/posts/{post_id}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"}, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            return True, ""
    except Exception as e:
        msg = str(e)
        if hasattr(e, "read"):
            try:
                msg = e.read().decode("utf-8")
            except Exception:
                pass
        return False, msg


def delete_old_versions(access_token: str, blog_id: str):
    """Delete any existing posts whose title matches OLD_TITLES_TO_DELETE."""
    print("\n[cleanup] Checking for old/duplicate versions to delete...")
    try:
        posts = fetch_all_posts(access_token, blog_id)
    except Exception as e:
        print(f"  WARN: could not fetch posts ({e}); skipping cleanup.")
        return
    targets = {t.strip() for t in OLD_TITLES_TO_DELETE}
    deleted = 0
    for p in posts:
        if p.get("title", "").strip() in targets:
            pid = p.get("id")
            title = p.get("title", "")[:50]
            ok, err = delete_post(access_token, blog_id, pid)
            if ok:
                print(f"  DELETED: {title} (id={pid})")
                deleted += 1
            else:
                print(f"  FAILED to delete {title}: {err[:150]}")
    print(f"  Cleanup done. {deleted} old post(s) deleted.")


def extract_title(html: str) -> str:
    """Extract the H1 title from the article HTML."""
    match = re.search(r"<h1>(.*?)</h1>", html, re.DOTALL)
    if match:
        # Strip inner tags (like <em>)
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return title
    return "Untitled"


def load_credentials():
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


def main():
    print("=" * 60)
    print("  Publish Original Articles")
    print("=" * 60)

    client_id, client_secret, refresh_token, blog_id = load_credentials()
    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing Blogger API credentials")
        sys.exit(1)

    print("\n[1/3] Authenticating with Blogger API...")
    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_try_auto_save_refresh_token,
    )
    print("  Token obtained.")

    # Remove old Chinese versions (and any prior English versions) first
    delete_old_versions(access_token, blog_id)

    print("\n[2/3] Finding original articles...")
    results = []
    for filename, meta in ORIGINAL_ARTICLES.items():
        filepath = ARTICLES_DIR / filename
        if not filepath.exists():
            print(f"  SKIP: {filename} not found")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        title = extract_title(html)
        labels = meta.get("labels", [])
        search_desc = meta.get("search_description", "")

        print(f"\n  Found: {title}")
        print(f"    File: {filename}")
        print(f"    Labels: {labels}")
        print(f"    Search desc: {search_desc[:50]}...")

        results.append({
            "title": title,
            "html": html,
            "labels": labels,
            "search_description": search_desc,
        })

    if not results:
        print("  No original articles found to publish.")
        return

    print(f"\n[3/3] Publishing {len(results)} article(s)...")
    success_count = 0
    for article in results:
        print(f"\n  Publishing: {article['title'][:60]}")
        result = publish_article(
            access_token=access_token,
            blog_id=blog_id,
            title=article["title"],
            content=article["html"],
            labels=article["labels"],
            search_description=article["search_description"],
        )
        if result.get("success"):
            print(f"    SUCCESS! URL: {result.get('url')}")
            success_count += 1
        else:
            print(f"    FAILED: {result.get('error', '')[:200]}")

    print(f"\n=== Summary: {success_count}/{len(results)} published ===")
    if success_count < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()

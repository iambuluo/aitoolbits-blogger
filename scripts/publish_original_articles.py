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

from publish_to_blogger import get_access_token, _try_auto_save_refresh_token, publish_post

BASE_DIR = Path(__file__).parent.parent
ARTICLES_DIR = BASE_DIR / "articles"
BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"


# Metadata for each original article: file -> (labels, search_description)
ORIGINAL_ARTICLES = {
    "original_i_tested_10_bg_removers.html": {
        "labels": ["实测", "AI工具", "原创"],
        "search_description": "同一张图跑遍10个AI抠图工具，只有3个能打。附测试方法、对比表和逐工具点评。",
    },
    "original_my_ai_writing_pipeline.html": {
        "labels": ["幕后", "AI写作", "原创"],
        "search_description": "我是如何用5个AI工具一天发3篇原创文章的？完整流水线、时间线和踩坑记录全公开。",
    },
}


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
        result = publish_post(
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

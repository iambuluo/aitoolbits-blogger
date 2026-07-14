"""
Self-check after AdSense readiness improvements.
Verifies:
1. Trust pages (About/Contact/Disclaimer) exist
2. No duplicate post titles remain
3. Original articles are published

Run via GitHub Actions (can't access Google from mainland China).
"""
import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish_to_blogger import get_access_token, _try_auto_save_refresh_token

BASE_DIR = Path(__file__).parent.parent
CTX = ssl.create_default_context()
BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"


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


def get_all_posts(access_token, blog_id):
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
                all_posts.extend(data.get("items", []))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"  Error fetching posts: {e}")
            break
    return all_posts


def get_all_pages(access_token, blog_id):
    pages = []
    page_token = None
    api_base = f"{BLOGGER_API}/{blog_id}/pages"
    for _ in range(5):
        params = {"maxResults": "100"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{api_base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {access_token}")
        try:
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages.extend(data.get("items", []))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"  Error fetching pages: {e}")
            break
    return pages


def main():
    print("=" * 60)
    print("  AdSense Readiness Self-Check")
    print("=" * 60)

    client_id, client_secret, refresh_token, blog_id = load_credentials()
    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing credentials")
        sys.exit(1)

    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_try_auto_save_refresh_token,
    )

    # 1. Check trust pages
    print("\n[1] Checking trust pages...")
    pages = get_all_pages(access_token, blog_id)
    page_titles = [p.get("title", "").strip().lower() for p in pages]
    required_pages = {"about": False, "contact": False, "disclaimer": False}
    for t in page_titles:
        if "about" in t:
            required_pages["about"] = True
        if "contact" in t:
            required_pages["contact"] = True
        if "disclaimer" in t:
            required_pages["disclaimer"] = True

    for name, found in required_pages.items():
        print(f"  {'✅' if found else '❌'} {name.capitalize()} page: {'FOUND' if found else 'MISSING'}")
    pages_ok = all(required_pages.values())

    # 2. Check duplicates
    print("\n[2] Checking for duplicate post titles...")
    posts = get_all_posts(access_token, blog_id)
    title_groups = defaultdict(list)
    for post in posts:
        title_groups[post.get("title", "").strip().lower()].append(post)
    dup_groups = {k: v for k, v in title_groups.items() if len(v) > 1}
    print(f"  Total posts: {len(posts)}")
    print(f"  Duplicate title groups: {len(dup_groups)}")
    for key, group in dup_groups.items():
        print(f"    [{'x'.join([''] * len(group))[1:]}] {group[0].get('title', '')[:60]}")
    no_dupes = len(dup_groups) == 0

    # 3. Check original articles
    print("\n[3] Checking original articles...")
    orig_titles = [
        "我把同一张图塞进 10 个 ai 抠图工具，只有 3 个能用",
        "我的 ai 写作流水线：5 个工具如何让我一天发 3 篇",
    ]
    post_titles_lower = [p.get("title", "").strip().lower() for p in posts]
    orig_found = 0
    for ot in orig_titles:
        found = any(ot in pt for pt in post_titles_lower)
        print(f"  {'✅' if found else '❌'} {ot[:40]}...: {'PUBLISHED' if found else 'NOT FOUND'}")
        if found:
            orig_found += 1
    orig_ok = orig_found == len(orig_titles)

    # Summary
    print("\n" + "=" * 60)
    print("  SELF-CHECK SUMMARY")
    print("=" * 60)
    print(f"  Trust pages (About/Contact/Disclaimer): {'✅ PASS' if pages_ok else '❌ FAIL'}")
    print(f"  No duplicate titles:                     {'✅ PASS' if no_dupes else '❌ FAIL'}")
    print(f"  Original articles published:            {'✅ PASS' if orig_ok else '❌ FAIL'} ({orig_found}/{len(orig_titles)})")
    print("=" * 60)

    all_ok = pages_ok and no_dupes and orig_ok
    print(f"  OVERALL: {'✅ ALL CHECKS PASSED' if all_ok else '❌ SOME CHECKS FAILED'}")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

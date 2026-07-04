"""
Sync published_urls database from Blogger API.
Fills in missing entries so the duplicate prevention mechanism is complete.
"""
import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "published_urls.json"
CTX = ssl.create_default_context()


def get_access_token():
    """Get Blogger access token. Supports env vars (CI) and local config file."""
    # Try env vars first (GitHub Actions)
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")

    # Fallback to local config file
    if not all([client_id, client_secret, refresh_token]):
        tokens_path = BASE_DIR / "blogger_tokens.json"
        if tokens_path.exists():
            with open(tokens_path, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = tokens.get("BLOGGER_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError("Missing Blogger API credentials")

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))["access_token"]
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return None


def get_all_posts(access_token, blog_id):
    """Get all published posts from Blogger API."""
    all_posts = []
    page_token = None
    api_base = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"

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
                for post in posts:
                    all_posts.append({
                        "url": post.get("url", ""),
                        "title": post.get("title", ""),
                    })
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"API error at page {_} : {e}")
            break

    return all_posts


def load_db():
    """Load existing published_urls database."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"urls": [], "updated_at": None}


def save_db(db):
    """Save published_urls database."""
    os.makedirs(DATA_FILE.parent, exist_ok=True)
    from datetime import datetime
    db["updated_at"] = datetime.now().isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 60)
    print("  同步 Published URLs 数据库")
    print("=" * 60)

    # Get Blogger credentials (env vars first, then local file)
    tokens_path = BASE_DIR / "blogger_tokens.json"
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
    
    if not blog_id:
        if tokens_path.exists():
            with open(tokens_path, "r") as f:
                tokens = json.load(f)
            blog_id = tokens.get("BLOGGER_BLOG_ID", "")
    
    if not blog_id:
        print("[X] BLOGGER_BLOG_ID 未配置")
        return

    # Step 1: Get access token
    print("\n[1/3] 获取 Blogger access token...")
    access_token = get_access_token()
    if not access_token:
        print("[X] 无法获取 access token")
        return
    print("[OK] Token 获取成功")

    # Step 2: Fetch all posts
    print("\n[2/3] 获取所有已发布文章...")
    posts = get_all_posts(access_token, blog_id)
    print(f"[OK] 获取 {len(posts)} 篇文章")

    # Step 3: Sync to database
    print("\n[3/3] 同步到 published_urls.json...")
    db = load_db()
    existing_urls = {item["url"] for item in db["urls"]}
    new_count = 0

    for post in posts:
        if post["url"] and post["url"] not in existing_urls:
            db["urls"].append({
                "url": post["url"],
                "title": post["title"],
            })
            existing_urls.add(post["url"])
            new_count += 1
            print(f"  [+] {post['title'][:60]}")

    save_db(db)

    print(f"\n{'=' * 60}")
    print(f"  同步完成!")
    print(f"  新增: {new_count} 篇")
    print(f"  总计: {len(db['urls'])} 篇")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

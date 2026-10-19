"""
Sync existing Blogger articles with fallback methods.
Handles both GitHub Actions (secrets) and local (tokens file) environments.
"""
import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "published_urls.json"
CTX = ssl.create_default_context()

def get_credentials():
    """Get Blogger credentials from env vars or local file."""
    # Try env vars first (GitHub Actions)
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
    
    source = "env"
    
    # Fallback to local config file
    if not all([client_id, client_secret, refresh_token, blog_id]):
        tokens_path = BASE_DIR / "blogger_tokens.json"
        if tokens_path.exists():
            with open(tokens_path, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = tokens.get("BLOGGER_REFRESH_TOKEN", "")
            blog_id = tokens.get("BLOGGER_BLOG_ID", "")
            source = "local_file"
    
    return client_id, client_secret, refresh_token, blog_id, source

def get_access_token(client_id, client_secret, refresh_token):
    """Get Blogger access token."""
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]

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
    
    return all_posts

def main():
    print("=== Blogger Article Sync ===")
    
    client_id, client_secret, refresh_token, blog_id, source = get_credentials()
    
    print(f"Credentials source: {source}")
    print(f"Blog ID: {blog_id[:10]}..." if blog_id else "Blog ID: MISSING")
    print(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: MISSING")
    
    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing required credentials")
        sys.exit(1)
    
    try:
        print("\nGetting access token...")
        access_token = get_access_token(client_id, client_secret, refresh_token)
        print(f"Access token obtained: {access_token[:20]}...")
        
        print("\nFetching all posts...")
        posts = get_all_posts(access_token, blog_id)
        print(f"Total posts fetched: {len(posts)}")
        
        # Save
        db = {"urls": posts, "updated_at": datetime.now().isoformat()}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {DATA_FILE}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Check Google indexed article count via site: search.
Runs in GitHub Actions (can access Google).
"""
import urllib.request
import urllib.parse
import ssl
import re
import sys
import json
import os
from datetime import datetime

BLOG_URL = "https://aitoolbits.blogspot.com"
GTM_ID = "G-ZLSZKQ9RQD"  # Google Tag Manager ID on your blog


def count_indexed_via_google_search():
    """Search Google for site:aitoolbits.blogspot.com and count results."""
    query = f"site:aitoolbits.blogspot.com"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=100&hl=en&filter=0"
    
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Google search failed: {e}")
        return None
    
    # Method 1: Look for result-stats
    m = re.search(r'id="result-stats"[^>]*>([^<]+)<', html, re.IGNORECASE)
    if m:
        stats_text = m.group(1)
        print(f"Google result stats: {stats_text}")
        # Extract number
        num_m = re.search(r'([\d,]+)', stats_text.replace(",", ""))
        if num_m:
            return int(num_m.group(1).replace(",", ""))
    
    # Method 2: Count actual result links
    urls = re.findall(r'(https?://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[^\"\'<>\s]+?\.html)', html)
    unique = len(set(urls))
    print(f"Unique article URLs on first page: {unique}")
    
    # Method 3: Look for "About X results" text
    m = re.search(r'About ([\d,]+) results', html, re.IGNORECASE)
    if m:
        count = int(m.group(1).replace(",", ""))
        print(f"About {count} results")
        return count
    
    # If we got some results but couldn't extract count
    if unique > 0:
        return f"> {unique} (first page only)"
    
    return 0


def count_indexed_via_bing():
    """Check Bing for indexed pages as alternate data point."""
    query = f"site:aitoolbits.blogspot.com"
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&count=50"
    
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Bing search failed: {e}")
        return None
    
    # Look for result count
    m = re.search(r'About ([\d,]+) results', html, re.IGNORECASE)
    if m:
        count = int(m.group(1).replace(",", ""))
        print(f"Bing: About {count} results")
        return count
    
    # Count article URLs
    urls = re.findall(r'(https?://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[^\"\'<>\s]+?\.html)', html)
    unique = len(set(urls))
    if unique > 0:
        print(f"Bing: {unique} unique article URLs on first page")
        return f"> {unique} (first page only)"
    
    return 0


def count_total_posts_via_blogger_api():
    """Get total post count from Blogger API."""
    # Read tokens from environment (set in GitHub Actions secrets)
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
    
    if not all([client_id, client_secret, refresh_token, blog_id]):
        # Try file fallback
        tokens_path = os.path.join(os.path.dirname(__file__), "..", "blogger_tokens.json")
        if os.path.exists(tokens_path):
            with open(tokens_path) as f:
                tokens = json.load(f)
            client_id = client_id or tokens.get("BLOGGER_CLIENT_ID", tokens.get("client_id", ""))
            client_secret = client_secret or tokens.get("BLOGGER_CLIENT_SECRET", tokens.get("client_secret", ""))
            refresh_token = refresh_token or tokens.get("BLOGGER_REFRESH_TOKEN", tokens.get("refresh_token", ""))
            blog_id = blog_id or tokens.get("BLOGGER_BLOG_ID", "")
        else:
            print("No Blogger tokens available")
            return None
    
    # Get access token
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            access_token = result.get("access_token", "")
    except Exception as e:
        print(f"Failed to get access token: {e}")
        return None
    
    if not access_token:
        print("No access token")
        return None
    
    # Count posts
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=1&fields=totalItems"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("totalItems", 0)
    except Exception as e:
        print(f"Blogger API failed: {e}")
        return None


def send_wechat_notification(google_count, bing_count, total_posts):
    """Send indexing report via ServerChan."""
    sckey = os.environ.get("SERVER_CHAN_KEY", "")
    if not sckey:
        print("No ServerChan key configured")
        return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Build report
    g_str = str(google_count) if google_count is not None else "检测失败"
    b_str = str(bing_count) if bing_count is not None else "检测失败"
    t_str = str(total_posts) if total_posts is not None else "未知"
    
    if isinstance(google_count, int) and isinstance(total_posts, int) and total_posts > 0:
        ratio = f"{google_count / total_posts * 100:.1f}%"
    else:
        ratio = "未知"
    
    title = f"Google 收录检测: {g_str}/{t_str} ({ratio})"
    
    content = f"""## aitoolbits 收录情况报告
> 检测时间: {now}

| 搜索引擎 | 收录篇数 |
| -------- | -------- |
| Google   | {g_str} |
| Bing     | {b_str} |

**总文章数**: {t_str} 篇
**Google 收录率**: {ratio}

**说明**: 如果 Google 收录数偏低，可能需要：
1. 等待 3-7 天（Google 爬虫持续抓取中）
2. 在 GSC 后台手动请求索引重点文章
3. 检查是否有被标记为低质量的页面
"""
    
    data = urllib.parse.urlencode({
        "title": title,
        "desp": content,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"https://sctapi.ftqq.com/{sckey}.send",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"Notification sent: {resp.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Notification failed: {e}")


def main():
    print("=" * 60)
    print("aitoolbits.blogspot.com 索引收录检测")
    print("=" * 60)
    print()
    
    # 1. Total posts count
    print("[1/3] 获取文章总数...")
    total_posts = count_total_posts_via_blogger_api()
    if total_posts:
        print(f"  文章总数: {total_posts} 篇")
    else:
        print("  无法获取文章总数")
    
    print()
    
    # 2. Google indexed count
    print("[2/3] 检测 Google 收录...")
    google_count = count_indexed_via_google_search()
    if google_count is not None:
        print(f"  Google 收录: {google_count} 篇")
    else:
        print("  Google 收录检测失败")
    
    print()
    
    # 3. Bing indexed count
    print("[3/3] 检测 Bing 收录...")
    bing_count = count_indexed_via_bing()
    if bing_count is not None:
        print(f"  Bing 收录: {bing_count} 篇")
    else:
        print("  Bing 收录检测失败")
    
    print()
    print("=" * 60)
    
    # Summary
    if total_posts and isinstance(google_count, int):
        pct = google_count / total_posts * 100 if total_posts > 0 else 0
        print(f"收录率: {google_count}/{total_posts} = {pct:.1f}%")
    
    # Send notification
    send_wechat_notification(google_count, bing_count, total_posts)


if __name__ == "__main__":
    main()

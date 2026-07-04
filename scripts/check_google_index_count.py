"""
Check Google indexed article count via site: search.
Runs in GitHub Actions (can access Google).
Improved version with diagnostics and multiple methods.
"""
import urllib.request
import urllib.parse
import ssl
import re
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime

BLOG_URL = "https://aitoolbits.blogspot.com"


def count_total_posts_via_atom_feed():
    """Count total posts via Blogger Atom Feed (no auth needed)."""
    feed_url = f"{BLOG_URL}/feeds/posts/default?max-results=1&alt=json"
    req = urllib.request.Request(feed_url)
    req.add_header("User-Agent", "Mozilla/5.0")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            total = int(data.get("feed", {}).get("openSearch$totalResults", {}).get("$t", 0))
            print(f"  Atom Feed 文章总数: {total} 篇")
            return total
    except Exception as e:
        print(f"  Atom Feed 获取失败: {e}")
        return None


def check_blog_accessible():
    """Check if the blog is accessible and returns proper HTML."""
    print("\n[诊断] 检查博客可访问性...")
    req = urllib.request.Request(BLOG_URL)
    req.add_header("User-Agent", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            status = resp.status
            print(f"  HTTP Status: {status}")
            print(f"  Page size: {len(html)} bytes")
            
            # Check for noindex
            if "noindex" in html[:5000]:
                print("  [WARN] Page contains 'noindex'!")
            else:
                print("  [OK] No 'noindex' detected")
            
            # Check title
            title_m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_m:
                print(f"  Title: {title_m.group(1)[:80]}")
            
            # Check canonical
            canon_m = re.search(r'rel="canonical"[^>]*href="([^"]+)"', html, re.IGNORECASE)
            if canon_m:
                print(f"  Canonical: {canon_m.group(1)}")
            
            return True
    except Exception as e:
        print(f"  [FAIL] Cannot access blog: {e}")
        return False


def check_robots_txt():
    """Check robots.txt for blocks."""
    print("\n[诊断] 检查 robots.txt...")
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(f"{BLOG_URL}/robots.txt")
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            if "Disallow: /" in content:
                print("  [WARN] robots.txt blocks everything!")
                print(f"  Content: {content[:200]}")
            else:
                print(f"  [OK] robots.txt is fine")
                for line in content.strip().split("\n"):
                    if "Disallow" in line or "Sitemap" in line:
                        print(f"  {line.strip()}")
            return content
    except Exception as e:
        print(f"  [FAIL] Cannot fetch robots.txt: {e}")
        return None


def count_indexed_via_google_search():
    """Search Google for site:aitoolbits.blogspot.com and count results."""
    query = f"site:aitoolbits.blogspot.com"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=100&hl=en&filter=0&safe=off"
    
    # Try multiple User-Agent strategies
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    ]
    
    for ua in user_agents:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", ua)
        req.add_header("Accept-Language", "en-US,en;q=0.9")
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        req.add_header("Cache-Control", "no-cache")
        
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                print(f"  [UA: {ua[:30]}...] Response: {resp.status}, Size: {len(html)}")
                
                # Detect captcha/bot block
                if "captcha" in html.lower() or "unusual traffic" in html.lower():
                    print(f"  [BLOCKED] Google is showing captcha/bot detection page")
                    continue
                
                if len(html) < 5000:
                    print(f"  Response too small ({len(html)} bytes) - likely blocked")
                    continue
                
                # Method 1: Result stats
                m = re.search(r'id="result-stats"[^>]*>([^<]+)<', html, re.IGNORECASE)
                if m:
                    stats_text = m.group(1)
                    print(f"  Result stats: {stats_text}")
                    num_m = re.search(r'([\d,]+)', stats_text.replace(",", ""))
                    if num_m:
                        return int(num_m.group(1).replace(",", ""))
                
                # Method 2: Count article URLs
                urls = re.findall(
                    r'(https?://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[^\"\'<>\s]+?\.html)',
                    html
                )
                unique = len(set(urls))
                print(f"  Unique article URLs on page: {unique}")
                
                # Method 3: Broader URL match
                all_urls = re.findall(
                    r'(https?://aitoolbits\.blogspot\.com/[^\"\'<>\s]+)',
                    html
                )
                all_unique = len(set(all_urls))
                print(f"  All aitoolbits URLs on page: {all_unique}")
                
                # Method 4: "About X results" 
                m = re.search(r'About ([\d,]+) results', html, re.IGNORECASE)
                if m:
                    return int(m.group(1).replace(",", ""))
                
                if unique > 0:
                    return f"> {unique} (first page only)"
                
                # Show a snippet of HTML for diagnosis
                print(f"  HTML snippet: {html[500:800]}")
                break  # Got a reasonable response, no need to try other UAs
                
        except Exception as e:
            print(f"  Google search error: {e}")
            continue
    
    return None


def count_indexed_via_bing():
    """Check Bing for indexed pages."""
    query = f"site:aitoolbits.blogspot.com"
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&count=50"
    
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            print(f"  Bing response: Status={resp.status}, Size={len(html)}")
    except Exception as e:
        print(f"  Bing search failed: {e}")
        return None
    
    # Method 1: Result count
    m = re.search(r'About ([\d,]+) results', html, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))
    
    m = re.search(r'([\d,]+) results', html, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))
    
    # Method 2: Count article URLs
    urls = re.findall(
        r'(https?://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[^\"\'<>\s]+?\.html)',
        html
    )
    unique = len(set(urls))
    print(f"  Bing article URLs on page: {unique}")
    
    if unique > 0:
        return f"> {unique} (first page only)"
    
    # Try to detect if we got blocked
    if len(html) < 1000:
        print(f"  Bing response too small - likely blocked")
        return None
    
    return None


def send_wechat_notification(google_count, bing_count, total_posts):
    """Send indexing report via ServerChan."""
    sckey = os.environ.get("SERVER_CHAN_KEY", "")
    if not sckey:
        print("No ServerChan key configured")
        return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    g_str = str(google_count) if google_count is not None else "检测失败（被屏蔽）"
    b_str = str(bing_count) if bing_count is not None else "检测失败（被屏蔽）"
    t_str = str(total_posts) if total_posts is not None else "未知"
    
    if isinstance(google_count, int) and isinstance(total_posts, int) and total_posts > 0:
        ratio = f"{google_count / total_posts * 100:.1f}%"
    else:
        ratio = "待确认"
    
    title = f"收录检测: G={g_str} B={b_str} / 共{t_str}篇"
    
    content = f"""## aitoolbits 收录情况报告
> 检测时间: {now}

| 项目 | 数值 |
|------|------|
| Google 收录 | {g_str} |
| Bing 收录 | {b_str} |
| 文章总数 | {t_str} 篇 |
| 收录率 | {ratio} |

⚠️ 注意: 搜索引擎常会拦截自动请求，结果可能不准确。
最准确的方式: 登录 GSC → 效果 → 搜索结果 → 查看已编入索引的页面数。
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
    print("aitoolbits.blogspot.com 索引收录检测 v2")
    print("=" * 60)
    
    # 0. Diagnostics
    check_blog_accessible()
    check_robots_txt()
    
    # 1. Total posts count from Atom Feed
    print("\n[1/4] 获取文章总数...")
    total_posts = count_total_posts_via_atom_feed()
    
    # 2. Google indexed count
    print("\n[2/4] 检测 Google 收录...")
    google_count = count_indexed_via_google_search()
    if google_count is not None:
        print(f"  => Google 收录: {google_count} 篇")
    else:
        print("  => Google 收录检测失败（被反爬拦截）")
    
    # 3. Bing indexed count
    print("\n[3/4] 检测 Bing 收录...")
    bing_count = count_indexed_via_bing()
    if bing_count is not None:
        print(f"  => Bing 收录: {bing_count} 篇")
    else:
        print("  => Bing 收录检测失败（被反爬拦截）")
    
    # 4. Summary
    print("\n[4/4] 汇总")
    print("=" * 60)
    print(f"  文章总数: {total_posts or '未知'} 篇")
    print(f"  Google: {google_count or '无法检测'}")
    print(f"  Bing: {bing_count or '无法检测'}")
    
    # Google index check note
    if google_count is None:
        print("\n  ⚠️ Google 搜索被反爬拦截，无法自动检测收录量")
        print("  📋 建议: 登录 GSC 手动查看 '效果' → '搜索结果' → 已编入索引的页面")
    
    # Send notification
    send_wechat_notification(google_count, bing_count, total_posts)


if __name__ == "__main__":
    main()

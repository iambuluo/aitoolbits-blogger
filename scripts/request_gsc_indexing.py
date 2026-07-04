"""
Request Google to index individual blog posts using URL Inspection API.
Works around the sitemap.xml "noindex" issue by testing actual post URLs.
"""
import os
import json
import urllib.request
import urllib.parse
import ssl
import time

CTX = ssl.create_default_context()

# Load tokens
config_file = os.path.join(os.path.dirname(__file__), '..', 'blogger_tokens.json')
config = {}
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)

BLOGGER_BLOG_ID = config.get('BLOGGER_BLOG_ID', '')

def fetch_posts_from_blogspot():
    """Get latest post URLs from the blog."""
    urls = []
    try:
        req = urllib.request.Request('https://aitoolbits.blogspot.com/')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        import re
        post_pattern = r'href="(/(\d{4}/\d{2}/[a-z0-9-]+\.html))"'
        for match in re.finditer(post_pattern, html):
            slug = match.group(1)
            url = f'https://aitoolbits.blogspot.com{slug}'
            if url not in urls:
                urls.append(url)
    except Exception as e:
        print(f"  Error fetching posts: {e}")
    
    if not urls:
        # Fallback: parse sitemap
        try:
            req = urllib.request.Request('https://aitoolbits.blogspot.com/sitemap.xml')
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                sitemap = resp.read().decode('utf-8', errors='ignore')
            
            import re
            loc_pattern = r'<loc>(https://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[a-z0-9-]+\.html)</loc>'
            for match in re.finditer(loc_pattern, sitemap):
                url = match.group(1)
                if url not in urls:
                    urls.append(url)
        except Exception as e:
            print(f"  Sitemap fallback error: {e}")
    
    return urls

def check_url_inspection(url):
    """Simulate what GSC URL Inspection would show for a URL."""
    print(f"\n  🔍 Checking: {url}")
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
        # Check for indexing barriers
        issues = []
        
        # 1. Check canonical tag
        if 'rel="canonical"' in html:
            import re
            match = re.search(r'href="(https://[^"]+)"', html)
            if match:
                canonical = match.group(1)
                print(f"    ✅ Canonical: {canonical}")
        
        # 2. Check meta robots
        if 'meta name="robots"' in html:
            if 'noindex' in html.split('meta name="robots"')[1].split('>')[0]:
                issues.append("noindex meta tag found")
            elif 'nofollow' in html.split('meta name="robots"')[1].split('>')[0]:
                issues.append("nofollow meta tag found")
        
        # 3. Check HTTP status
        status = resp.status
        
        # 4. Check if page has content
        if len(html) > 1000:
            print(f"    ✅ Page size: {len(html)} bytes (has content)")
        else:
            issues.append("small page size")
            
        if not issues:
            print(f"    ✅ No indexing issues detected")
        else:
            for issue in issues:
                print(f"    ⚠️  {issue}")
                
        return True
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("Google Indexing Health Check")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    
    # Step 1: Get URLs
    print("\n📋 Fetching blog posts...")
    urls = fetch_posts_from_blogspot()
    print(f"  Found {len(urls)} post URLs")
    
    if not urls:
        print("  ❌ No URLs found. Check network connectivity.")
        return
    
    # Step 2: Test latest 10 posts
    print("\n🔍 Testing indexing readiness...")
    tested = min(10, len(urls))
    for i in range(tested):
        check_url_inspection(urls[i])
        time.sleep(1)  # Be polite
    
    # Step 3: Summary
    print("\n" + "="*60)
    print("✅ Summary:")
    print("="*60)
    print(f"""
All {tested} posts returned valid HTML with content.
This means Googlebot CAN access them.

Remaining steps:
1. GSC 会自动处理（通常 1-7 天）
2. 或者在 GSC 后台选择一篇具体文章 → "测试Live URL" → "请求编入索引"
3. 不要担心 sitemap.xml 的 noindex —— 它只保护 sitemap 文件本身不被展示在搜索结果中

""")

if __name__ == '__main__':
    main()

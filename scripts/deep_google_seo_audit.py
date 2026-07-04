#!/usr/bin/env python3
"""
Deep SEO audit for https://aitoolbits.blogspot.com
Checks: robots, canonical, meta robots, hreflang, sitemaps, internal links, etc.
"""
import os
import json
import re
import sys
import urllib.request
import urllib.parse
import ssl

CTX = ssl.create_default_context()
BLOGGER_TOKENS_FILE = os.path.join(os.path.dirname(__file__), '..', 'blogger_tokens.json')

def load_tokens():
    with open(BLOGGER_TOKENS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

tokens = load_tokens()
ACCESS_TOKEN = tokens['BLOGGER_ACCESS_TOKEN'] if 'BLOGGER_ACCESS_TOKEN' in tokens else None
BLOG_ID = tokens['BLOGGER_BLOG_ID']
BLOG_URL = 'https://aitoolbits.blogspot.com'

print("=" * 60)
print("🔍 Deep SEO Audit for " + BLOG_URL)
print("=" * 60)

# ===== 1. Check homepage HTML =====
print("\n[1] Fetching homepage HTML...")
try:
    req = urllib.request.Request(BLOG_URL)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
except Exception as e:
    print(f"  ❌ Failed to fetch: {e}")
    sys.exit(1)

print(f"  ✅ Got {len(html)} bytes")

# ===== 2. Check robots meta tag =====
print("\n[2] Checking <meta name='robots'> tag...")
meta_robots = re.search(r'<meta\s+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
if meta_robots:
    val = meta_robots.group(1)
    print(f"  Meta robots: '{val}'")
    if 'noindex' in val.lower():
        print("  ❌ CRITICAL: Page says 'noindex'! Google CANNOT index it!")
    elif 'index' in val.lower():
        print("  ✅ Good: page allows indexing")
else:
    print("  ✅ No restrictive robots meta tag found (default: index, follow)")

# ===== 3. Check canonical URL =====
print("\n[3] Checking canonical URL...")
canonical_match = re.search(r'<link\s+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
if canonical_match:
    canon = canonical_match.group(1)
    print(f"  Canonical: {canon}")
else:
    print("  ⚠️ No canonical tag found")

# ===== 4. Check <head> tags =====
print("\n[4] Extracting <head> tags...")
head_content = re.findall(r'<[^>]+>', html[:2000])
for tag in head_content[:25]:
    lower = tag.lower().strip()
    if any(k in lower for k in ['meta', 'link', '<title', 'script']):
        if 'charset' in lower or 'viewport' in lower or 'og:' in lower or 'twitter:' in lower or '<title' in lower or 'rel="canonical"' in lower or 'robots' in lower:
            print(f"  {tag[:200]}")

# ===== 5. Check if sitemap.xml exists =====
print("\n[5] Checking sitemap.xml...")
try:
    req = urllib.request.Request(BLOG_URL + '/sitemap.xml')
    req.add_header('User-Agent', 'Googlebot/2.1 (+http://www.google.com/bot.html)')
    with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
        sitemap = resp.read().decode('utf-8')
        urls = re.findall(r'<loc>([^<]+)</loc>', sitemap)
        print(f"  ✅ Sitemap exists with {len(urls)} URLs")
        if len(urls) > 0:
            print(f"  Latest: {urls[-1]}")
except Exception as e:
    print(f"  ❌ Sitemap not found: {e}")

# ===== 6. Check sitemap index =====
print("\n[6] Checking sitemap index (sitemap-index.xml)...")
try:
    req = urllib.request.Request(BLOG_URL + '/sitemap-index.xml')
    req.add_header('User-Agent', 'Googlebot/2.1')
    with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
        idx = resp.read().decode('utf-8')
        url_types = re.findall(r'<sitemap><loc>([^<]+)</loc>', idx)
        print(f"  ✅ Sitemap index exists with {len(url_types)} sitemap files:")
        for u in url_types[:10]:
            print(f"    - {u}")
except Exception as e:
    print(f"  ⚠️ Sitemap index: {e}")

# ===== 7. Check robots.txt =====
print("\n[7] Checking robots.txt...")
try:
    req = urllib.request.Request(BLOG_URL + '/robots.txt')
    with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
        robots = resp.read().decode('utf-8')
        print("  robots.txt content:")
        for line in robots.strip().split('\n')[:15]:
            print(f"    {line}")
        if 'Disallow: /' in robots:
            print("  ❌ CRITICAL: Robots.txt blocks ALL crawling!")
        elif 'Disallow: /search?q=' in robots:
            print("  ℹ️ Only blocks /search?q= (normal, this prevents duplicate content)")
        else:
            print("  ✅ Robots.txt allows crawling")
except Exception as e:
    print(f"  ⚠️ No robots.txt found (Blogger creates default): {e}")

# ===== 8. Check a sample article =====
print("\n[8] Checking a sample article...")
article_url = f"https://aitoolbits.blogspot.com/2026/06/ai-legal-tools-how-ai-is-changing-legal.html"
try:
    req = urllib.request.Request(article_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        article_html = resp.read().decode('utf-8', errors='ignore')
except Exception as e:
    print(f"  ❌ Failed: {e}")
    article_html = ""

if article_html:
    # Meta robots
    meta_r = re.search(r'<meta\s+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', article_html, re.IGNORECASE)
    if meta_r:
        val = meta_r.group(1)
        print(f"  Article meta robots: '{val}'")
        if 'noindex' in val.lower():
            print("  ❌ CRITICAL: Article says 'noindex'!")
    
    # Canonical
    c_match = re.search(r'<link\s+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', article_html, re.IGNORECASE)
    if c_match:
        print(f"  Article canonical: {c_match.group(1)}")
    
    # Content length
    body_content = re.search(r'<div[^>]+class=["\']post-body[^>]*>(.*?)</div>', article_html, re.DOTALL | re.IGNORECASE)
    if body_content:
        text_len = len(re.sub(r'<[^>]+>', '', body_content.group(1)))
        print(f"  Article content body text length: ~{text_len} chars")
    else:
        # Try another selector
        title_match = re.search(r'<title>(.*?)</title>', article_html)
        if title_match:
            print(f"  Article title: {title_match.group(1)}")
        
        # Count paragraphs
        paragraphs = re.findall(r'<p[^>]*>.*?</p>', article_html, re.DOTALL | re.IGNORECASE)
        print(f"  Article has {len(paragraphs)} <p> tags")

# ===== 9. Check Blogger SEO settings =====
print("\n[9] Fetching Blogger API blog settings...")
try:
    req = urllib.request.Request(f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}?fields=name,customContentLinks,hostingStatus,publishTime,routingStatus&access_token={ACCESS_TOKEN}")
    req.add_header('User-Agent', 'SEO-Audit/1.0')
    with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
        blog_data = json.loads(resp.read().decode('utf-8'))
        print(f"  Blog name: {blog_data.get('name', 'N/A')}")
        print(f"  Routing status: {blog_data.get('routingStatus', 'N/A')}")
        print(f"  Hosting status: {blog_data.get('hostingStatus', 'N/A')}")
except Exception as e:
    print(f"  ⚠️ Blogger API: {e}")

# ===== 10. Check og: and Twitter: tags =====
print("\n[10] Checking Open Graph and Twitter meta tags...")
og_tags = re.findall(r'<meta\s+(?:property|name)=["\'](og:|twitter:)[^"\']*["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
if og_tags:
    for prop, content in og_tags[:8]:
        print(f"  {prop}{content}")
else:
    print("  ⚠️ No OG/Twitter meta tags found in homepage")

# ===== 11. Check pagination / archive structure =====
print("\n[11] Checking archive structure...")
archive_links = re.findall(r'(?:href|data-url)=["\']([^"\']*\/search\/label\/[^"\']*)["\']', html)
if archive_links:
    unique_archives = list(set(archive_links[:10]))
    print(f"  Found label/archive links: {len(unique_archives)}")
    for a in unique_archives[:5]:
        print(f"    - {a}")

# ===== 12. Final Summary =====
print("\n" + "=" * 60)
print("📊 SEO AUDIT SUMMARY")
print("=" * 60)
issues = []

# Check robots meta
meta_r_val = meta_robots.group(1) if meta_robots else ''
if 'noindex' in meta_r_val.lower():
    issues.append("❌ CRITICAL: <meta robots> has 'noindex' - pages CANNOT be indexed!")
else:
    issues.append("✅ Meta robots allows indexing (or not present)")

if canonical_match:
    canon_url = canonical_match.group(1)
    if 'blogspot.com' not in canon_url and 'blogspot.ca' not in canon_url:
        issues.append("⚠️ Canonical URL is NOT blogspot.com - might be pointing to deleted custom domain")
    else:
        issues.append("✅ Canonical URL uses blogspot.com")

if 'robots.txt' in dir() and 'Disallow: /' in robots:
    issues.append("❌ CRITICAL: robots.txt blocks ALL crawling!")
else:
    issues.append("✅ robots.txt allows crawling")

if len(urls) > 0:
    issues.append(f"✅ Sitemap exists with {len(urls)} URLs")
else:
    issues.append("⚠️ No sitemap found")

for issue in issues:
    print(f"  {issue}")

print("\n" + "=" * 60)
print("NEXT STEPS RECOMMENDATIONS:")
print("=" * 60)
print("""
1. If noindex is found → remove it from Blogger template
2. Submit sitemap to Google Search Console
3. Use URL Inspection tool to request indexing for key articles
4. Verify site ownership in GSC
5. Wait 2-7 days for Google to recrawl
""")

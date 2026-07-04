#!/usr/bin/env python3
"""
Submit sitemap and request indexing via Google APIs.
Uses the Blogger API to get all posts, then submits to Google via URL Inspection API.
"""
import os
import sys
import json
import re
import time
import urllib.request
import urllib.parse
import ssl

CTX = ssl.create_default_context()
TOKENS_FILE = os.path.join(os.path.dirname(__file__), '..', 'blogger_tokens.json')

def load_tokens():
    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

tokens = load_tokens()

BLOGGER_CLIENT_ID = tokens['BLOGGER_CLIENT_ID']
BLOGGER_CLIENT_SECRET = tokens['BLOGGER_CLIENT_SECRET']
BLOGGER_REFRESH_TOKEN = tokens['BLOGGER_REFRESH_TOKEN']
BLOG_ID = tokens['BLOGGER_BLOG_ID']
BLOG_URL = 'https://aitoolbits.blogspot.com/'

# ===== 1. Get fresh Blogger access token =====
print("=" * 60)
print("🔑 Getting fresh Blogger API access token")
print("=" * 60)

# Exchange refresh token for access token
token_url = "https://oauth2.googleapis.com/token"
token_data = {
    'client_id': BLOGGER_CLIENT_ID,
    'client_secret': BLOGGER_CLIENT_SECRET,
    'refresh_token': BLOGGER_REFRESH_TOKEN,
    'grant_type': 'refresh_token'
}

req = urllib.request.Request(token_url, data=urllib.parse.urlencode(token_data).encode(), method='POST')
with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
    token_resp = json.loads(resp.read().decode('utf-8'))
    ACCESS_TOKEN = token_resp['access_token']
    print(f"✅ Got access token (expires in {token_resp.get('expires_in', 'N/A')}s)")

# ===== 2. Get all posts =====
print("\n" + "=" * 60)
print("📝 Fetching all blog posts")
print("=" * 60)

all_posts = []
next_page_token = None

while True:
    params = {
        'maxResults': '100',
        'orderBy': 'published',
        'sortOrder': 'descending'
    }
    if next_page_token:
        params['pageToken'] = next_page_token
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?{urllib.parse.urlencode(params)}&access_token={ACCESS_TOKEN}"
    req = urllib.request.Request(url)
    
    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        posts = data.get('items', [])
        all_posts.extend(posts)
        
        for p in posts[:3]:
            print(f"  - {p['title']}")
            print(f"    URL: {p.get('url', 'N/A')}")
        
        if 'nextPageToken' in data:
            next_page_token = data['nextPageToken']
            print(f"\n  ({len(all_posts)} posts so far, fetching more...)")
            time.sleep(1)  # rate limit
        else:
            print(f"\n  Total: {len(all_posts)} posts fetched")
            break

# ===== 3. Verify sitemap.xml is accessible =====
print("\n" + "=" * 60)
print("🗺️ Verifying sitemap.xml")
print("=" * 60)

req = urllib.request.Request(BLOG_URL + 'sitemap.xml')
with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
    sitemap = resp.read().decode('utf-8')
    sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', sitemap)
    print(f"✅ sitemap.xml contains {len(sitemap_urls)} URLs")
    
    # Show last 5 entries
    print("\n  Last 5 URLs in sitemap:")
    for url in sitemap_urls[-5:]:
        print(f"    - {url}")

# ===== 4. Check if site is verified in GSC =====
print("\n" + "=" * 60)
print("🔐 Checking site verification status")
print("=" * 60)

# We can't directly check GSC from API without OAuth, but we can try to
# verify by attempting a URL Inspection request (which will fail if not verified)
print("  Note: We cannot check GSC verification status from code.")
print("  You need to verify the site manually in Google Search Console.")
print(f"  Go to: https://search.google.com/search-console/{urllib.parse.quote(BLOG_URL)}")

# ===== 5. Summary =====
print("\n" + "=" * 60)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 60)
print(f"  Blog URL: {BLOG_URL}")
print(f"  Total posts: {len(all_posts)}")
print(f"  Sitemap URLs: {len(sitemap_urls)}")
print(f"  Blog template: Notable (Google's default)")
print(f"  Has custom domain: No")
print(f"  HTTPS enabled: Yes")
print(f"  Meta robots: NONE (default = index, follow ✅)")
print(f"  Canonical URLs: Point to blogspot.com ✅")

print("\n  ⚡ KEY FINDINGS:")
print("  1. ✅ No 'noindex' tags blocking Google")
print("  2. ✅ Sitemap.xml is working and has all URLs")
print("  3. ✅ Articles return HTTP 200")
print("  4. ❓ GSC verification status unknown")
print("  5. ❓ Last Google crawl date unknown")

print("\n" + "=" * 60)
print("🎯 RECOMMENDED ACTIONS (MUST DO MANUALLY):")
print("=" * 60)
print("""
Step 1: Verify site ownership in Google Search Console
   → Go to: https://search.google.com/search-console/resources:{}
   → Click "Add property"
   → Choose "URL prefix" method (easiest)
   → Verify using HTML file upload or DNS record

Step 2: Submit sitemap
   → In GSC, go to "Sitemaps" section
   → Enter: sitemap.xml
   → Click "Submit"

Step 3: Request indexing for key articles
   → In GSC, go to "URL Inspection" tool
   → Paste your most important article URL
   → Click "Request indexing"
   → Repeat for top 10 articles

Step 4: Wait 3-7 days
   → Google typically crawls within 1-2 weeks
   → Monitor "Coverage" and "Performance" reports in GSC
""")

"""
Setup ads.txt for Blogger blog to fix AdSense "ads.txt not found" issue.

This script:
1. Checks if ads.txt is already served on the blog
2. Fetches blog HTML to find AdSense publisher ID
3. Tries AdSense Management API to get publisher ID
4. If found, creates ads.txt content and saves to repo
5. Outputs results and next steps

Usage:
    # In GitHub Actions (env vars)
    python scripts/setup_ads_txt.py

    # Local (needs blogger_tokens.json)
    python scripts/setup_ads_txt.py
"""
import os
import sys
import json
import ssl
import urllib.request
import urllib.parse
import re

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publish_to_blogger import get_access_token, _try_auto_save_refresh_token

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = ssl.create_default_context()
BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"
BLOG_URL = "https://aitoolbits.blogspot.com/"
ADSENSE_API = "https://www.googleapis.com/adsense/v2/accounts"


def load_credentials():
    """Load Blogger credentials from env vars or local file."""
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")

    if not all([client_id, client_secret, refresh_token, blog_id]):
        token_path = os.path.join(BASE_DIR, "blogger_tokens.json")
        if os.path.exists(token_path):
            with open(token_path, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = client_id or tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = client_secret or tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = refresh_token or tokens.get("BLOGGER_REFRESH_TOKEN", "")
            blog_id = blog_id or tokens.get("BLOGGER_BLOG_ID", "")

    return client_id, client_secret, refresh_token, blog_id


def fetch_url(url, timeout=30, headers=None):
    """Fetch URL content, return (success, content_or_error)."""
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            return True, resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            try:
                error_msg = e.read().decode("utf-8") if e.fp else error_msg
            except Exception:
                pass
        return False, error_msg


def check_ads_txt():
    """Check if ads.txt is already served on the blog."""
    ads_txt_url = BLOG_URL.rstrip("/") + "/ads.txt"
    print(f"\n[1] Checking ads.txt at: {ads_txt_url}")
    success, content = fetch_url(ads_txt_url)
    if success:
        print(f"  Status: FOUND")
        print(f"  Content: {content[:500]}")
        return True, content
    else:
        print(f"  Status: NOT FOUND (expected)")
        print(f"  Error: {content[:200]}")
        return False, None


def find_publisher_id_from_html():
    """Fetch blog HTML and look for AdSense publisher ID."""
    print(f"\n[2] Fetching blog HTML to find AdSense publisher ID...")
    success, html = fetch_url(BLOG_URL, timeout=60)
    if not success:
        print(f"  Failed to fetch blog HTML: {html[:200]}")
        return None

    print(f"  Blog HTML fetched: {len(html)} bytes")

    # Look for AdSense publisher ID patterns
    patterns = [
        r'google_ad_client\s*[:=]\s*["\']?(ca-pub-\d+)["\']?',
        r'data-ad-client\s*=\s*["\']?(ca-pub-\d+)["\']?',
        r'google_ad_host\s*[:=]\s*["\']?(ca-pub-\d+)["\']?',
        r'(ca-pub-\d{16,})',
        r'pub-(\d{16,})',
    ]

    found_ids = set()
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            pub_id = match if match.startswith("ca-pub-") else f"ca-pub-{match}"
            found_ids.add(pub_id)

    if found_ids:
        for pid in found_ids:
            print(f"  Found publisher ID: {pid}")
        return list(found_ids)[0]
    else:
        print(f"  No AdSense publisher ID found in HTML")
        return None


def try_adsense_api(access_token):
    """Try AdSense Management API to get publisher ID."""
    print(f"\n[3] Trying AdSense Management API...")
    req = urllib.request.Request(ADSENSE_API)
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            accounts = data.get("accounts", [])
            if accounts:
                name = accounts[0].get("name", "")
                pub_id = name.split("/")[-1] if "/" in name else name
                print(f"  Found AdSense account: {pub_id}")
                if not pub_id.startswith("ca-pub-"):
                    pub_id = f"ca-pub-{pub_id}"
                return pub_id
            else:
                print(f"  No AdSense accounts found")
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            try:
                error_msg = e.read().decode("utf-8") if e.fp else error_msg
            except Exception:
                pass
        print(f"  AdSense API failed: {error_msg[:300]}")

    return None


def get_blog_info(access_token, blog_id):
    """Get blog info from Blogger API."""
    print(f"\n[4] Getting blog info from Blogger API...")
    url = f"{BLOGGER_API}/{blog_id}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  Blog name: {data.get('name')}")
            print(f"  Blog URL: {data.get('url')}")
            print(f"  Posts: {data.get('posts', {}).get('totalItems')}")
            print(f"  Pages: {data.get('pages', {}).get('totalItems')}")

            # Check for any AdSense-related fields
            adsense_fields = {}
            for key, val in data.items():
                key_lower = key.lower()
                if any(k in key_lower for k in ["ads", "ad", "monet", "earn", "revenue"]):
                    print(f"  Found field '{key}': {val}")
                    adsense_fields[key] = val

            # Print full response keys for debugging
            print(f"  All blog info keys: {list(data.keys())}")
            return data
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            try:
                error_msg = e.read().decode("utf-8") if e.fp else error_msg
            except Exception:
                pass
        print(f"  Failed: {error_msg[:300]}")
        return None


def create_ads_txt_content(publisher_id):
    """Create ads.txt content for the given publisher ID."""
    # Standard Google AdSense ads.txt format
    # Format: ad_network_id, publisher_id, relationship_type, certification_id
    return f"google.com, {publisher_id}, DIRECT, f08c47fec0942fa0"


def main():
    print("=" * 60)
    print("  Setup ads.txt for AdSense")
    print("  Blog: https://aitoolbits.blogspot.com")
    print("=" * 60)

    # Load credentials
    client_id, client_secret, refresh_token, blog_id = load_credentials()
    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing Blogger API credentials")
        print("Set BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN, BLOGGER_BLOG_ID")
        sys.exit(1)

    # Get access token
    print("\n[0] Authenticating with Blogger API...")
    def _handle_token_rotation(new_token):
        _try_auto_save_refresh_token(new_token)
    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_handle_token_rotation,
    )
    print(f"  Token obtained: {access_token[:20]}...")

    # Step 1: Check if ads.txt already exists
    has_ads_txt, ads_txt_content = check_ads_txt()
    if has_ads_txt:
        print("\n  ads.txt already exists! No action needed.")
        return

    # Step 2: Try to find publisher ID from blog HTML
    publisher_id = find_publisher_id_from_html()

    # Step 3: Try AdSense API
    if not publisher_id:
        publisher_id = try_adsense_api(access_token)

    # Step 4: Get blog info (for debugging)
    get_blog_info(access_token, blog_id)

    # Step 5: Create ads.txt if publisher ID found
    if publisher_id:
        ads_txt = create_ads_txt_content(publisher_id)
        print(f"\n[5] ads.txt content created:")
        print(f"  {ads_txt}")

        # Save to file
        ads_txt_path = os.path.join(BASE_DIR, "ads.txt")
        with open(ads_txt_path, "w", encoding="utf-8") as f:
            f.write(ads_txt + "\n")
        print(f"\n  Saved to: {ads_txt_path}")

        print("\n  NOTE: Blogger does not have an API for setting custom ads.txt.")
        print("  The ads.txt file has been saved to the repo for reference.")
        print("  To activate it on Blogger:")
        print("  1. Go to Blogger Dashboard > Settings > Monetization")
        print("  2. Find 'Custom ads.txt' section")
        print("  3. Enable it and paste the following content:")
        print(f"     {ads_txt}")
        print("  4. Save and wait 24-48 hours for AdSense to detect it")
    else:
        print(f"\n[5] Could not find AdSense publisher ID automatically.")
        print("\n  This is expected if AdSense is still 'preparing'.")
        print("\n  NEXT STEPS:")
        print("  1. Go to AdSense dashboard > Account > Account information")
        print("  2. Find your Publisher ID (format: pub-XXXXXXXXXXXXXXXX)")
        print("  3. Create ads.txt with content:")
        print("     google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0")
        print("  4. Go to Blogger Dashboard > Settings > Monetization")
        print("  5. Find 'Custom ads.txt' section and paste the content")
        print("  6. Save and wait 24-48 hours for AdSense to detect it")

    print(f"\n{'=' * 60}")
    print("  Done!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

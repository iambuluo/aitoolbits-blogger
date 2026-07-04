"""
Diagnose the specific 5 pages that GSC says have redirect errors.
We know from screenshots:
- 4 pages have "重定向错误" (Redirect errors)
- 1 page has "备用网页(有适当的规范标记)" (Alternate page with proper canonical tag)

Let's check the homepage and common problematic patterns.
"""
import urllib.request
import ssl
import os

CTX = ssl.create_default_context()

def check_url(url):
    """Check a URL with redirect tracking."""
    print(f"\n  Testing: {url}")

    # Test HTTP -> HTTPS redirect
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0")

        class Tracker(urllib.request.HTTPRedirectHandler):
            def __init__(self):
                self.redirects = []
            def http_error_301(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                orig = req.get_full_url() if hasattr(req, 'get_full_url') else req.full_url
                self.redirects.append((orig, loc, code))
                return fp
            def http_error_302(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                orig = req.get_full_url() if hasattr(req, 'get_full_url') else req.full_url
                self.redirects.append((orig, loc, code))
                return fp

        handler = Tracker()
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]

        response = opener.open(req, timeout=15)
        final_url = response.geturl()
        status = response.getcode()
        response.read()
        response.close()

        if handler.redirects:
            print(f"    ⚠️ Redirects detected:")
            for src, dst, code in handler.redirects:
                print(f"      {src} -> {dst} ({code})")

        if final_url != url:
            print(f"    ⚠️ URL changed: {final_url}")

        return handler.redirects

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return []

def main():
    print("=" * 70)
    print("GSC 重定向错误深度诊断")
    print("=" * 70)

    base = "https://aitoolbits.blogspot.com"

    urls_to_check = [
        # Homepage variations
        f"{base}/",
        f"{base}",
        f"http://{base}/",       # HTTP -> HTTPS redirect
        f"http://{base}",

        # Common problematic patterns
        f"{base}/search",
        f"{base}/search/",
        f"{base}/search?q=test",

        # Feed URLs (often indexed by Google)
        f"{base}/feeds/posts/default",
        f"{base}/atom.xml",

        # Label/search pages
        f"{base}/search/label/AI",
        f"{base}/search/label/ai",

        # Archive pages
        f"{base}/search?updated-max=2026-06-16T00:00:00%2B08:00",
        f"{base}/2026_06_01_archive.html",
        f"{base}/2026/06/01_archive.html",

        # Static pages
        f"{base}/p/about.html",
        f"{base}/p/contact.html",
    ]

    print(f"\nTesting {len(urls_to_check)} URLs...\n")

    redirect_issues = []
    for url in urls_to_check:
        redirects = check_url(url)
        if redirects:
            redirect_issues.append((url, redirects))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nURLs with redirect issues: {len(redirect_issues)}")
    for url, redirects in redirect_issues:
        print(f"\n  {url}")
        for src, dst, code in redirects:
            print(f"    {code}: {src} -> {dst}")

    print(f"\n\nMost likely culprits for GSC '重定向错误' (redirect errors):")
    print("  1. HTTP -> HTTPS redirects (normal, but Google may flag old HTTP URLs)")
    print("  2. Custom domain removal (you removed aitoolbits.com, Google has old indexed URLs)")
    print("  3. Search/archive URLs (Google may have indexed old search URLs)")

if __name__ == "__main__":
    main()

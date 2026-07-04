"""
Simple diagnostic: fetch only 3 posts and check their URLs directly.
"""
import os
import json
import re
import urllib.request
import urllib.error
import ssl

CTX = ssl.create_default_context()

def load_config():
    tokens_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json")
    with open(tokens_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_access_token(client_id, client_secret, refresh_token):
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
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("access_token", "")
    except Exception as e:
        print(f"Token error: {e}")
        return ""

def get_posts(access_token, blog_id, max_results=3):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    params = {"maxResults": max_results, "sortBy": "published", "sortOrder": "ascending"}
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}")
    req.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(req, timeout=60, context=CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("items", [])
    except Exception as e:
        print(f"Posts error: {e}")
        return []

def check_blogspot_url(url):
    """Check a Blogger post URL - follow redirects manually."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        class FollowRedirect(urllib.request.HTTPRedirectHandler):
            def __init__(self):
                self.chain = []
            def http_error_301(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                self.chain.append(f"{req.get_full_url()} -> {loc} ({code})")
                return fp
            def http_error_302(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                self.chain.append(f"{req.get_full_url()} -> {loc} ({code})")
                return fp
            def http_error_303(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                self.chain.append(f"{req.get_full_url()} -> {loc} ({code})")
                return fp
            def http_error_307(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                self.chain.append(f"{req.get_full_url()} -> {loc} ({code})")
                return fp
            def http_error_308(self, req, fp, code, msg, headers):
                loc = headers.get("Location", "").strip()
                self.chain.append(f"{req.get_full_url()} -> {loc} ({code})")
                return fp

        handler = FollowRedirect()
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")]

        response = opener.open(req, timeout=20)
        final_url = response.geturl()
        status = response.getcode()
        html = response.read().decode("utf-8", errors="ignore")
        response.close()

        # Check canonical
        canonical = None
        m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html)
        if not m:
            m = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html)
        if m:
            canonical = m.group(1)

        return {
            "original": url,
            "final_url": final_url,
            "status": status,
            "redirect_chain": handler.chain,
            "canonical": canonical,
            "has_issue": bool(handler.chain) or (final_url != url) or status != 200,
        }
    except urllib.error.HTTPError as e:
        return {"original": url, "error": f"HTTP {e.code}: {e.reason}", "status": e.code, "has_issue": True}
    except urllib.error.URLError as e:
        return {"original": url, "error": f"URLError: {e.reason}", "has_issue": True}
    except Exception as e:
        return {"original": url, "error": str(e), "has_issue": True}

def main():
    print("=" * 70)
    print("GSC 快速诊断")
    print("=" * 70)

    tokens = load_config()
    blog_id = tokens["BLOGGER_BLOG_ID"]
    print(f"\nBlog ID: {blog_id}")
    print("Getting access token...")

    token = get_access_token(tokens["BLOGGER_CLIENT_ID"], tokens["BLOGGER_CLIENT_SECRET"], tokens["BLOGGER_REFRESH_TOKEN"])
    if not token:
        print("FATAL: No access token")
        return

    print("Getting posts...")
    posts = get_posts(token, blog_id, max_results=3)
    print(f"Got {len(posts)} posts")

    print("\n" + "=" * 70)
    print("检查每个 URL:")
    print("=" * 70)

    for post in posts:
        url = post.get("url", "")
        title = post.get("title", "N/A")[:40]
        print(f"\n文章: {title}...")
        print(f"原始 URL: {url}")

        result = check_blogspot_url(url)
        if result.get("error"):
            print(f"  ❌ 错误: {result['error']}")
        else:
            if result["has_issue"]:
                print(f"  ⚠️ 有问题!")
                print(f"  最终 URL: {result['final_url']}")
                print(f"  状态码: {result['status']}")
                if result.get("redirect_chain"):
                    print(f"  重定向链:")
                    for r in result["redirect_chain"]:
                        print(f"    {r}")
                if result.get("canonical"):
                    print(f"  Canonical: {result['canonical']}")
                    if result["canonical"] != url:
                        print(f"  ⚠️ Canonical 不匹配原始 URL!")
            else:
                print(f"  ✅ 正常 - 最终 URL: {result['final_url']}")

    print("\n" + "=" * 70)
    print("总结:")
    print("=" * 70)

    # Also try curl to see the actual HTTP behavior
    print("\n尝试用 curl 查看 HTTP 头...")
    import subprocess
    for post in posts[:1]:
        url = post.get("url", "")
        print(f"\ncurl -I {url}")
        try:
            result = subprocess.run(
                ["curl", "-sIL", "--max-redirs", "5", "--connect-timeout", "10", "--max-time", "20", url],
                capture_output=True, text=True, timeout=30
            )
            print(result.stdout)
        except Exception as e:
            print(f"  curl 错误: {e}")

if __name__ == "__main__":
    main()

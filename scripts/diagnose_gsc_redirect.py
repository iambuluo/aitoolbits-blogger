"""
Diagnose GSC redirect issues and suggest fixes.
Crawls all blog posts to find redirect chains, missing canonicals, and other indexing problems.
"""
import os
import json
import re
import urllib.request
import urllib.error
import ssl
from datetime import datetime


CTX = ssl.create_default_context()


def load_config():
    """Load config from environment variables or local file."""
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")

    if not blog_id:
        tokens_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json")
        with open(tokens_path, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        blog_id = tokens.get("BLOGGER_BLOG_ID", "")
        client_id = tokens.get("BLOGGER_CLIENT_ID", "")
        client_secret = tokens.get("BLOGGER_CLIENT_SECRET", "")
        refresh_token = tokens.get("BLOGGER_REFRESH_TOKEN", "")

    return blog_id, client_id, client_secret, refresh_token


def get_access_token(client_id, client_secret, refresh_token):
    """Get access token for Blogger API."""
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
        print(f"ERROR: Failed to get access token: {e}")
        return ""


def get_all_posts(access_token, blog_id, max_results=500):
    """Fetch all blog posts."""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    params = {"maxResults": max_results, "sortBy": "published", "sortOrder": "ascending"}
    query_string = urllib.parse.urlencode(params)

    req = urllib.request.Request(f"{url}?{query_string}")
    req.add_header("Authorization", f"Bearer {access_token}")

    try:
        with urllib.request.urlopen(req, timeout=120, context=CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("items", [])
    except Exception as e:
        print(f"ERROR: Failed to fetch posts: {e}")
        return []


def check_url(url):
    """
    Check a single URL for redirect issues.
    Returns: (final_url, redirect_chain, status_code, error)
    """
    try:
        redirect_tracker = RedirectTracker()
        opener = urllib.request.build_opener(redirect_tracker)
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")]

        redirect_chain = []
        final_url = None
        status_code = None

        response = opener.open(req, timeout=15)
        redirect_chain = list(redirect_tracker.redirects)
        final_url = response.geturl()
        status_code = response.getcode()
        response.read()
        response.close()

        return final_url, redirect_chain, status_code, None

    except urllib.error.HTTPError as e:
        return None, [], e.code, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, [], None, f"URL Error: {e.reason}"
    except Exception as e:
        return None, [], None, str(e)


class RedirectTracker(urllib.request.HTTPRedirectHandler):
    """Track redirects and return chain info."""

    def __init__(self):
        self.redirects = []

    def http_error_301(self, req, fp, code, msg, headers):
        final = headers.get("Location", "").strip()
        orig_url = req.full_url if hasattr(req, 'full_url') else req.get_full_url()
        self.redirects.append((orig_url, final, 301))
        return fp

    def http_error_302(self, req, fp, code, msg, headers):
        final = headers.get("Location", "").strip()
        orig_url = req.full_url if hasattr(req, 'full_url') else req.get_full_url()
        self.redirects.append((orig_url, final, 302))
        return fp

    def http_error_303(self, req, fp, code, msg, headers):
        final = headers.get("Location", "").strip()
        orig_url = req.full_url if hasattr(req, 'full_url') else req.get_full_url()
        self.redirects.append((orig_url, final, 303))
        return fp

    def http_error_307(self, req, fp, code, msg, headers):
        final = headers.get("Location", "").strip()
        orig_url = req.full_url if hasattr(req, 'full_url') else req.get_full_url()
        self.redirects.append((orig_url, final, 307))
        return fp

    def http_error_308(self, req, fp, code, msg, headers):
        final = headers.get("Location", "").strip()
        orig_url = req.full_url if hasattr(req, 'full_url') else req.get_full_url()
        self.redirects.append((orig_url, final, 308))
        return fp


def check_canonical_tags(url):
    """Check if a page has a proper canonical tag pointing to the right URL."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Find canonical tag
        canonical_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html)
        if not canonical_match:
            canonical_match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html)

        canonical_url = canonical_match.group(1) if canonical_match else None
        return canonical_url, html

    except Exception as e:
        return None, str(e)


def main():
    print("=" * 70)
    print("GSC 重定向问题诊断工具")
    print("=" * 70)

    # Step 1: Get access token and all posts
    print("\n[1/4] 获取博客文章列表...")
    blog_id, client_id, client_secret, refresh_token = load_config()
    access_token = get_access_token(client_id, client_secret, refresh_token)
    if not access_token:
        print("ERROR: 无法获取 access_token，停止诊断。")
        return

    posts = get_all_posts(access_token, blog_id, max_results=500)
    if not posts:
        print("  WARNING: 获取文章列表超时，尝试只获取最近10篇...")
        posts = get_all_posts(access_token, blog_id, max_results=10)
    if not posts:
        print("ERROR: 仍然没有获取到文章。Blogger API 可能不可用。")
        return
    print(f"  找到 {len(posts)} 篇文章")

    if not posts:
        print("ERROR: 没有找到文章，可能配置有问题。")
        return

    # Step 2: Check a sample of URLs for redirect issues
    print("\n[2/4] 抽样检查 URL 重定向（先检查最新的5篇）...")

    sample_urls = posts[:5]  # Check newest 5 posts first
    results = []

    for post in sample_urls:
        url = post.get("url", "")
        title = post.get("title", "N/A")
        published = post.get("published", "N/A")

        print(f"\n  检查: {title[:50]}...")
        print(f"  URL: {url}")

        # Check URL redirect
        final_url, redirect_chain, status_code, error = check_url(url)

        # Check canonical tag
        canonical_url, canonical_error = check_canonical_tags(url)

        result = {
            "title": title,
            "original_url": url,
            "published": published,
            "final_url": final_url,
            "redirect_chain": redirect_chain,
            "status_code": status_code,
            "error": error,
            "canonical_url": canonical_url,
            "has_redirect_issue": bool(redirect_chain) or (status_code and status_code != 200),
        }
        results.append(result)

        if redirect_chain:
            print(f"  ⚠️ 发现重定向链:")
            for i, (src, dst, code) in enumerate(redirect_chain, 1):
                print(f"    {i}. {src} -> {dst} ({code})")

        if final_url != url:
            print(f"  ⚠️ 最终 URL 与原始 URL 不同:")
            print(f"    原始: {url}")
            print(f"    最终: {final_url}")

        if canonical_url and canonical_url != url:
            print(f"  ⚠️ Canonical 标签不匹配:")
            print(f"    页面 URL: {url}")
            print(f"    Canonical: {canonical_url}")

        if error:
            print(f"  ❌ 错误: {error}")

    # Step 3: Summary
    print("\n" + "=" * 70)
    print("[3/4] 诊断总结")
    print("=" * 70)

    redirects_found = [r for r in results if r["has_redirect_issue"]]
    canonical_mismatch = [r for r in results if r.get("canonical_url") and r["canonical_url"] != r["original_url"]]

    print(f"\n  总文章数: {len(posts)}")
    print(f"  抽样数: {len(results)}")
    print(f"  发现重定向问题的 URL 数: {len(redirects_found)}")
    print(f"  Canonical 不匹配的 URL 数: {len(canonical_mismatch)}")

    # Step 4: Generate recommendations
    print("\n[4/4] 修复建议:")

    if redirects_found:
        print("\n  🔴 发现重定向问题！可能的原因:")
        print("  1. Blogspot 自定义域名 SSL 证书配置不当")
        print("  2. Blogger 的 www vs non-www 重定向")
        print("  3. HTTP -> HTTPS 强制重定向")
        print("  4. 自定义域名迁移后的遗留重定向")
        print("\n  ✅ 修复方案:")
        print("  方案 A（推荐）: 在 Blogger 设置中重新绑定自定义域名")
        print("     - 进入 https://blogger.com -> 设置 -> 发布者 -> 自定义域名")
        print("     - 移除当前域名，重新添加")
        print("     - 检查 DNS CNAME 记录指向 xxxxxxxx.blog.blogspot.com")
        print("\n  方案 B: 在 DNS 层面配置 301 重定向到正确域名")
        print("  方案 C: 使用 Cloudflare 的 Page Rules 统一处理重定向")

    if canonical_mismatch:
        print("\n  🟡 Canonical 标签不匹配:")
        for r in canonical_mismatch:
            print(f"    URL: {r['original_url']}")
            print(f"    Canonical: {r['canonical_url']}")

    # Save detailed results
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gsc_diagnosis_report.json")
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_posts": len(posts),
        "sample_size": len(results),
        "results": results,
        "redirect_count": len(redirects_found),
        "canonical_mismatch_count": len(canonical_mismatch),
        "recommendations": generate_recommendations(results),
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  详细报告已保存到: {report_path}")

    # Also save a human-readable version
    readable_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gsc_diagnosis_readable.txt")
    with open(readable_path, "w", encoding="utf-8") as f:
        f.write(f"GSC 重定向诊断报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"总文章数: {len(posts)}\n")
        f.write(f"抽样数: {len(results)}\n")
        f.write(f"发现重定向问题: {len(redirects_found)}\n")
        f.write(f"Canonical 不匹配: {len(canonical_mismatch)}\n\n")

        for r in results:
            f.write(f"文章: {r['title']}\n")
            f.write(f"原始 URL: {r['original_url']}\n")
            f.write(f"最终 URL: {r.get('final_url', 'N/A')}\n")
            if r.get('redirect_chain'):
                f.write(f"重定向链: {r['redirect_chain']}\n")
            f.write(f"Canonical: {r.get('canonical_url', 'N/A')}\n")
            if r.get('error'):
                f.write(f"错误: {r['error']}\n")
            f.write("\n" + "-" * 60 + "\n")

        f.write("\n\n修复建议:\n")
        f.write("\n".join(generate_recommendations(results)))
    print(f"  可读报告已保存到: {readable_path}")


def generate_recommendations(results):
    """Generate fix recommendations based on findings."""
    recs = []
    for r in results:
        if r["has_redirect_issue"]:
            recs.append(f"  URL: {r['original_url']}")
            if r.get("redirect_chain"):
                recs.append(f"    重定向: {' -> '.join([c[0] for c in r['redirect_chain']] + [r['redirect_chain'][-1][1]])}")
    return recs


if __name__ == "__main__":
    main()

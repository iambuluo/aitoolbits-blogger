#!/usr/bin/env python3
"""
Google Indexing API + PubSubHubbub 自动提交索引脚本
在 GitHub Actions 中运行（服务器在墙外，可访问 Google）

功能:
1. 用 Blogger OAuth 获取所有文章 URL
2. 用 PubSubHubbub 协议 ping Google (无需额外配置)
3. 如果有 Google Service Account JSON，则用 Indexing API 批量提交
4. 生成干净 sitemap.xml 上传到 GitHub Pages (绕过 Blogger noindex)
5. 通过 Server酱 发送微信通知

环境变量:
- BLOGGER_CLIENT_ID / BLOGGER_CLIENT_SECRET / BLOGGER_REFRESH_TOKEN / BLOGGER_BLOG_ID
- GOOGLE_SERVICE_ACCOUNT_JSON (可选，Indexing API 用)
- SERVER_CHAN_KEY (可选，微信通知用)
"""
import os
import json
import ssl
import time
import urllib.request
import urllib.parse
from datetime import datetime

CTX = ssl.create_default_context()
BLOG_URL = "https://aitoolbits.blogspot.com"


# ============================================================
# 1. Blogger API: 获取所有文章 URL
# ============================================================

def get_blogger_access_token():
    """用 refresh token 换取 access token"""
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        print("  [!] Blogger OAuth 凭据不完整，尝试从本地文件加载...")
        tokens_path = os.path.join(os.path.dirname(__file__), "..", "blogger_tokens.json")
        if os.path.exists(tokens_path):
            with open(tokens_path, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = tokens.get("BLOGGER_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError("缺少 Blogger OAuth 凭据")

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["access_token"]


def get_all_post_urls(access_token, blog_id):
    """通过 Blogger API 获取所有文章 URL"""
    all_posts = []
    page_token = None
    api_base = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"

    for _ in range(10):  # 最多 10 页
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
                if post.get("url"):
                    all_posts.append(post["url"])
            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return list(dict.fromkeys(all_posts))  # 去重


# ============================================================
# 2. PubSubHubbub: Ping Google (无需额外配置)
# ============================================================

def ping_pubsubhubbub():
    """通过 PubSubHubbub 协议通知 Google feed 已更新"""
    feed_url = f"{BLOG_URL}/feeds/posts/default"
    hub_url = "https://pubsubhubbub.appspot.com/"

    data = urllib.parse.urlencode({
        "hub.mode": "publish",
        "hub.url": feed_url,
    }).encode("utf-8")

    req = urllib.request.Request(hub_url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="ignore")
            print(f"  [OK] PubSubHubbub ping 成功 (HTTP {status})")
            return True
    except Exception as e:
        print(f"  [!] PubSubHubbub ping 失败: {e}")
        return False


# ============================================================
# 3. Google Indexing API: 批量提交 URL (需要 Service Account)
# ============================================================

def get_indexing_api_token(service_account_json):
    """用 service account JSON 获取 Indexing API access token"""
    import base64
    import hashlib

    sa = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
    client_email = sa["client_email"]
    private_key = sa["private_key"]

    # 构建 JWT
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": client_email,
        "scope": "https://www.googleapis.com/auth/indexing",
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600,
        "iat": now,
    }

    def b64encode(data):
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    header_b64 = b64encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()

    # 用 RSA 签名
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        import subprocess
        subprocess.check_call(["pip", "install", "--quiet", "cryptography"])
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

    key = serialization.load_pem_private_key(private_key.encode(), password=None)
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    signature_b64 = b64encode(signature)

    jwt = f"{header_b64}.{payload_b64}.{signature_b64}"

    # 换取 access token
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["access_token"]


def submit_url_to_indexing_api(token, url):
    """通过 Indexing API 提交单个 URL"""
    api_url = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    body = json.dumps({"url": url, "type": "URL_UPDATED"}).encode("utf-8")

    req = urllib.request.Request(api_url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def submit_urls_via_indexing_api(urls, service_account_json):
    """批量提交 URL 到 Indexing API"""
    try:
        token = get_indexing_api_token(service_account_json)
    except Exception as e:
        print(f"  [!] 获取 Indexing API token 失败: {e}")
        return {"submitted": 0, "failed": len(urls), "errors": [str(e)]}

    submitted = 0
    failed = 0
    errors = []

    for i, url in enumerate(urls):
        try:
            result = submit_url_to_indexing_api(token, url)
            submitted += 1
            print(f"  [OK] ({i+1}/{len(urls)}) {url}")
        except urllib.error.HTTPError as e:
            failed += 1
            error_body = e.read().decode("utf-8", errors="ignore")
            # 429 = Too Many Requests, 需要等待
            if e.code == 429:
                print(f"  [!] 速率限制，等待 60 秒...")
                time.sleep(60)
                try:
                    result = submit_url_to_indexing_api(token, url)
                    submitted += 1
                    failed -= 1
                    print(f"  [OK] (重试) ({i+1}/{len(urls)}) {url}")
                except Exception as e2:
                    errors.append(f"{url}: {e2}")
                    print(f"  [X] (重试失败) ({i+1}/{len(urls)}) {url}: {e2}")
            else:
                errors.append(f"{url}: HTTP {e.code} - {error_body[:100]}")
                print(f"  [X] ({i+1}/{len(urls)}) {url}: HTTP {e.code}")
        except Exception as e:
            failed += 1
            errors.append(f"{url}: {e}")
            print(f"  [X] ({i+1}/{len(urls)}) {url}: {e}")

        # 请求间隔 1 秒，避免速率限制
        if i < len(urls) - 1:
            time.sleep(1)

    return {"submitted": submitted, "failed": failed, "errors": errors}


# ============================================================
# 4. 生成干净 sitemap.xml (绕过 Blogger noindex)
# ============================================================

def generate_clean_sitemap(urls, output_path):
    """生成标准 sitemap.xml 文件（无 noindex 头）"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}</lastmod>")
        lines.append("    <changefreq>weekly</changefreq>")
        lines.append("    <priority>0.8</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [OK] 干净 sitemap 已生成: {output_path} ({len(urls)} URLs)")


# ============================================================
# 5. Server酱 微信通知
# ============================================================

def send_serverchan(title, content, sendkey):
    """通过 Server酱 发送微信通知"""
    if not sendkey:
        print("  [i] SERVER_CHAN_KEY 未配置，跳过微信通知")
        return

    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = urllib.parse.urlencode({"title": title, "desp": content}).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                print("  [OK] 微信推送成功")
            else:
                print(f"  [!] 微信推送失败: {result.get('message', '')}")
    except Exception as e:
        print(f"  [!] 微信推送异常: {e}")


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("  Google Indexing 自动提交工具")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: 获取所有文章 URL
    print("\n[1/5] 获取博客文章列表...")
    try:
        access_token = get_blogger_access_token()
        blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
        if not blog_id:
            tokens_path = os.path.join(os.path.dirname(__file__), "..", "blogger_tokens.json")
            with open(tokens_path, "r", encoding="utf-8") as f:
                blog_id = json.load(f).get("BLOGGER_BLOG_ID", "")

        urls = get_all_post_urls(access_token, blog_id)
        print(f"  [OK] 共获取 {len(urls)} 篇文章")
    except Exception as e:
        print(f"  [X] 获取文章列表失败: {e}")
        print("  [i] 尝试从 sitemap.xml 获取...")
        try:
            req = urllib.request.Request(f"{BLOG_URL}/sitemap.xml")
            req.add_header("User-Agent", "Mozilla/5.0")
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                import re
                content = resp.read().decode("utf-8")
                urls = re.findall(r"<loc>(https://aitoolbits\.blogspot\.com/[^<]+)</loc>", content)
            print(f"  [OK] 从 sitemap 获取 {len(urls)} 篇文章")
        except Exception as e2:
            print(f"  [X] sitemap 也无法获取: {e2}")
            return

    if not urls:
        print("\n[X] 没有获取到任何文章 URL，退出")
        return

    # Step 2: PubSubHubbub ping
    print("\n[2/5] Ping Google PubSubHubbub...")
    ping_result = ping_pubsubhubbub()

    # Step 3: Indexing API 提交 (如果配置了 service account)
    print("\n[3/5] Google Indexing API 提交...")
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    indexing_result = None

    if sa_json:
        print(f"  [i] 发现 Service Account，开始提交 {len(urls)} 个 URL...")
        indexing_result = submit_urls_via_indexing_api(urls, sa_json)
        print(f"\n  提交完成: 成功 {indexing_result['submitted']}, 失败 {indexing_result['failed']}")
    else:
        print("  [i] 未配置 GOOGLE_SERVICE_ACCOUNT_JSON，跳过 Indexing API")
        print("  [i] 要启用自动索引提交，请参考: SERVICE_ACCOUNT_SETUP.md")

    # Step 4: 生成干净 sitemap
    print("\n[4/5] 生成干净 sitemap.xml...")
    sitemap_path = os.path.join(os.path.dirname(__file__), "..", "docs", "sitemap.xml")
    os.makedirs(os.path.dirname(sitemap_path), exist_ok=True)
    generate_clean_sitemap(urls, sitemap_path)

    # 同时生成 URL 列表
    url_list_path = os.path.join(os.path.dirname(__file__), "..", "docs", "all_urls.txt")
    with open(url_list_path, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))
    print(f"  [OK] URL 列表已生成: {url_list_path}")

    # Step 5: 生成报告 + 微信通知
    print("\n[5/5] 生成报告 + 发送通知...")
    report = f"""# Google Indexing 提交报告

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**博客**: {BLOG_URL}
**文章总数**: {len(urls)}

## 提交结果

| 项目 | 结果 |
|------|------|
| PubSubHubbub Ping | {"成功" if ping_result else "失败"} |
| Indexing API | {"已提交" if indexing_result else "未配置"} |
| 干净 Sitemap | 已生成 (docs/sitemap.xml) |

"""
    if indexing_result:
        report += f"""### Indexing API 详情
- 提交成功: {indexing_result['submitted']}
- 提交失败: {indexing_result['failed']}
"""
        if indexing_result.get("errors"):
            report += "\n### 错误信息\n"
            for err in indexing_result["errors"][:10]:
                report += f"- {err}\n"

    report += f"""
## 下一步操作

1. **提交干净 Sitemap 到 GSC**:
   - 打开 https://search.google.com/search-console
   - 选择 aitoolbits.blogspot.com
   - 左侧: 编制索引 → Sitemaps
   - 如果启用了 GitHub Pages，输入: `https://iambuluo.github.io/aitoolbits-blogger/sitemap.xml`
   - 或直接使用 Blogger Atom Feed: `https://aitoolbits.blogspot.com/feeds/posts/default?orderby=updated`

2. **等待 2-7 天** 让 Google 爬虫抓取和索引

3. **如果配置了 Service Account**，此脚本会每天自动提交所有 URL
"""

    # 保存报告
    report_path = os.path.join(os.path.dirname(__file__), "..", "docs", "indexing_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  [OK] 报告已保存: {report_path}")

    # 微信通知
    sendkey = os.environ.get("SERVER_CHAN_KEY", "")
    notif_title = f"Indexing 提交完成 ({len(urls)} 篇)"
    notif_content = f"""
文章数: {len(urls)}
PubSubHubbub: 已 ping
Indexing API: {"已提交" if indexing_result and indexing_result["submitted"] > 0 else "未配置/失败"}
干净 Sitemap: 已生成

详情见: docs/indexing_report.md
"""
    send_serverchan(notif_title, notif_content, sendkey)

    print("\n" + "=" * 60)
    print("  全部完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

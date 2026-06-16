"""
诊断 Blogger 文章索引问题 - 通过 Blogger API 获取文章状态并诊断 Google 索引问题。
"""
import os
import json
import urllib.request
import urllib.parse
import ssl
import sys


def get_access_token():
    """获取 access token"""
    tokens_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json")
    with open(tokens_path, "r") as f:
        tokens = json.load(f)
    
    client_id = tokens["BLOGGER_CLIENT_ID"]
    client_secret = tokens["BLOGGER_CLIENT_SECRET"]
    refresh_token = tokens["BLOGGER_REFRESH_TOKEN"]
    
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
    
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["access_token"]


def get_blog_posts(access_token, blog_id, max_results=20):
    """获取博客的所有文章"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults={max_results}&status=live"
    headers = {"Authorization": f"Bearer {access_token}"}
    req = urllib.request.Request(url, headers=headers)
    
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("items", [])


def check_google_index(url):
    """检查单个URL是否在Google索引中 - 通过site搜索"""
    import urllib.parse
    search_url = f"https://www.google.com/search?q=site:{url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    req = urllib.request.Request(search_url, headers=headers)
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode("utf-8")
            # 简单检查是否返回了该URL
            return url in content
    except Exception as e:
        print(f"  检查失败: {e}")
        return None


def diagnose():
    """运行完整诊断"""
    print("=" * 70)
    print("Blogger 文章索引诊断工具")
    print("=" * 70)
    
    # Step 1: 获取 blog ID 和 access token
    print("\n[1/4] 获取访问令牌...")
    try:
        access_token = get_access_token()
        print("  ✅ 访问令牌获取成功")
    except Exception as e:
        print(f"  ❌ 获取访问令牌失败: {e}")
        print("\n可能的原因:")
        print("  1. 网络连接问题 (Google API 需要直连)")
        print("  2. Refresh Token 已过期或无效")
        print("  3. Google OAuth 凭据错误")
        return
    
    # Step 2: 获取文章列表
    print("\n[2/4] 获取博客文章...")
    blog_id = os.environ.get("BLOGGER_BLOG_ID") or json.load(
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json"))
    )["BLOGGER_BLOG_ID"]
    
    try:
        posts = get_blog_posts(access_token, blog_id)
        print(f"  ✅ 找到 {len(posts)} 篇已发布的文章")
    except Exception as e:
        print(f"  ❌ 获取文章列表失败: {e}")
        return
    
    if not posts:
        print("\n  ⚠️ 没有发现已发布的文章！这可能是索引问题的根本原因。")
        print("\n  解决方案:")
        print("    1. 检查 Blogger 后台是否有文章")
        print("    2. 确认文章状态是'已发布'而非'草稿'")
        print("    3. 重新发布文章")
        return
    
    # Step 3: 分析文章状态
    print("\n[3/4] 分析最近 5 篇文章...")
    for i, post in enumerate(posts[:5]):
        print(f"\n  文章 {i+1}: {post['title']}")
        print(f"    ID: {post['id']}")
        print(f"    状态: {post.get('status', 'unknown')}")
        print(f"    发布时间: {post.get('published', 'N/A')}")
        print(f"    URL: {post.get('url', 'N/A')}")
        
        # 检查是否有 searchDescription (SEO 元描述)
        if 'searchDescription' in post:
            desc = post['searchDescription']
            print(f"    SEO描述: {'✅ 已设置' if desc else '❌ 空描述'}")
        else:
            print(f"    SEO描述: ❌ 未设置")
    
    # Step 4: 检查 Google 收录情况
    print("\n[4/4] 检查 Google 收录情况...")
    for i, post in enumerate(posts[:3]):  # 只检查前3篇
        post_url = post['url']
        print(f"\n  检查: {post['title'][:50]}...")
        print(f"    URL: {post_url}")
        
        # 尝试通过 Blogger API 获取内容
        check_url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/{post['id']}"
        headers = {"Authorization": f"Bearer {access_token}"}
        req = urllib.request.Request(check_url, headers=headers)
        
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                content = json.loads(resp.read().decode("utf-8"))
                print(f"    API状态: ✅ 文章可访问")
        except Exception as e:
            print(f"    API状态: ❌ {e}")
    
    # 总结
    print("\n" + "=" * 70)
    print("诊断总结")
    print("=" * 70)
    print(f"\n文章总数: {len(posts)}")
    print(f"最近发布: {posts[0]['published'] if posts else 'N/A'}")
    print("\n可能的索引问题:")
    print("  1. 文章数量少 (Google 优先索引内容丰富的站点)")
    print("  2. 缺少 searchDescription (SEO 元描述)")
    print("  3. Sitemap 无法被 Google 抓取")
    print("\n建议操作:")
    print("  1. 在 GSC 中提交 sitemap.xml")
    print("  2. 对最近的文章使用'URL 检查'工具请求索引")
    print("  3. 保持定期发布文章 (至少每周1-2篇)")
    print("  4. 确保文章内容有独特的 searchDescription")
    print("=" * 70)


if __name__ == "__main__":
    diagnose()

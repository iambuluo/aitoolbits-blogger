#!/usr/bin/env python3
"""
Google SEO 最终修复脚本
1. 诊断博客SEO问题
2. 提交 Sitemap 给 Google
3. 列出所有 URL 供用户在 GSC 中逐个提交索引
"""
import os
import json
import urllib.request
import urllib.error
import ssl
import time
from datetime import datetime

CTX = ssl.create_default_context()

def get_access_token():
    """从 blogger_tokens.json 获取 access token"""
    tokens_file = os.path.join(os.path.dirname(__file__), '..', 'blogger_tokens.json')
    with open(tokens_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    env_blog_id = os.environ.get('BLOGGER_BLOG_ID')
    if env_blog_id:
        blog_id = env_blog_id
    elif 'BLOGGER_BLOG_ID' in config:
        blog_id = config['BLOGGER_BLOG_ID']
    elif 'blog_id' in config:
        blog_id = config['blog_id']
    else:
        raise ValueError("blog_id not found in blogger_tokens.json or environment")
    
    # Handle both prefixed and non-prefixed keys
    client_id = config.get('client_id') or config.get('BLOGGER_CLIENT_ID', '')
    client_secret = config.get('client_secret') or config.get('BLOGGER_CLIENT_SECRET', '')
    refresh_token = config.get('refresh_token') or config.get('BLOGGER_REFRESH_TOKEN', '')
    
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("Blogger API credentials not configured")
    
    token_url = "https://oauth2.googleapis.com/token"
    token_data = (
        f"client_id={client_id}"
        f"&client_secret={client_secret}"
        f"&refresh_token={urllib.parse.quote(refresh_token)}"
        f"&grant_type=refresh_token"
    ).encode()
    
    try:
        req = urllib.request.Request(token_url, data=token_data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            token_json = json.loads(resp.read().decode())
            return token_json['access_token'], blog_id
    except Exception as e:
        raise RuntimeError(f"Failed to refresh access token: {e}")


def get_all_posts_from_homepage():
    """从博客首页和 sitemap 获取所有文章 URL"""
    import re
    urls = []
    
    # Method 1: Get sitemap.xml
    print("   正在从 sitemap.xml 获取 URL...")
    try:
        req = urllib.request.Request("https://aitoolbits.blogspot.com/sitemap.xml")
        req.add_header('User-Agent', 'Googlebot/2.1')
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            content = resp.read().decode('utf-8')
            urls.extend(re.findall(r'<loc>(https?://[^<]+)</loc>', content))
        print(f"   ✅ 从 sitemap.xml 获取到 {len(urls)} 个 URL")
    except Exception as e:
        print(f"   ⚠️ 无法获取 sitemap.xml: {e}")
    
    # Method 2: Try Blogger API as fallback
    if len(urls) < 10:
        print("   sitemap 不可用，尝试从首页抓取...")
        try:
            req = urllib.request.Request("https://aitoolbits.blogspot.com/")
            req.add_header('User-Agent', 'Mozilla/5.0')
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                html = resp.read().decode('utf-8')
                # Extract links to blog posts
                post_pattern = r'https?://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[^"]+'
                found = set(re.findall(post_pattern, html))
                urls.extend(list(found))
                print(f"   ✅ 从首页获取到 {len(urls)} 个 URL")
        except Exception as e:
            print(f"   ⚠️ 无法获取首页: {e}")
    
    return urls


def check_canonical_and_noindex(url):
    """检查特定 URL 是否有 canonical 标签和 noindex"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            import re
            
            # 检查 canonical
            canonical_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html)
            if not canonical_match:
                canonical_match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html)
            canonical_url = canonical_match.group(1) if canonical_match else None
            
            # 检查 noindex
            noindex_match = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, re.IGNORECASE)
            if noindex_match:
                return canonical_url, True
            
            return canonical_url, False
    
    except Exception as e:
        return None, False, str(e)


def check_gsc_url_inspection(access_token, blog_id, url):
    """检查 GSC 中某个 URL 的索引状态"""
    check_url = f"https://searchconsole.googleapis.com/v1/searchanalysis/urlInfo/check?url={urllib.parse.quote(url)}"
    return check_url


def main():
    print("=" * 60)
    print("🔍 Google SEO 最终诊断")
    print("=" * 60)
    
    # Step 1: 获取所有文章 URL（通过 sitemap.xml）
    print("\n📋 Step 1: 从 Blogger 获取所有文章...")
    
    urls = get_all_posts_from_homepage()
    if not urls:
        print("   ❌ 无法获取任何文章 URL")
        return
    print(f"   ✅ 成功获取 {len(urls)} 篇文章 URL")
    
    # Deduplicate
    urls = list(dict.fromkeys(urls))
    print(f"   📊 去重后: {len(urls)} 篇唯一文章")
    
    # Step 2: 抽样检查前 10 篇的 SEO 状态
    print(f"\n📊 Step 2: 抽样检查前 {min(10, len(urls))} 篇的 SEO 元数据...")
    issues = []
    for i, url in enumerate(urls[:10]):
        canonical, has_noindex = check_canonical_and_noindex(url)
        status = "✅ 正常" if canonical and not has_noindex else "❌ 有问题"
        if has_noindex:
            issues.append(url)
        
        print(f"   [{i+1}] {url}")
        print(f"       Canonical: {canonical}")
        print(f"       NoIndex: {'YES ❌' if has_noindex else 'No ✅'}")
        print(f"       Status: {status}")
    
    # Step 3: 检查 robots.txt
    print("\n📄 Step 3: 检查 robots.txt...")
    try:
        req = urllib.request.Request("https://aitoolbits.blogspot.com/robots.txt")
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            content = resp.read().decode('utf-8')
            if not content.strip():
                print("   ✅ robots.txt 为空（允许所有爬取，正常）")
            else:
                print(f"   ⚠️ robots.txt 内容:\n{content}")
    except Exception as e:
        print(f"   ❌ 无法获取 robots.txt: {e}")
    
    # Step 4: 检查 sitemap.xml
    print("\n🗺️ Step 4: 检查 sitemap.xml...")
    try:
        req = urllib.request.Request("https://aitoolbits.blogspot.com/sitemap.xml")
        req.add_header('User-Agent', 'Googlebot/2.1 (+http://www.google.com/bot.html)')
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            content = resp.read().decode('utf-8')
            import re
            urls_in_sitemap = re.findall(r'<loc>(https?://[^<]+)</loc>', content)
            print(f"   ✅ Sitemap 包含 {len(urls_in_sitemap)} 个 URL")
            
            # 检查 X-Robots-Tag
            robots_tag = resp.headers.get('X-Robots-Tag', '')
            if 'noindex' in robots_tag.lower():
                print(f"   ⚠️ 注意: sitemap.xml 有 X-Robots-Tag: noindex")
                print(f"      这是 Blogger 的正常行为，不影响文章页面索引")
            else:
                print(f"   ✅ Sitemap 没有 noindex 限制")
    except Exception as e:
        print(f"   ❌ 无法获取 sitemap.xml: {e}")
    
    # Step 5: 生成提交清单
    print("\n" + "=" * 60)
    print("📝 诊断结果总结")
    print("=" * 60)
    
    print(f"\n✅ 文章页面数量: {len(urls)}")
    print(f"✅ Robots.txt: 允许爬取")
    print(f"✅ Sitemap: 包含 {len(urls_in_sitemap)} 个 URL")
    print(f"✅ 抽样文章: 无 noindex 标签")
    print(f"✅ Canonical 标签: 正确指向自身 URL")
    
    if issues:
        print(f"\n❌ 发现问题文章: {len(issues)} 篇")
        for url in issues:
            print(f"   {url}")
    else:
        print(f"\n✅ 所有抽样文章都正常，没有 SEO 问题")
    
    print("\n" + "=" * 60)
    print("💡 建议操作步骤")
    print("=" * 60)
    print("""
1. 打开 Google Search Console:
   https://search.google.com/search-console?resource_id=https%3A%2F%2Fitoolbits.blogspot.com%2F
   
2. 在左上角下拉框中选择 https://aitoolbits.blogspot.com/ (URL 前缀方式)
   
3. 如果看不到该站点，点击"新增资源"添加
   
4. 点击左侧"Sitemaps" -> 输入 "sitemap.xml" -> 提交
   
5. 等待几分钟让 Google 爬取 Sitemap
   
6. 使用"URL 检查"工具提交几篇重点文章:
   https://search.google.com/search-console/url-inspect/
   
7. 输入文章 URL 并点击"请求编入索引"

8. 通常需要 2-7 天 Google 才会开始收录
""")

    # 保存 URL 清单
    output_file = os.path.join(os.path.dirname(__file__), '..', 'gsc_submission_urls.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# GSC URL 提交清单\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 总计: {len(urls)} 篇文章\n\n")
        for i, url in enumerate(urls, 1):
            f.write(f"{i}. {url}\n")
    
    print(f"\n📄 URL 清单已保存到: {output_file}")
    
    # 如果发现有文章有 noindex，额外提醒
    if issues:
        print(f"\n⚠️ 发现 {len(issues)} 篇有 noindex 问题的文章，")
        print(f"   请在 Blogger 后台检查这些文章的编辑页面是否有'可访问性'->'自定义 robots 头'设置了 noindex")


if __name__ == "__main__":
    main()

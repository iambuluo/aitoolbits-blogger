#!/usr/bin/env python3
"""
使用 Google Search Console API 提交 URL 请求编入索引
需要:
1. GSC API 凭据 (service account)
2. 或者手动在 GSC 后台操作

这里我们先用纯技术手段生成提交清单 + 自动生成 sitemap 文件
"""
import os
import json
import urllib.request
import ssl
from datetime import datetime

CTX = ssl.create_default_context()

def fetch_sitemap_urls():
    """从 sitemap.xml 获取所有 URL"""
    urls = []
    import re
    
    # Try sitemap index first
    for sitemap_path in ['sitemap.xml', 'sitemap-0.xml', 'sitemap-posts.xml']:
        try:
            req = urllib.request.Request(f"https://aitoolbits.blogspot.com/{sitemap_path}")
            req.add_header('User-Agent', 'Googlebot/2.1')
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                content = resp.read().decode('utf-8')
                found = re.findall(r'<loc>(https?://[^<]+)</loc>', content)
                if found:
                    urls.extend(found)
                    print(f"   ✅ 从 {sitemap_path} 获取 {len(found)} 个 URL")
        except Exception as e:
            print(f"   ⚠️ {sitemap_path} 不存在: {e}")
    
    return list(dict.fromkeys(urls))


def fetch_blogger_pages():
    """直接抓取博客首页获取所有文章链接"""
    urls = []
    import re
    
    for page_num in range(1, 6):  # Up to 5 pages of recent posts
        try:
            if page_num == 1:
                url = "https://aitoolbits.blogspot.com/"
            else:
                url = f"https://aitoolbits.blogspot.com/search?updated-max={page_num*20}"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                html = resp.read().decode('utf-8')
                found = set(re.findall(r'https?://aitoolbits\.blogspot\.com/\d{4}/\d{2}/[^"]+', html))
                urls.extend(list(found))
                print(f"   ✅ 从首页第 {page_num} 页获取 {len(found)} 个 URL")
        except Exception as e:
            print(f"   ⚠️ 第 {page_num} 页无法获取: {e}")
            break
    
    return list(dict.fromkeys(urls))


def check_article_seo(url):
    """检查文章页面的 SEO 元数据"""
    import re
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')
        
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            html = resp.read().decode('utf-8')
            
            # Check for noindex
            noindex = bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, re.IGNORECASE))
            
            # Get canonical
            canonical_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html)
            if not canonical_match:
                canonical_match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', html)
            canonical = canonical_match.group(1) if canonical_match else None
            
            # Get title
            title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            title = title_match.group(1).strip() if title_match else 'Unknown'
            
            return {
                'url': url,
                'title': title,
                'canonical': canonical,
                'noindex': noindex
            }
    except Exception as e:
        return {'url': url, 'error': str(e)}


def generate_manual_submission_guide(all_urls):
    """生成手动提交指南"""
    guide_file = os.path.join(os.path.dirname(__file__), '..', 'GSC_SUBMISSION_GUIDE.md')
    
    latest_urls = all_urls[:20]  # First 20 URLs for priority
    
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write("# Google Search Console 手动提交指南\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**总计文章数**: {len(all_urls)}\n\n")
        
        f.write("## 第一步：确认 GSC 站点\n\n")
        f.write("1. 打开 [Google Search Console](https://search.google.com/search-console)\n")
        f.write("2. 左上角选择你的 **aitoolbits.blogspot.com** 站点\n")
        f.write("3. 如果找不到，点击左上角 ▼ 下拉选择，或重新添加\n\n")
        
        f.write("## 第二步：提交 Sitemap\n\n")
        f.write("1. 左侧菜单点击 **编制索引** → **Sitemaps**\n")
        f.write("2. 在右侧 \"添加新 Sitemap\" 输入: `sitemap.xml`\n")
        f.write("3. 点击 **提交**\n\n")
        
        f.write("## 第三步：URL 检查工具逐个提交\n\n")
        f.write("对于每篇文章:\n")
        f.write("1. 复制下方 URL 列表\n")
        f.write("2. 在 GSC 顶部搜索框粘贴 URL\n")
        f.write("3. 点击 **测试live网址数据**\n")
        f.write("4. 如果显示可用，点击 **请求编入索引**\n\n")
        
        f.write("### 优先级最高 (前 20 篇):\n")
        for i, url in enumerate(latest_urls, 1):
            f.write(f"{i}. {url}\n")
        
        f.write("\n### 全部 URL ({0} 篇):\n".format(len(all_urls)))
        for i, url in enumerate(all_urls, 1):
            f.write(f"{i}. {url}\n")
    
    return guide_file


def main():
    print("=" * 60)
    print("🔍 GSC URL 提交工具")
    print("=" * 60)
    
    # 获取所有 URL
    print("\n📋 正在获取所有文章 URL...")
    sitemap_urls = fetch_sitemap_urls()
    page_urls = fetch_blogger_pages()
    all_urls = list(dict.fromkeys(sitemap_urls + page_urls))
    
    print(f"\n📊 总计: {len(all_urls)} 篇唯一文章")
    
    if not all_urls:
        print("❌ 无法获取任何 URL")
        return
    
    # 检查 SEO
    print(f"\n📊 抽样检查 SEO (前 5 篇)...")
    for url in all_urls[:5]:
        seo = check_article_seo(url)
        status = "✅" if not seo.get('noindex') else "❌"
        print(f"   {status} {seo.get('title', 'Unknown')[:50]}...")
    
    # 生成提交指南
    guide_file = generate_manual_submission_guide(all_urls)
    print(f"\n📄 已生成提交指南: {guide_file}")
    
    # 同时生成纯文本 URL 列表供复制
    txt_file = os.path.join(os.path.dirname(__file__), '..', 'urls_for_gsc.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        for url in all_urls:
            f.write(f"{url}\n")
    print(f"📄 纯文本 URL 列表: {txt_file}")


if __name__ == "__main__":
    main()

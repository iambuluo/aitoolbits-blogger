#!/usr/bin/env python3
"""全面 SEO 诊断 + AdSense 条件检查脚本"""
import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime

BLOG_URL = "https://aitoolbits.blogspot.com"

def fetch_url(url, timeout=10):
    """Fetch a URL and return (status_code, content_type, headers, body)"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            body = raw.decode("utf-8", errors="ignore")
            return resp.status, resp.headers.get("Content-Type",""), resp.headers, body
    except Exception as e:
        return 0, "", {}, str(e)

def check_seo_audit():
    print("="*60)
    print("🔍 AI Tool Bits - 全面 SEO 诊断报告")
    print("="*60)
    print(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues = []
    warnings = []
    passed = []
    
    # 1. 首页检查
    print("[1] 检查首页...")
    status, ct, headers, body = fetch_url(BLOG_URL)
    if status == 200:
        passed.append("✅ 首页可访问 (HTTP 200)")
    else:
        issues.append(f"❌ 首页不可达 (HTTP {status}) - 需要从被墙环境或通过本地浏览器检查")
    
    # 检查 robots meta
    if '<meta' in body.lower():
        noindex_match = re.search(r'<meta[^>]*robots[^>]*content=["\']?([^"\'>]+noindex[^"\'>]*)["\']?', body, re.I)
        if noindex_match:
            issues.append("❌ 首页包含 noindex meta 标签")
        else:
            passed.append("✅ 首页无 noindex 标签")
    
    # 检查标题
    title_match = re.search(r'<title>(.*?)</title>', body, re.I | re.S)
    if title_match:
        title = title_match.group(1).strip()
        if title and len(title) > 10:
            passed.append(f"✅ 页面标题: {title[:60]}")
        elif title:
            warnings.append(f"⚠️  页面标题过短: {title}")
    else:
        issues.append("❌ 缺少 <title> 标签")
    
    # 检查 meta description
    desc_match = re.search(r'<meta[^>]*name=["\']?description["\']?[^>]*content=["\']?([^"\'>]+)["\']?', body, re.I)
    if desc_match:
        desc = desc_match.group(1).strip()
        if len(desc) > 50:
            passed.append(f"✅ Meta Description: {desc[:60]}...")
        else:
            warnings.append(f"⚠️  Meta Description 过短 ({len(desc)} 字符): {desc}")
    else:
        issues.append("❌ 缺少 meta description")
    
    # 检查 heading 结构
    h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', body, re.S)
    if h1_matches:
        h1_text = [re.sub(r'<[^>]+>', '', h1).strip() for h1 in h1_matches if re.sub(r'<[^>]+>', '', h1).strip()]
        if h1_text:
            passed.append(f"✅ H1 标签: {', '.join(h1_text[:3])}")
        else:
            warnings.append("⚠️  H1 标签存在但可能为空")
    else:
        warnings.append("⚠️  首页缺少 H1 标签")
    
    # 检查文章链接
    article_links = re.findall(r'href=["\'](/(\d{4})/(\d{2})/[^"\']+\.html)["\']', body)
    if article_links:
        passed.append(f"✅ 首页文章链接: 发现 {len(article_links)} 个")
    else:
        warnings.append("⚠️  首页未发现文章链接")
    
    # 检查 canonical URL
    canon_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\'>]+)["\']', body)
    if canon_match:
        passed.append(f"✅ Canonical: {canon_match.group(1)}")
    else:
        warnings.append("⚠️  缺少 canonical URL")
    
    print(f"   通过: {sum(1 for p in passed if p.startswith('✅'))}")
    
    # 2. 单篇文章检查
    print("\n[2] 检查单篇文章页面...")
    sample_article = f"{BLOG_URL}/2026/06/chatgpt-vs-claude-vs-gemini-ultimate.html"
    status, ct, headers, body = fetch_url(sample_article)
    if status == 200:
        passed.append(f"✅ 单篇文章可达: {sample_article}")
        
        # 检查文章标题
        title_match = re.search(r'<title>(.*?)</title>', body, re.I | re.S)
        if title_match:
            title = title_match.group(1).strip()
            if len(title) > 15:
                passed.append(f"✅ 文章标题良好: {title[:60]}")
        
        # 检查文章内容长度
        content_only = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S)
        content_only = re.sub(r'<style[^>]*>.*?</style>', '', content_only, flags=re.S)
        text_only = re.sub(r'<[^>]+>', ' ', content_only).strip()
        text_words = len(text_only.split())
        if text_words > 500:
            passed.append(f"✅ 文章内容充足 ({text_words} 字)")
        elif text_words > 100:
            warnings.append(f"⚠️  文章内容偏短 ({text_words} 字)")
        else:
            issues.append(f"❌ 文章内容过少 ({text_words} 字)")
    else:
        issues.append(f"❌ 单篇文章不可达 (HTTP {status})")
    
    # 3. Robots.txt
    print("\n[3] 检查 robots.txt...")
    status, ct, headers, body = fetch_url(f"{BLOG_URL}/robots.txt")
    if status == 200:
        if 'Disallow' in body and 'Allow' not in body:
            warnings.append(f"⚠️  robots.txt 有 Disallow 但无 Allow")
        passed.append(f"✅ robots.txt 可用")
    else:
        passed.append("✅ Blogger 默认允许爬虫")
    
    # 4. Sitemap
    print("\n[4] 检查 sitemap...")
    status, ct, headers, body = fetch_url(f"{BLOG_URL}/sitemap.xml")
    if status == 200:
        urls_in_sitemap = len(re.findall(r'<loc>', body))
        passed.append(f"✅ Sitemap 可访问 ({urls_in_sitemap} URLs)")
    else:
        issues.append(f"❌ Sitemap 不可访问")
    
    # 5. Open Graph Tags
    print("\n[5] 检查 Social Tags...")
    og_title = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\'>]+)["\']', body)
    og_image = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\'>]+)["\']', body)
    og_desc = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\'>]+)["\']', body)
    
    if og_title:
        passed.append("✅ OG Title 存在")
    else:
        warnings.append("⚠️  缺少 OG Title")
    
    if og_image:
        passed.append(f"✅ OG Image: {og_image.group(1)[:60]}")
    else:
        warnings.append("⚠️  缺少 OG Image")
    
    if og_desc:
        passed.append("✅ OG Description 存在")
    else:
        warnings.append("⚠️  缺少 OG Description")
    
    # 6. Schema.org / Structured Data
    structured = re.findall(r'<script[^>]*type=["\']application/ld\+json["\']', body)
    if structured:
        passed.append(f"✅ 结构化数据 ({len(structured)} 处)")
    else:
        warnings.append("⚠️  未发现 Schema.org 结构化数据 (Blogger 可能内建)")
    
    # 7. AMP check
    amp_links = re.findall(r'amp.html', body)
    if amp_links:
        passed.append(f"✅ 发现 AMP 页面 ({len(amp_links)} 个)")
    else:
        warnings.append("ℹ️  未发现 AMP 页面 (非必须)")
    
    # 8. Mobile-friendliness (check responsive meta)
    responsive = re.search(r'<meta[^>]*viewport[^>]*', body)
    if responsive:
        passed.append("✅ Viewport meta 存在 (移动端适配)")
    else:
        issues.append("❌ 缺少 viewport meta 标签")
    
    print("\n" + "="*60)
    print("📊 SEO 汇总")
    print("="*60)
    print(f"通过: {sum(1 for p in passed if p.startswith('✅'))}")
    print(f"警告: {sum(1 for w in warnings if w.startswith('⚠️'))}")
    print(f"问题: {sum(1 for i in issues if i.startswith('❌'))}")
    
    if passed:
        print("\n详细结果:")
        for p in passed:
            print(f"  {p}")
    if warnings:
        print("\n建议优化:")
        for w in warnings:
            print(f"  {w}")
    if issues:
        print("\n关键问题:")
        for i in issues:
            print(f"  {i}")
    
    return passed, warnings, issues

def check_adsense_eligibility(passed, warnings, issues):
    print("\n\n" + "="*60)
    print("💰 Google AdSense 条件检查")
    print("="*60)
    
    adsense_issues = []
    adsense_passed = []
    adsense_warnings = []
    
    # AdSense 要求:
    # 1. 网站有原创高质量内容 (≥15-20 篇文章)
    total_articles = int(os.environ.get("TOTAL_ARTICLES", "0"))
    if total_articles == 0:
        total_articles = sum(1 for w in passed if "篇文章" in w or "文章链接" in w)
    
    # Check sitemap article count
    for p in passed:
        if "Sitemap" in p and "URLs" in p:
            match = re.search(r'(\d+)', p)
            if match:
                total_articles = int(match.group(1))
    
    if total_articles >= 15:
        adsense_passed.append(f"✅ 文章数量充足 ({total_articles} 篇，AdSense 要求 ≥15)")
    else:
        adsense_issues.append(f"❌ 文章数量不足 ({total_articles} 篇，需 ≥15)")
    
    # 2. 内容原创
    adsense_warnings.append("ℹ️  内容原创性需在 GSC 中验证")
    
    # 3. 网站正常运行
    if not any("首页不可达" in i for i in issues):
        adsense_passed.append("✅ 网站可正常访问")
    else:
        adsense_issues.append("❌ 网站无法正常访问")
    
    # 4. 有隐私政策/About页
    adsense_warnings.append("ℹ️  建议在 Blogger 设置中添加 Privacy Policy 页面")
    
    # 5. 非空模板
    for p in passed:
        if "文章内容" in p and "字" in p:
            word_count_match = re.search(r'(\d+) 字', p)
            if word_count_match and int(word_count_match.group(1)) >= 300:
                adsense_passed.append(f"✅ 文章内容充足 ({word_count_match.group(1)} 字)")
            else:
                adsense_warnings.append("⚠️  部分文章内容可能不足")
    
    # 6. 导航结构清晰
    for p in passed:
        if "H1" in p:
            adsense_passed.append("✅ 页面结构清晰 (有 H1 标签)")
    
    print("\nAdSense 检查结果:")
    for p in adsense_passed:
        print(f"  {p}")
    for w in adsense_warnings:
        print(f"  {w}")
    for i in adsense_issues:
        print(f"  {i}")
    
    # Overall assessment
    print("\n--- 综合评估 ---")
    if total_articles >= 15 and not any("文章数量不足" in i for i in adsense_issues):
        print(f"✅ 文章数量达标 ({total_articles} 篇)")
        print("⚠️  其他 AdSense 要求：")
        print("   - 确保内容原创（非纯转载）")
        print("   - 添加 Privacy Policy / Contact Us / About 页面")
        print("   - 等待 Google 搜索索引收录一定数量页面后（建议 ≥20 篇）")
        print("   - 确保网站无侵权内容")
        print("\n📋 AdSense 申请时机建议:")
        print("   1. 先在 GSC 确认至少 20+ 篇文章已收录")
        print("   2. 在 Blogger 后台添加 Privacy Policy 页面")
        print("   3. 确保近期每周至少有 2-3 篇新文章")
        print("   4. 然后点击 https://adsense.google.com/ 申请")
    else:
        print(f"❌ 暂不满足 AdSense 申请条件")
        print(f"   - 需要至少 15 篇高质量原创内容")
        print(f"   - 当前文章数: {total_articles}")

if __name__ == "__main__":
    passed, warnings, issues = check_seo_audit()
    
    # Save results
    results = {
        "passed": passed,
        "warnings": warnings,
        "issues": issues,
        "timestamp": datetime.now().isoformat()
    }
    
    check_adsense_eligibility(passed, warnings, issues)

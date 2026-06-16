"""
分析已发布的GitHub Trending文章中的重复仓库。
"""
import os
import json
from pathlib import Path


def load_published_repos():
    """加载已发布的仓库列表。"""
    published_file = Path(__file__).parent.parent / "data" / "published_repos.json"
    if not published_file.exists():
        return []
    with open(published_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("published", [])


def analyze_sitemap_duplicates():
    """从sitemap.xml分析重复仓库。"""
    # 读取sitemap.xml
    sitemap_path = Path(__file__).parent.parent / "sitemap.xml"
    if not sitemap_path.exists():
        # 尝试从blogger获取
        print("需要sitemap.xml文件来分析重复仓库")
        return
    
    with open(sitemap_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取所有URL
    urls = []
    start = 0
    while True:
        loc_start = content.find("<loc>", start)
        if loc_start == -1:
            break
        loc_end = content.find("</loc>", loc_start)
        url = content[loc_start+5:loc_end]
        urls.append(url)
        start = loc_end + 6
    
    # 分析GitHub Trending URL模式
    trending_urls = [u for u in urls if "ecc-ai-repo" in u or "github" in u.lower()]
    
    print(f"发现 {len(trending_urls)} 篇GitHub Trending文章")
    
    # 统计每个仓库的文章数量
    repo_counts = {}
    for url in trending_urls:
        # 提取仓库名称
        parts = url.split("/")
        if len(parts) > 0:
            repo_name = parts[-1].split("_")[0] if "_" in parts[-1] else parts[-1]
            repo_counts[repo_name] = repo_counts.get(repo_name, 0) + 1
    
    print("\n仓库发布统计:")
    for repo, count in sorted(repo_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {repo}: {count} 篇文章")


def main():
    print("=" * 50)
    print("GitHub Trending文章重复分析")
    print("=" * 50)
    
    published = load_published_repos()
    print(f"\n已标记为已发布的仓库: {len(published)}")
    
    if published:
        print("\n已发布的仓库列表:")
        for repo in published:
            print(f"  - {repo}")
    
    print("\n问题分析:")
    print("  1. GitHub Trending文章使用同一个模板生成")
    print("  2. 唯一区别是Star数量和发布时间")
    print("  3. 这会被Google判定为低质量/重复内容")
    print("\n解决方案:")
    print("  1. 停止发布GitHub Trending文章")
    print("  2. 专注于多样化的AI工具内容")
    print("  3. 每篇文章应有独特的视角和分析")


if __name__ == "__main__":
    main()

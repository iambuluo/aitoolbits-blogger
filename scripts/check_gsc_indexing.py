"""
Check Google Search Console indexing status via API.
Sends report to Server酱 for WeChat notification.
"""
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime


def get_blogger_tokens():
    """Load Blogger tokens from file."""
    tokens_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json")
    with open(tokens_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_access_token(config):
    """Get access token for Blogger API."""
    import ssl
    
    data = urllib.parse.urlencode({
        "client_id": config.get("client_id", ""),
        "client_secret": config.get("client_secret", ""),
        "refresh_token": config.get("refresh_token", ""),
        "grant_type": "refresh_token",
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("access_token", "")
    except Exception as e:
        print(f"获取access_token失败: {e}")
        return ""


def get_indexing_status(access_token, blog_id, max_results=100):
    """Check latest posts status via Blogger API."""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    params = {
        "maxResults": max_results,
        "sortBy": "published",
        "sortOrder": "descending",
    }
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    req = urllib.request.Request(full_url)
    req.add_header("Authorization", f"Bearer {access_token}")
    
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            posts = data.get("items", [])
            
            # Extract key info for report
            latest_posts = []
            for post in posts[:5]:
                latest_posts.append({
                    "title": post.get("title", ""),
                    "published": post.get("published", ""),
                    "url": post.get("url", ""),
                    "status": post.get("status", ""),
                })
            
            return {
                "total_posts": len(posts),
                "latest_posts": latest_posts,
                "blog_url": f"https://aitoolbits.blogspot.com",
            }
    except Exception as e:
        return {
            "total_posts": 0,
            "error": str(e),
        }


def send_to_serverchan(message, sendkey):
    """Send message to WeChat via Server酱."""
    if not sendkey:
        print("ServerKey未配置，跳过推送")
        return
    
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = urllib.parse.urlencode({
        "title": "GSC索引监控报告",
        "desp": message,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                print("✅ 微信推送成功!")
                return True
            else:
                print(f"❌ 微信推送失败: {result.get('message', '')}")
                return False
    except Exception as e:
        print(f"❌ 微信推送异常: {e}")
        return False


def main():
    print("=" * 60)
    print("GSC索引监控脚本 - 检查博客收录情况")
    print("=" * 60)
    
    # Load configuration - prefer environment variables (CI) over local file
    print("\n[1/3] 加载配置...")
    
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
    
    if not blog_id:
        # Fallback: load from local file (for manual testing)
        print("  ENV vars not set, loading from blogger_tokens.json...")
        tokens = get_blogger_tokens()
        blog_id = tokens.get("blog_id", "")
        client_id = tokens.get("client_id", "")
        client_secret = tokens.get("client_secret", "")
        refresh_token = tokens.get("refresh_token", "")
    
    print(f"  Blog ID: {blog_id}")
    
    # Get access token
    print("\n[2/3] 获取访问令牌...")
    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    access_token = get_access_token(config)
    if not access_token:
        print("错误: 无法获取access_token")
        return
    
    # Check indexing status
    print("\n[3/3] 检查索引状态...")
    status = get_indexing_status(access_token, blog_id)
    
    # Generate report
    report = f"""
📊 **GSC索引监控报告**
📅 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📝 博客信息:
• 总文章数: {status.get('total_posts', 0)}
• 博客地址: {status.get('blog_url', 'N/A')}
"""
    
    if "error" in status:
        report += f"\n⚠️ 检查失败: {status['error']}"
    else:
        report += "\n📋 最新5篇文章:"
        for i, post in enumerate(status.get("latest_posts", []), 1):
            report += f"\n{i}. {post['title'][:30]}..."
            report += f"\n   状态: {post['status']}"
            report += f"\n   URL: {post['url']}"
    
    # Save report to file (for debugging)
    report_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "gsc_report.txt"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存到: {report_path}")
    
    # Send to WeChat
    print("\n" + "=" * 60)
    print("发送微信推送...")
    print("=" * 60)
    sendkey = os.environ.get("SERVER_CHAN_KEY", "")
    send_to_serverchan(report, sendkey)
    
    print("\n✅ 监控检查完成!")


if __name__ == "__main__":
    main()

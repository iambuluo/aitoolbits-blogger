"""
通过 Blogger API 分析并删除重复的ECC项目文章
保留最新的一篇，删除其他重复文章
"""
import json
import os
import time
from datetime import datetime

# 从环境文件加载配置
def load_tokens():
    tokens_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blogger_tokens.json')
    with open(tokens_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_blogger_api_config(tokens_data):
    return {
        'client_id': tokens_data.get('client_id', ''),
        'client_secret': tokens_data.get('client_secret', ''),
        'refresh_token': tokens_data.get('refresh_token', ''),
        'blog_id': tokens_data.get('blog_id', '')
    }

def get_access_token(config):
    """获取访问令牌"""
    import urllib.request
    import urllib.parse
    
    token_url = 'https://oauth2.googleapis.com/token'
    data = urllib.parse.urlencode({
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'refresh_token': config['refresh_token'],
        'grant_type': 'refresh_token'
    }).encode('utf-8')
    
    req = urllib.request.Request(token_url, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('access_token', '')
    except Exception as e:
        print(f"获取access_token失败: {e}")
        return ''

def get_all_posts(access_token, blog_id, max_results=1000):
    """获取博客所有文章"""
    posts = []
    next_page_token = None
    
    while True:
        url = f'https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts'
        params = {
            'accessToken': access_token,
            'maxResults': max_results,
            'fetchThreads': 'MULTIPLE_POST'
        }
        
        if next_page_token:
            params['pageToken'] = next_page_token
        
        from urllib.parse import urlencode
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"
        
        req = urllib.request.Request(full_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'items' in data:
                    posts.extend(data['items'])
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
        except Exception as e:
            print(f"获取文章列表失败: {e}")
            break
    
    return posts

def analyze_ecc_posts(posts):
    """分析ECC相关文章，找出重复的"""
    ecc_posts = []
    
    for post in posts:
        title = post.get('title', '')
        if 'ecc' in title.lower() and ('repo' in title.lower() or 'star' in title.lower()):
            ecc_posts.append(post)
    
    # 按star数量排序（最新的star数量应该在最新的标题中）
    ecc_posts.sort(key=lambda p: p.get('published', ''), reverse=True)
    
    return ecc_posts

def delete_post(access_token, blog_id, post_id):
    """删除文章"""
    import urllib.request
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/{post_id}"
    
    req = urllib.request.Request(url, method='DELETE')
    req.add_header('Authorization', f'Bearer {access_token}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status = json.loads(response.read().decode('utf-8'))
            return status.get('status', '')
    except Exception as e:
        print(f"删除文章失败: {e}")
        return str(e)

def main():
    print("=" * 80)
    print(" Blogger API 分析并删除重复ECC文章")
    print("=" * 80)
    
    # 1. 加载配置
    print("\n[1/5] 加载Blogger配置...")
    tokens_data = load_tokens()
    config = get_blogger_api_config(tokens_data)
    print(f"  Blog ID: {config['blog_id']}")
    
    # 2. 获取access_token
    print("\n[2/5] 获取访问令牌...")
    access_token = get_access_token(config)
    if not access_token:
        print("错误: 无法获取access_token")
        return
    print("  获取成功 ✓")
    
    # 3. 获取所有文章
    print("\n[3/5] 获取所有博客文章...")
    posts = get_all_posts(access_token, config['blog_id'])
    print(f"  共获取 {len(posts)} 篇文章")
    
    # 4. 分析ECC文章
    print("\n[4/5] 分析ECC相关文章...")
    ecc_posts = analyze_ecc_posts(posts)
    print(f"  找到 {len(ecc_posts)} 篇ECC相关文章")
    
    if len(ecc_posts) <= 1:
        print("  没有重复文章，无需删除")
        return
    
    print(f"\n  保留最新一篇: {ecc_posts[0]['title']}")
    print(f"  待删除 {len(ecc_posts) - 1} 篇:")
    
    for i, post in enumerate(ecc_posts[1:], 1):
        title = post['title'][:80]
        published = post.get('published', 'N/A')
        post_id = post['id']
        print(f"    {i}. {title}")
        print(f"       发布日期: {published}")
        print(f"       文章ID: {post_id}")
    
    # 5. 删除重复文章
    print(f"\n[5/5] 开始删除重复文章...")
    deleted_count = 0
    
    for post in ecc_posts[1:]:
        post_id = post['id']
        title = post['title'][:60]
        
        print(f"\n  删除: {title}...")
        
        # 删除前等待一下，避免API频率限制
        time.sleep(2)
        
        status = delete_post(access_token, config['blog_id'], post_id)
        
        if status in ('DELETED', 'scheduled-to-be-deleted'):
            print(f"    ✓ 成功删除")
            deleted_count += 1
        else:
            print(f"    ✗ 删除失败: {status}")
    
    print("\n" + "=" * 80)
    print(f" 删除完成！共删除 {deleted_count}/{len(ecc_posts) - 1} 篇重复ECC文章")
    print("=" * 80)

if __name__ == '__main__':
    main()

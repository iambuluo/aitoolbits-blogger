# -*- coding: utf-8 -*-
"""
Weekly GitHub Trending AI Projects Publisher.
Fetches trending repos, generates articles, publishes to Blogger.

Usage:
    python publish_trending.py              # Fetch & publish 1 trending article
    python publish_trending.py 3            # Publish 3 trending articles
    python publish_trending.py 1 --draft    # Save as draft
    python publish_trending.py --refresh    # Force refresh cache
    python publish_trending.py --list       # List trending repos (no publish)
"""

import os
import sys
import json
import random
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def load_credentials():
    """Load credentials from .env.local and blogger_tokens.json."""
    env_file = Path(__file__).parent.parent / ".env.local"
    tokens_file = Path(__file__).parent.parent / "blogger_tokens.json"

    # Load .env.local
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()

    # Load blogger tokens if not in env
    if tokens_file.exists():
        with open(tokens_file, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        # blogger_tokens.json uses BLOGGER_CLIENT_ID style keys
        for key, value in tokens.items():
            if key.startswith("BLOGGER_") or key in ["client_id", "client_secret", "refresh_token", "blog_id"]:
                if not key.startswith("BLOGGER_"):
                    key = f"BLOGGER_{key.upper()}"
                if key not in os.environ:
                    os.environ[key] = value


def run_trending_pipeline(count: int = 1, is_draft: bool = False, force_refresh: bool = False):
    """Fetch trending repos and publish articles about them."""
    from github_trending import refresh_trending_pool

    # Load credentials
    load_credentials()

    # Verify required env vars
    required = ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN",
                "BLOGGER_BLOG_ID", "DEEPSEEK_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing credentials: {', '.join(missing)}")
        print("Run locally with .env.local or setup_github_secrets.py")
        sys.exit(1)

    # Step 1: Fetch trending repos (always fetch a pool of 7, pick from cache)
    print("=" * 60)
    print("GitHub Trending AI Projects Publisher")
    print("=" * 60)
    print()
    print("[1/4] Fetching trending AI repos from GitHub...")
    
    use_cache = not force_refresh
    # Always fetch a pool of 7 repos, then pick the top 'count' unpublished ones
    pool_size = max(count, 7)
    trending_topics = refresh_trending_pool(limit=pool_size, use_cache=use_cache)

    if not trending_topics:
        print("ERROR: Failed to fetch trending repos. Check GitHub API availability.")
        sys.exit(1)

    # Limit to requested count
    trending_topics = trending_topics[:count]

    print(f"  Pool: {pool_size} repos, publishing top {len(trending_topics)}")
    for i, t in enumerate(trending_topics, 1):
        r = t.get("repo", {})
        print(f"  {i}. {r.get('full_name', 'N/A')} - * {r.get('stars', 0):,}")
    print()

    # Step 2: Authenticate with Blogger
    print("[2/4] Authenticating with Blogger API...")
    from publish_to_blogger import get_access_token, _try_auto_save_refresh_token
    
    def _handle_rotation(new_token):
        print("  🔄 Google rotated the refresh token. Auto-saving...")
        _try_auto_save_refresh_token(new_token)
    
    access_token = get_access_token(
        os.environ["BLOGGER_CLIENT_ID"],
        os.environ["BLOGGER_CLIENT_SECRET"],
        os.environ["BLOGGER_REFRESH_TOKEN"],
        on_new_refresh=_handle_rotation,
    )
    print("  Token obtained.")
    print()

    # Step 3: Generate articles
    print(f"[3/4] Generating {count} trending article(s)...")
    from generate_article import generate_article_from_topic, insert_images

    articles = []
    for i, topic in enumerate(trending_topics):
        r = topic.get("repo", {})
        print(f"  [{i + 1}/{count}] {r.get('full_name', topic['title'][:60])}")
        try:
            article = generate_article_from_topic(topic, os.environ["DEEPSEEK_API_KEY"])
            articles.append(article)
            print(f"    OK: {len(article['content'])} chars")
        except Exception as e:
            print(f"    FAIL: {e}")

    if not articles:
        print("ERROR: No articles generated.")
        sys.exit(1)

    # Step 3b: Add images
    from image_fetcher import fetch_article_images
    print(f"\n  Adding images...")
    for article in articles:
        topic_info = {
            "title": article["title"],
            "category": article["category"],
            "keywords": article.get("keywords", []),
        }
        images = fetch_article_images(topic_info, count=2)
        if images:
            article["content"] = insert_images(article["content"], images)
            print(f"    {len(images)} images -> \"{article['title'][:50]}...\"")
        else:
            print(f"    No images for \"{article['title'][:50]}...\"")
    print()

    # Step 4: Publish
    print("[4/4] Publishing to Blogger...")
    from publish_to_blogger import publish_article

    results = []
    for i, article in enumerate(articles):
        if i > 0:
            delay = random.randint(15, 45)
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

        print(f"  [{i + 1}/{len(articles)}] Publishing: {article['title'][:70]}...")
        result = publish_article(
            access_token=access_token,
            blog_id=os.environ["BLOGGER_BLOG_ID"],
            title=article["title"],
            content=article["content"],
            labels=article.get("labels", []),
            search_description=article.get("search_description", ""),
            is_draft=is_draft,
        )
        results.append(result)

        if result["success"]:
            print(f"    OK: {result['url']}")
        else:
            print(f"    FAIL: {result.get('error', 'Unknown error')}")

    # Summary
    print()
    print("=" * 60)
    success = sum(1 for r in results if r["success"])
    print(f"Published: {success}/{len(results)}")
    for i, r in enumerate(results):
        status = "OK" if r["success"] else "FAIL"
        print(f"  [{status}] {r['title'][:80]}")
    print("=" * 60)

    # Fail the workflow if no articles were published
    if success == 0:
        print("\nERROR: No articles were published successfully!")
        sys.exit(1)

    # Mark successful repos as published (avoid repeats)
    if success > 0:
        try:
            from github_trending import mark_published
            for i, (result, topic) in enumerate(zip(results, trending_topics)):
                if result["success"]:
                    repo_name = topic.get("repo", {}).get("full_name", "")
                    if repo_name:
                        mark_published(repo_name)
                        print(f"  Marked as published: {repo_name}")
        except Exception as e:
            print(f"  [WARN] Could not mark repos: {e}")

    return results


def list_trending():
    """List trending repos without publishing."""
    load_credentials()
    from github_trending import fetch_trending_repos

    print("Fetching trending AI repos from GitHub...")
    print()
    repos = fetch_trending_repos(limit=10, use_cache=False)

    print(f"Top {len(repos)} AI Repos This Week:")
    print("-" * 70)
    for i, r in enumerate(repos, 1):
        stars = f"{r['stars']:,}".rjust(6)
        lang = r.get('language', 'N/A') or 'N/A'
        print(f"{i:2d}. {stars} *  {r['full_name']:<35s} [{lang}]")
        desc = r.get('description', 'No description')
        if len(desc) > 70:
            desc = desc[:67] + "..."
        print(f"     {desc}")
        print(f"     {r['html_url']}")
        print()


def main():
    args = sys.argv[1:]

    if "--list" in args:
        list_trending()
        return

    count = 1
    is_draft = False
    force_refresh = False

    for arg in args:
        if arg.isdigit():
            count = int(arg)
        elif arg == "--draft":
            is_draft = True
        elif arg == "--refresh":
            force_refresh = True

    run_trending_pipeline(count=count, is_draft=is_draft, force_refresh=force_refresh)


if __name__ == "__main__":
    main()

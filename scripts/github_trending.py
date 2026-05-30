# -*- coding: utf-8 -*-
"""
Fetch trending AI repositories from GitHub Search API.
No auth required for public repo searches (60 req/hour unauthenticated).
"""

import urllib.request
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# Cache directory for trending data
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_TTL_HOURS = 24  # Refresh cache daily

# AI-related search queries to diversify results
# Strategy: mix of (1) popular established repos and (2) newer trending repos
SEARCH_QUERIES = [
    # Popular AI repos with recent updates
    "topic:artificial-intelligence+pushed:>2024-01-01&sort=stars&order=desc",
    "topic:machine-learning+pushed:>2024-01-01&sort=stars&order=desc",
    "topic:llm+pushed:>2024-01-01&sort=stars&order=desc",
    "topic:ai-agent+pushed:>2025-01-01&sort=stars&order=desc",
    "topic:generative-ai+pushed:>2024-06-01&sort=stars&order=desc",
    "topic:rag+pushed:>2024-06-01&sort=stars&order=desc",
    # Newer repos gaining traction
    "topic:ai-tools+created:>2025-01-01&sort=stars&order=desc",
    "topic:llm-framework+created:>2025-01-01&sort=stars&order=desc",
]

SEARCH_BASE = "https://api.github.com/search/repositories"

# Known mega-projects to deprioritize (too generic, already saturated content)
DEPRIORITIZE = {
    "tensorflow/tensorflow", "huggingface/transformers",
    "pytorch/pytorch", "microsoft/vscode",
    "Significant-Gravitas/AutoGPT", "AUTOMATIC1111/stable-diffusion-webui",
}

PUBLISHED_FILE = CACHE_DIR / "published_repos.json"


def _load_published() -> set:
    """Load set of already-published repo full_names."""
    if not PUBLISHED_FILE.exists():
        return set()
    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("published", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def _save_published(repo_full_name: str) -> None:
    """Mark a repo as published so it won't be repeated."""
    published = _load_published()
    published.add(repo_full_name)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump({"published": sorted(list(published))}, f, indent=2)


def mark_published(repo_full_name: str) -> None:
    """Public API: mark a repo as already covered in an article."""
    _save_published(repo_full_name)


def _load_cache(cache_file: Path) -> dict | None:
    """Load cached trending data if still fresh."""
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = data.get("cached_at", "")
        if cached_at:
            cache_time = datetime.fromisoformat(cached_at)
            if datetime.now() - cache_time < timedelta(hours=CACHE_TTL_HOURS):
                return data
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    return None


def _save_cache(cache_file: Path, data: dict) -> None:
    """Save trending data to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["cached_at"] = datetime.now().isoformat()
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _fetch_repos(query: str, per_page: int = 10) -> list[dict]:
    """Fetch repositories from GitHub Search API."""
    url = f"{SEARCH_BASE}?q={query}&per_page={per_page}"
    
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "aitoolbits-blogger/1.0"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        items = data.get("items", [])
        
        repos = []
        for item in items:
            repos.append({
                "name": item.get("name", ""),
                "full_name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "html_url": item.get("html_url", ""),
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "language": item.get("language", ""),
                "topics": item.get("topics", []),
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", ""),
                "open_issues": item.get("open_issues_count", 0),
                "license": item.get("license", {}).get("spdx_id", "") if item.get("license") else "",
                "homepage": item.get("homepage", ""),
                "owner": {
                    "login": item.get("owner", {}).get("login", ""),
                    "avatar_url": item.get("owner", {}).get("avatar_url", ""),
                },
            })
        return repos
    except urllib.error.HTTPError as e:
        print(f"  [WARN] GitHub API returned {e.code} for query: {query[:50]}...")
        return []
    except Exception as e:
        print(f"  [WARN] Failed to fetch: {e}")
        return []


def fetch_trending_repos(limit: int = 10, use_cache: bool = True) -> list[dict]:
    """
    Fetch top trending AI repositories from GitHub.
    
    Args:
        limit: Max number of repos to return
        use_cache: Whether to use cached data if fresh
    
    Returns:
        List of repo dicts with keys: name, full_name, description,
        html_url, stars, forks, language, topics, owner, homepage
    """
    cache_file = CACHE_DIR / "trending_repos.json"
    
    # Try cache first
    if use_cache:
        cached = _load_cache(cache_file)
        if cached:
            repos = cached.get("repos", [])
            if len(repos) >= limit:
                print(f"[CACHE] Using cached trending data ({len(repos)} repos)")
                return repos[:limit]
    
    # Fetch fresh data
    print("[FETCH] Fetching trending AI repos from GitHub...")
    all_repos = []
    seen = set()
    
    for query in SEARCH_QUERIES:
        if len(all_repos) >= limit * 3:  # Fetch 3x needed for dedup
            break
        repos = _fetch_repos(query, per_page=8)
        for repo in repos:
            if repo["full_name"] not in seen:
                seen.add(repo["full_name"])
                all_repos.append(repo)
        time.sleep(1.5)  # Rate limiting
    
    # Deduplicate and sort by stars
    all_repos.sort(key=lambda r: r.get("stars", 0), reverse=True)
    
    # Filter: prefer repos with good descriptions, exclude deprioritized + published
    published = _load_published()
    filtered = [
        r for r in all_repos
        if r.get("description") and len(r["description"]) > 20
        and r.get("full_name") not in DEPRIORITIZE
        and r.get("full_name") not in published
    ]
    if not filtered:
        filtered = all_repos  # fallback if all filtered out
    
    result = filtered[:limit]
    
    # Cache results
    _save_cache(cache_file, {"repos": result})
    
    print(f"[DONE] Fetched {len(all_repos)} repos, returning top {len(result)}")
    return result


def get_trending_topics(repos: list[dict]) -> list[dict]:
    """
    Convert fetched repos into article topic dicts.
    Each repo becomes one article topic.
    
    Returns list of topic dicts compatible with existing pipeline.
    """
    topics = []
    for i, repo in enumerate(repos):
        stars_str = f"{repo['stars']:,}" if repo['stars'] else "new"
        
        topic = {
            "title": f"{repo['name']}: The AI Repo Gaining {stars_str}+ Stars This Week",
            "category": "GitHub Trending",
            "type": "github_trending",
            "is_trending": True,
            "keywords": [
                repo['name'],
                f"{repo['name']} GitHub",
                repo.get("language", "AI"),
                "GitHub trending",
                "open source AI",
            ],
            "repo": {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description", ""),
                "html_url": repo["html_url"],
                "stars": repo["stars"],
                "forks": repo.get("forks", 0),
                "language": repo.get("language", ""),
                "topics": repo.get("topics", []),
                "open_issues": repo.get("open_issues", 0),
                "license": repo.get("license", ""),
                "homepage": repo.get("homepage", ""),
                "owner_login": repo.get("owner", {}).get("login", ""),
            },
        }
        topics.append(topic)
    
    return topics


def get_trending_article_prompt(topic: dict) -> str:
    """
    Generate a prompt for DeepSeek to write an in-depth article
    about a trending GitHub repo.
    
    Args:
        topic: Topic dict with repo info
    
    Returns:
        Prompt string for DeepSeek
    """
    repo = topic.get("repo", {})
    repo_name = repo.get("full_name", topic["title"])
    description = repo.get("description", "An open-source AI project")
    stars = repo.get("stars", 0)
    language = repo.get("language", "N/A")
    topics_list = repo.get("topics", [])
    topics_str = ", ".join(topics_list[:5]) if topics_list else "N/A"
    homepage = repo.get("homepage", "")
    
    stars_str = f"{stars:,}" if stars else "many"
    
    prompt = f"""You are a tech writer for a blog covering AI tools and open-source projects.

Write a comprehensive, SEO-optimized blog article about the GitHub repository **{repo_name}**.

Here are the facts about this project:
- Full Name: {repo_name}
- Description: {description}
- Stars: {stars_str}
- Language: {language}
- Topics: {topics_str}
- Homepage: {homepage if homepage else "No separate homepage"}
- GitHub URL: {repo.get("html_url", "")}

Article Requirements:
- Title: "{topic.get('title')}"  
- Length: 800-1200 words, well-structured with H2 and H3 headings
- Format: Clean HTML (no <!DOCTYPE>, no <html>, no <body> - just the article body)
- Do NOT use <h1> tags (the platform handles the title)
- Use proper semantic HTML: <h2>, <h3>, <p>, <ul>, <li>, <code>, <strong>

Structure:
1. **Opening hook** (2-3 sentences): Why this repo is gaining attention right now ({stars_str} stars and counting)
2. **What is {repo.get('name', 'it')}?** (h2): Overview of the project, its purpose, who it's for
3. **Key Features** (h2): 3-5 standout features with explanations
4. **Getting Started** (h2): Quick installation guide (one-liner pip/npm install if applicable, or git clone)
5. **Why It's Trending** (h2): Context about why this project is gaining traction in the AI community
6. **Who Should Use It** (h2): Target audience - developers, researchers, hobbyists, etc.
7. **Comparison** (h2): How it compares to similar tools (mention 1-2 alternatives if relevant)
8. **Bottom Line** (h2): Final verdict, 2-3 sentences

Style Guidelines:
- Write in a conversational but knowledgeable tone
- Use short paragraphs (2-4 sentences max)
- Include practical value: tell the reader WHAT they can build with this
- Mention the star count naturally (e.g., "With {stars_str} stars on GitHub, {repo.get('name', 'the project')} has clearly resonated with developers...")
- Link to the GitHub repo naturally in the text: <a href="{repo.get('html_url', '#')}" target="_blank" rel="noopener noreferrer">View on GitHub</a>
- Add a call-to-action at the end: encourage bookmarking or starring the repo

SEO Requirements (GEO - Generative Engine Optimization):
- Naturally include keywords: {repo.get('name', '')}, GitHub trending, AI open source, {language} AI project
- Write for featured snippets: answer "What is {repo.get('name', '')}?" clearly in the first H2 section
- Include schema-friendly structure with clear H2/H3 hierarchy

Return ONLY the HTML article body, nothing else. No markdown, no code fences, no explanations before or after."""

    return prompt


# Topic pool for trending articles (used when cache has fresh data)
TRENDING_TOPIC_POOL = {}

def refresh_trending_pool(limit: int = 10, use_cache: bool = True) -> list[dict]:
    """Fetch trending repos and update the topic pool. Returns topic list."""
    repos = fetch_trending_repos(limit=limit, use_cache=use_cache)
    topics = get_trending_topics(repos)
    return topics


if __name__ == "__main__":
    # Quick test
    repos = fetch_trending_repos(limit=5, use_cache=False)
    print(f"\nTop {len(repos)} AI Repos:")
    print("-" * 60)
    for i, r in enumerate(repos, 1):
        stars = f"{r['stars']:,}".rjust(6)
        print(f"{i}. {stars} * {r['full_name']}")
        print(f"   {r.get('description', 'No description')[:100]}")
        print()

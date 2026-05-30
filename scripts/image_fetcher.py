# -*- coding: utf-8 -*-
"""
Image fetcher for blog articles.
Primary: Unsplash API (free key, instant setup)
Fallback: Curated Unsplash direct photo links (zero config, always works)

Usage:
    UNSPLASH_ACCESS_KEY=xxx python image_fetcher.py
"""

import os
import json
import random
import urllib.request
import urllib.error
import urllib.parse
import ssl

# ==================== Curated fallback images ====================
# High-quality Unsplash direct links by topic - always work, no key needed.
# Each topic has 5+ images so articles don't repeat.

FALLBACK_IMAGES = {
    "AI Image Generation": [
        "https://images.unsplash.com/photo-1547954575-855750c57bd3",
        "https://images.unsplash.com/photo-1633356122544-f134324a6cee",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e",
        "https://images.unsplash.com/photo-1677442136019-21780ecad995",
    ],
    "AI Video Generation": [
        "https://images.unsplash.com/photo-1492619375914-88005aa9e8fb",
        "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85",
        "https://images.unsplash.com/photo-1536240478700-b869070f9279",
        "https://images.unsplash.com/photo-1598387993441-a364f854c3e1",
        "https://images.unsplash.com/photo-1611162616475-46b635cb6868",
    ],
    "AI Writing": [
        "https://images.unsplash.com/photo-1455390582262-044cdead277a",
        "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2",
        "https://images.unsplash.com/photo-1434030216411-0b793f4b4173",
        "https://images.unsplash.com/photo-1553545204-4f7d339aa06a",
        "https://images.unsplash.com/photo-1499750310107-5fef28a66643",
    ],
    "AI Coding": [
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6",
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085",
        "https://images.unsplash.com/photo-1555066931-4365d14bab8c",
        "https://images.unsplash.com/photo-1515879218367-8466d910auj9",
        "https://images.unsplash.com/photo-1504639725590-34d0984388bd",
    ],
    "AI Audio": [
        "https://images.unsplash.com/photo-1478737270239-2f02b77fc618",
        "https://images.unsplash.com/photo-1598653222000-6b7b7a552625",
        "https://images.unsplash.com/photo-1516280440614-37939bbacd81",
        "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04",
        "https://images.unsplash.com/photo-1558618666-fcd25c85f82e",
    ],
    "AI Productivity": [
        "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b",
        "https://images.unsplash.com/photo-1512758017271-d7b84c2113f1",
        "https://images.unsplash.com/photo-1611532736597-de2d4265fba3",
        "https://images.unsplash.com/photo-1497215728101-856f4ea42174",
        "https://images.unsplash.com/photo-1507925921958-8a62f3d1a50d",
    ],
    "AI Design": [
        "https://images.unsplash.com/photo-1561070791-2526d30994b5",
        "https://images.unsplash.com/photo-1559028012-481c04fa702d",
        "https://images.unsplash.com/photo-1613909207039-6b173b4dfb4f",
        "https://images.unsplash.com/photo-1626785774573-4b799315345d",
        "https://images.unsplash.com/photo-1558655146-d09347e92766",
    ],
    "Free AI Tools": [
        "https://images.unsplash.com/photo-1531482615713-2afd69097998",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5",
        "https://images.unsplash.com/photo-1518770660439-4636190af475",
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
    ],
    "AI Marketing": [
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71",
        "https://images.unsplash.com/photo-1553877522-43269d4ea984",
        "https://images.unsplash.com/photo-1432888498266-38ffec3eaf0a",
        "https://images.unsplash.com/photo-1559136555-9303baea8ebd",
    ],
    "AI Business": [
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf",
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40",
        "https://images.unsplash.com/photo-1552664730-d307ca884978",
        "https://images.unsplash.com/photo-1600880292203-757bb62b4baf",
        "https://images.unsplash.com/photo-1553729459-afe8a2a582c0",
    ],
    "GitHub Trending": [
        "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb",
        "https://images.unsplash.com/photo-1556075798-4825dfaaf498",
        "https://images.unsplash.com/photo-1520085601670-ee14aa5fa072",
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d",
        "https://images.unsplash.com/photo-1518770660439-4636190af475",
    ],
}

# Generic fallback if no category match
GENERIC_FALLBACK = [
    "https://images.unsplash.com/photo-1677442136019-21780ecad995",
    "https://images.unsplash.com/photo-1620712943543-bcc4688e7485",
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e",
    "https://images.unsplash.com/photo-1531482615713-2afd69097998",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
]

UNSPLASH_API = "https://api.unsplash.com"
PEXELS_API_URL = "https://api.pexels.com/v1"


# ==================== Unsplash API ====================

def search_unsplash(query: str, count: int = 3, orientation: str = "landscape") -> list:
    """Search Unsplash API (requires UNSPLASH_ACCESS_KEY env var)."""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not access_key:
        return []

    params = urllib.parse.urlencode({
        "query": query,
        "per_page": min(count * 2, 10),
        "orientation": orientation,
        "content_filter": "high",
    })
    url = f"{UNSPLASH_API}/search/photos?{params}"
    headers = {"Authorization": f"Client-ID {access_key}"}
    req = urllib.request.Request(url, headers=headers)

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    photos = data.get("results", [])
    results = []
    for photo in photos[:count]:
        raw_url = photo["urls"]["regular"]
        results.append({
            "url": f"{raw_url}&w=800&fit=max",
            "alt": photo.get("alt_description", query) or query,
            "photographer": photo["user"]["name"],
            "photographer_url": photo["user"]["links"]["html"],
            "width": 800,
            "height": 450,
        })
    return results


# ==================== Pexels API (legacy, kept for compatibility) ====================

def search_pexels(query: str, count: int = 3, orientation: str = "landscape") -> list:
    """Search Pexels API (requires PEXELS_API_KEY env var)."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []

    params = urllib.parse.urlencode({
        "query": query,
        "per_page": min(count * 2, 10),
        "orientation": orientation,
        "size": "large",
    })
    url = f"{PEXELS_API_URL}/search?{params}"
    headers = {"Authorization": api_key}
    req = urllib.request.Request(url, headers=headers)

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []

    photos = data.get("photos", [])
    seen = set()
    results = []
    for photo in photos:
        if len(results) >= count:
            break
        p = photo["photographer"]
        if p in seen:
            continue
        seen.add(p)
        src = photo["src"].get("large", photo["src"]["original"])
        sep = "&" if "?" in src else "?"
        results.append({
            "url": f"{src}{sep}auto=compress&cs=tinysrgb&w=800",
            "alt": photo.get("alt", query) or query,
            "photographer": p,
            "photographer_url": photo.get("photographer_url", ""),
            "width": 800,
            "height": 450,
        })
    return results


# ==================== Combined search ====================

def search_images(query: str, count: int = 3, orientation: str = "landscape") -> list:
    """Search for images - tries Unsplash first, then Pexels."""
    # Try Unsplash API
    images = search_unsplash(query, count, orientation)
    if images:
        return images

    # Try Pexels API
    images = search_pexels(query, count, orientation)
    if images:
        return images

    return []


# ==================== Topic keywords ====================

def get_image_keywords(topic: dict) -> list:
    """Generate image search keywords from article topic."""
    category_map = {
        "AI Image Generation": ["artificial intelligence art", "digital art technology", "neural network visualization"],
        "AI Video Generation": ["video editing technology", "digital content creation", "film production"],
        "AI Writing": ["content creation workspace", "digital writing technology", "blog writing"],
        "AI Coding": ["programming code screen", "software development", "developer programming"],
        "AI Audio": ["music production studio", "audio recording", "podcast recording"],
        "AI Productivity": ["productivity workspace", "smart office", "digital organization"],
        "AI Design": ["graphic design workspace", "digital design tools", "UI design"],
        "Free AI Tools": ["AI applications", "digital tools", "tech workspace"],
        "AI Marketing": ["digital marketing analytics", "social media technology", "SEO analytics"],
        "AI Business": ["business AI technology", "data analytics", "business automation"],
        "GitHub Trending": ["github open source", "software development community", "code repository"],
    }

    keywords = category_map.get(topic.get("category", ""), ["artificial intelligence", "technology innovation"])
    title = topic.get("title", "").lower()

    if "headshot" in title or "portrait" in title:
        keywords = ["professional headshot", "business portrait"]
    elif "logo" in title or "brand" in title:
        keywords = ["brand logo design", "creative branding"]
    elif "meme" in title:
        keywords = ["funny internet culture", "viral social media"]
    elif "music" in title or "song" in title:
        keywords = ["music production", "audio creation"]
    elif "resume" in title or "cv" in title:
        keywords = ["professional resume", "career development"]

    return keywords


# ==================== Fallback images ====================

def get_fallback_images(topic: dict, count: int = 3) -> list:
    """Get curated Unsplash images by topic category - always works, no key needed."""
    category = topic.get("category", "")
    urls = FALLBACK_IMAGES.get(category, GENERIC_FALLBACK)

    # Shuffle to avoid same images every time
    shuffled = urls.copy()
    random.shuffle(shuffled)

    results = []
    for i, url in enumerate(shuffled[:count]):
        results.append({
            "url": f"{url}?w=800&fit=max&q=80",
            "alt": topic.get("title", "AI technology"),
            "photographer": "Unsplash",
            "photographer_url": "https://unsplash.com",
            "width": 800,
            "height": 450,
        })

    return results


# ==================== Main entry ====================

def fetch_article_images(topic: dict, count: int = 3) -> list:
    """Fetch images for an article.

    Priority:
    1. Unsplash API (if UNSPLASH_ACCESS_KEY is set)
    2. Pexels API (if PEXELS_API_KEY is set)
    3. Curated Unsplash direct links (always works)
    """
    keywords = get_image_keywords(topic)
    all_images = []

    for kw in keywords:
        if len(all_images) >= count:
            break
        images = search_images(kw, count - len(all_images))
        existing = {img["url"] for img in all_images}
        for img in images:
            if img["url"] not in existing:
                all_images.append(img)
                existing.add(img["url"])

    # If APIs didn't return enough, use curated fallback
    if len(all_images) < count:
        fallback = get_fallback_images(topic, count - len(all_images))
        existing = {img["url"] for img in all_images}
        for img in fallback:
            if img["url"] not in existing:
                all_images.append(img)

    return all_images[:count]


if __name__ == "__main__":
    # Quick test
    test_topics = [
        {"title": "Best AI Image Generators in 2026", "category": "AI Image Generation", "keywords": ["AI", "image"]},
        {"title": "ChatGPT vs Claude vs Gemini", "category": "AI Writing", "keywords": ["AI", "writing"]},
        {"title": "Best AI Coding Assistants", "category": "AI Coding", "keywords": ["coding", "AI"]},
    ]

    for topic in test_topics:
        print(f"\nTopic: {topic['title']}")
        print(f"  Category: {topic['category']}")
        print(f"  Keywords: {get_image_keywords(topic)}")
        images = fetch_article_images(topic)
        print(f"  Found {len(images)} images:")
        for i, img in enumerate(images):
            print(f"    [{i+1}] \"{img['alt'][:50]}\" by {img.get('photographer', '?')}")

"""
Image fetcher using Pexels API.
Fetches relevant, high-quality images for blog articles.

Pexels API: Free, 200 requests/hour, 20,000 requests/month.
Signup: https://www.pexels.com/api/ (instant approval)

Usage:
    PEXELS_API_KEY=xxx python image_fetcher.py
"""

import os
import json
import random
import urllib.request
import urllib.error
import urllib.parse
import ssl

PEXELS_API_URL = "https://api.pexels.com/v1"


def search_images(query: str, count: int = 3, orientation: str = "landscape") -> list:
    """Search for images on Pexels.

    Args:
        query: Search query (e.g., "artificial intelligence technology")
        count: Number of images to return (1-3)
        orientation: "landscape", "portrait", or "squarish"

    Returns:
        List of dicts with keys: url, alt, photographer, photographer_url, width, height
    """
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []

    params = urllib.parse.urlencode({
        "query": query,
        "per_page": min(count * 2, 10),  # Fetch extra for diversity filtering
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
    except Exception as e:
        return []

    photos = data.get("photos", [])
    if not photos:
        return []

    # Select diverse images from different photographers
    results = []
    seen_photographers = set()
    for photo in photos:
        if len(results) >= count:
            break
        photographer = photo["photographer"]
        if photographer in seen_photographers:
            continue
        seen_photographers.add(photographer)

        # Use large image URL with web optimization params
        src = photo["src"].get("large", photo["src"]["original"])
        separator = "&" if "?" in src else "?"
        img_url = f"{src}{separator}auto=compress&cs=tinysrgb&w=800"

        # Calculate proportional height for responsive layout
        orig_w = max(photo.get("width", 800), 1)
        orig_h = photo.get("height", 500)
        display_w = 800
        display_h = max(int(orig_h * display_w / orig_w), 300)

        results.append({
            "url": img_url,
            "alt": photo.get("alt", query) or query,
            "photographer": photographer,
            "photographer_url": photo.get("photographer_url", ""),
            "width": display_w,
            "height": display_h,
        })

    return results


def get_image_keywords(topic: dict) -> list:
    """Generate image search keywords from article topic for Pexels.

    Returns multiple keyword variations to try if the first search
    doesn't return enough results.
    """
    category_map = {
        "AI Image Generation": [
            "artificial intelligence art",
            "digital art technology",
            "AI creative tools",
            "neural network visualization",
        ],
        "AI Video Generation": [
            "video editing technology",
            "digital content creation",
            "film production workspace",
            "AI video tools",
        ],
        "AI Writing": [
            "AI writing assistant",
            "content creation workspace",
            "digital writing technology",
            "blog writing laptop",
        ],
        "AI Coding": [
            "programming code screen",
            "software development workspace",
            "AI coding technology",
            "developer programming",
        ],
        "AI Audio": [
            "music production studio",
            "audio recording technology",
            "podcast recording setup",
            "sound engineering",
        ],
        "AI Productivity": [
            "productivity workspace",
            "AI assistant technology",
            "smart office workspace",
            "digital organization",
        ],
        "AI Design": [
            "graphic design workspace",
            "digital design tools",
            "UI design technology",
            "creative design studio",
        ],
        "Free AI Tools": [
            "free software technology",
            "AI applications collection",
            "digital tools technology",
            "tech workspace setup",
        ],
        "AI Marketing": [
            "digital marketing analytics",
            "social media technology",
            "content marketing workspace",
            "SEO analytics dashboard",
        ],
        "AI Business": [
            "business AI technology",
            "corporate data analytics",
            "business automation",
            "data dashboard",
        ],
    }

    keywords = category_map.get(topic.get("category", ""), [
        "artificial intelligence",
        "technology innovation",
        "AI tools",
    ])

    # Override with more specific keywords based on title keywords
    title = topic.get("title", "").lower()
    if "headshot" in title or "portrait" in title:
        keywords = ["professional headshot", "business portrait", "corporate photography"]
    elif "logo" in title or "brand" in title:
        keywords = ["brand logo design", "creative branding", "business identity"]
    elif "meme" in title:
        keywords = ["funny internet culture", "viral social media", "humor technology"]
    elif "music" in title or "song" in title:
        keywords = ["music production", "music studio", "audio creation"]
    elif "resume" in title or "CV" in title:
        keywords = ["professional resume", "career development", "job application"]

    # Add category as fallback keyword
    cat = topic.get("category", "")
    if cat and cat not in keywords[0].lower():
        keywords.append(cat.lower() + " technology")

    return keywords


def fetch_article_images(topic: dict, count: int = 3) -> list:
    """Fetch images for an article based on its topic.

    Tries multiple keyword variations until enough images are found.
    Returns 0-3 images depending on API availability and search results.

    Args:
        topic: Article topic dict with 'title', 'category', 'keywords'
        count: Maximum number of images to fetch

    Returns:
        List of image dicts (url, alt, photographer, etc.)
    """
    keywords = get_image_keywords(topic)
    all_images = []

    for kw in keywords:
        if len(all_images) >= count:
            break
        images = search_images(kw, count - len(all_images))
        # Avoid duplicates by URL
        existing_urls = {img["url"] for img in all_images}
        for img in images:
            if img["url"] not in existing_urls:
                all_images.append(img)
                existing_urls.add(img["url"])

    # Limit to requested count
    return all_images[:count]


if __name__ == "__main__":
    # Quick test
    test_topics = [
        {"title": "Best AI Image Generators in 2026", "category": "AI Image Generation"},
        {"title": "ChatGPT vs Claude vs Gemini", "category": "AI Writing"},
        {"title": "Best AI Coding Assistants", "category": "AI Coding"},
    ]

    for topic in test_topics:
        print(f"\nTopic: {topic['title']}")
        print(f"  Keywords: {get_image_keywords(topic)}")
        images = fetch_article_images(topic)
        print(f"  Found {len(images)} images:")
        for i, img in enumerate(images):
            print(f"    [{i+1}] \"{img['alt']}\" by {img['photographer']}")

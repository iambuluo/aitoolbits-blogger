"""
Article generator using DeepSeek API.
Generates SEO-optimized blog articles for aitoolbits.blogspot.com
"""

import os
import json
import random
import hashlib
from datetime import datetime
from topics import get_random_topic, get_article_prompt


def _is_duplicate(title: str) -> bool:
    """Quick in-memory duplicate check against published titles."""
    from published_urls import check_if_duplicate
    return check_if_duplicate(title)["duplicate"]


def call_deepseek(prompt: str, api_key: str, model: str = "deepseek-chat") -> str:
    """Call DeepSeek API to generate article content."""
    import urllib.request
    import urllib.error

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert tech blogger who writes engaging, SEO-optimized articles "
                    "about AI tools and technology. Your writing style is conversational yet "
                    "professional, similar to top tech publications like The Verge or TechCrunch. "
                    "You always include practical examples, actionable advice, and real data. "
                    "You write in pure HTML format without any markdown syntax.\n\n"
                    "CRITICAL RULES FOR EVERY ARTICLE:\n"
                    "1. PRODUCT LINKS: Whenever you mention an AI tool, product, or service by name, "
                    "you MUST include its official website URL as a hyperlink on the first mention. "
                    "Format: <a href=\"https://example.com\" target=\"_blank\" rel=\"nofollow noopener\">Product Name</a>. "
                    "Only link to the product's actual official website. If unsure of the URL, "
                    "use the most commonly known domain (e.g. openai.com for ChatGPT, "
                    "anthropic.com for Claude, midjourney.com for Midjourney, runwayml.com for Runway, "
                    "suno.com for Suno AI, notion.so for Notion, figma.com for Figma, "
                    "canva.com for Canva, vercel.com for Vercel, github.com for GitHub, "
                    "elevenlabs.io for ElevenLabs, jasper.ai for Jasper, grammarly.com for Grammarly, "
                    "cursor.com for Cursor, bolt.new for Bolt.new, lovable.dev for Lovable, "
                    "replit.com for Replit, gamma.app for Gamma, framer.com for Framer, "
                    "stability.ai for Stable Diffusion, pika.art for Pika, klingai.com for Kling AI).\n"
                    "2. E-E-A-T: Demonstrate Experience, Expertise, Authoritativeness, and Trustworthiness. "
                    "Use specific data, version numbers, pricing details, and real-world examples.\n"
                    "3. ORIGINALITY: Write unique, insightful content. Avoid generic filler. "
                    "Include personal analysis and opinions based on features.\n"
                    "4. READABILITY: Use short paragraphs (2-3 sentences), bullet points, "
                    "and clear H2/H3 hierarchy. Aim for Flesch readability score above 60.\n"
                    "5. INTERNAL CONTEXT: Write as an independent AI tools reviewer "
                    "on aitoolbits.blogspot.com, a dedicated AI tools review blog."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8 + random.uniform(-0.2, 0.2),
        "max_tokens": 4096,
    }

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"DeepSeek API error {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"DeepSeek API request failed: {e}")


def call_deepseek_trending(prompt: str, api_key: str, model: str = "deepseek-chat") -> str:
    """Call DeepSeek API with a conversational reviewer persona for trending articles."""
    import urllib.request
    import urllib.error

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a developer who loves trying new open-source projects and sharing "
                    "honest, no-BS opinions. Your style is like a YouTube tech reviewer: personal, "
                    "direct, conversational. You actually try things and tell people what you think.\n\n"
                    "VOICE RULES:\n"
                    "- Write in FIRST PERSON. \"I tried this...\" \"I found that...\"\n"
                    "- Be CONVERSATIONAL. Like you're explaining to a friend.\n"
                    "- Have REAL OPINIONS. If something is confusing, say so.\n"
                    "- Use EVERYDAY language. Not \"leverages cutting-edge technology\" but \"it's clever how they...\"\n"
                    "- Be SPECIFIC. Mention actual features, not vague praise.\n"
                    "- Keep it REAL. Acknowledge limitations. Nothing is perfect.\n"
                    "- Short paragraphs. One idea per paragraph.\n\n"
                    "NEVER DO:\n"
                    "- Corporate press-release language (\"revolutionary\", \"game-changing\")\n"
                    "- Generic AI-speak (\"In today's fast-paced digital landscape...\")\n"
                    "- Fake enthusiasm\n"
                    "- Filler paragraphs that say nothing\n"
                    "- Markdown. Output pure HTML only.\n\n"
                    "You write for aitoolbits.blogspot.com - an independent blog that actually "
                    "tests AI tools and open-source projects before recommending them."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 4096,
    }

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise Exception(f"DeepSeek API error {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"DeepSeek API request failed: {e}")


def build_image_html(img: dict) -> str:
    """Build SEO-optimized image HTML from image data.

    Includes:
    - Semantic <figure> wrapper
    - Descriptive alt text for Google Image Search
    - Proper width/height to prevent CLS (Core Web Vitals)
    - Lazy loading for performance
    - Photographer credit in figcaption
    """
    height = max(img.get("height", 500), 300)
    return (
        f'\n<figure style="margin:24px 0;text-align:center;">'
        f'\n  <img src="{img["url"]}"'
        f'\n       alt="{img["alt"]}"'
        f'\n       loading="lazy"'
        f'\n       style="max-width:100%;height:auto;border-radius:8px;"'
        f'\n       width="{img["width"]}"'
        f'\n       height="{height}">'
        f'\n  <figcaption style="font-size:0.9em;color:#666;margin-top:8px;'
        f'font-style:italic;">Photo by '
        f'<a href="{img["photographer_url"]}" target="_blank" '
        f'rel="nofollow noopener">{img["photographer"]}</a> via Pexels'
        f'</figcaption>\n</figure>'
    )


def insert_images(content: str, images: list) -> str:
    """Insert images into article content at strategic positions for SEO/GEO.

    Placement strategy:
    - 1st image: After the 1st H2 (hero image, grabs attention immediately)
    - 2nd image: After the 3rd H2 (mid-article, reduces bounce rate)
    - 3rd image: After the 5th H2 (deep content, only for longer articles)

    SEO benefits:
    - Images increase time-on-page (reduces bounce rate)
    - Alt text helps Google Image Search ranking
    - Proper width/height prevents CLS (Core Web Vitals signal)
    - Lazy loading improves page load speed
    - Figcaption adds semantic context for search engines
    """
    if not images:
        return content

    lines = content.split("\n")
    result_lines = []
    h2_count = 0
    img_index = 0
    image_positions = {1, 3, 5}  # Insert after these H2 positions

    for line in lines:
        result_lines.append(line)
        if line.strip().startswith("<h2"):
            h2_count += 1
            if h2_count in image_positions and img_index < len(images):
                img_html = build_image_html(images[img_index])
                result_lines.append(img_html)
                img_index += 1

    return "\n".join(result_lines)


def clean_html(content: str) -> str:
    """Clean and validate generated HTML content."""
    # Remove markdown artifacts that AI might generate
    content = content.replace("```html", "").replace("```", "")
    # Remove any H1 tags (blog platform handles title)
    lines = content.split("\n")
    cleaned = []
    for line in lines:
        if line.strip().startswith("<h1") or line.strip().startswith("</h1"):
            continue
        cleaned.append(line)
    content = "\n".join(cleaned)
    # Remove leading/trailing whitespace
    content = content.strip()
    # Ensure content starts with an HTML tag
    if content and not content.startswith("<"):
        content = "<p>" + content + "</p>"
    return content


def insert_ads(content: str, provider: str = None, zone_id: str = None) -> str:
    """Insert ad code into article content.

    Strategy: 3 ad placements for maximum revenue without hurting readability.
    1. After the 2nd H2 (mid-article, after intro)
    2. After the 4th H2 (deep mid-article)
    3. At the end (footer)

    Args:
        content: Clean HTML article content
        provider: "monetag" or "adsense" or "none"
        zone_id: Ad zone ID (Monetag) or client ID (AdSense)

    Returns:
        HTML content with ads inserted
    """
    provider = provider or os.environ.get("AD_PROVIDER", "none")
    if provider == "none":
        return content

    zone_id = zone_id or os.environ.get("AD_ZONE_ID", "229646")

    if provider == "monetag":
        ad_code = (
            f'<div style="margin:24px 0;text-align:center;clear:both;">'
            f'<script src="https://quge5.com/88/tag.min.js" data-zone="{zone_id}" '
            f'async data-cfasync="false"></script></div>'
        )
    elif provider == "adsense":
        client = zone_id
        ad_code = (
            f'<div style="margin:24px 0;text-align:center;clear:both;">'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{client}" '
            f'data-ad-slot="auto" data-ad-format="auto" '
            f'data-full-width-responsive="true"></ins>'
            f'<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div>'
        )
    else:
        return content

    # Insert ads after specific H2 positions
    lines = content.split("\n")
    result_lines = []
    h2_count = 0
    ad_positions = {2, 4}  # Insert after 2nd and 4th H2
    ads_inserted = 0

    for line in lines:
        result_lines.append(line)
        if line.strip().startswith("<h2") and h2_count + 1 in ad_positions and ads_inserted < 2:
            h2_count += 1
            result_lines.append("")
            result_lines.append(ad_code)
            result_lines.append("")
            ads_inserted += 1
        elif line.strip().startswith("<h2"):
            h2_count += 1

    content_with_ads = "\n".join(result_lines)

    # Always add footer ad
    return content_with_ads + "\n\n" + ad_code


def _generate_labels(topic: dict) -> list:
    """Generate smart, SEO-friendly labels for Blogger."""
    raw_labels = [topic["category"]]
    for kw in topic["keywords"][:3]:
        label = kw.title()
        if len(label) <= 30:
            raw_labels.append(label)
    raw_labels.append(f"{topic['type'].title()} Article")
    # Deduplicate while preserving order
    seen = set()
    labels = []
    for l in raw_labels:
        if l not in seen:
            seen.add(l)
            labels.append(l)
    return labels[:6]  # Blogger supports max 20, 5-6 is optimal


def _generate_search_description(topic: dict) -> str:
    """Generate an SEO meta description for the article (150-160 chars)."""
    type_desc = {
        "comparison": f"Compare the best {topic['category'].lower()} tools. Find out which {topic['keywords'][0]} is right for you with our detailed analysis.",
        "review": f"Honest review of {topic['title'].replace(' in ' + str(__import__('datetime').datetime.now().year), '')}. Features, pricing, pros & cons, and our verdict.",
        "tutorial": f"Step-by-step tutorial: {topic['title'].replace(' in ' + str(__import__('datetime').datetime.now().year), '')}. Learn how to get started with practical tips.",
        "list": f"Discover the top {topic['category'].lower()} tools. Complete list with features, pricing, and recommendations for {topic['keywords'][0]}.",
    }
    desc = type_desc.get(topic["type"], f"{topic['title']}. Expert analysis and recommendations.")
    # Blogger/Blogger search description max ~500 chars, but SEO best is 150-160
    if len(desc) > 160:
        desc = desc[:157] + "..."
    return desc


def generate_article_from_topic(topic: dict, api_key: str = None) -> dict:
    """Generate an article from a specific topic dict.

    Args:
        topic: Topic dict with title, category, keywords, type, and optional repo info
        api_key: DeepSeek API key (or env DEEPSEEK_API_KEY)

    Returns:
        dict with keys: title, content, category, keywords, filename
    """
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is required")

    # Pre-flight duplicate check BEFORE calling the API
    if _is_duplicate(topic["title"]):
        print(f"  ⚠ SKIP: Title '{topic['title']}' is a known duplicate")
        raise ValueError("DUPLICATE_TOPIC")

    # For trending topics, use specialized prompt + conversational system role
    is_trending = topic.get("is_trending") and topic.get("type") == "github_trending"
    if is_trending:
        try:
            from github_trending import get_trending_article_prompt
            prompt = get_trending_article_prompt(topic)
        except ImportError:
            prompt = get_article_prompt(topic)
    else:
        prompt = get_article_prompt(topic)

    print(f"  Generating: {topic['title']}")

    if is_trending:
        content = call_deepseek_trending(prompt, api_key)
    else:
        content = call_deepseek(prompt, api_key)
    content = clean_html(content)
    content = insert_ads(content)

    # Generate filename from title
    slug = topic["title"].lower()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = slug.replace(" ", "-")[:80]
    slug = slug.strip("-")

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.html"

    # Keywords: for trending articles, use repo topics
    if topic.get("is_trending") and topic.get("type") == "github_trending":
        repo = topic.get("repo", {})
        keywords = repo.get("topics", topic.get("keywords", ["GitHub", "AI", "trending"]))
    else:
        keywords = topic.get("keywords", [])

    search_desc = _generate_search_description(topic)
    
    # Enhance search description if topic has custom SEO prompt
    if topic.get("search_description"):
        search_desc = topic["search_description"]
    
    return {
        "title": topic["title"],
        "content": content,
        "category": topic.get("category", "GitHub Trending"),
        "keywords": keywords,
        "search_description": search_desc,
        "labels": _generate_labels(topic),
        "filename": filename,
        "repo_url": topic.get("repo", {}).get("html_url", ""),
    }


def generate_article(api_key: str = None) -> dict:
    """Generate a complete article ready for publishing.

    Returns:
        dict with keys: title, content, category, keywords, filename
    """
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is required")

    topic = get_random_topic()
    prompt = get_article_prompt(topic)

    print(f"  Generating: {topic['title']}")

    # Pre-flight duplicate check BEFORE calling the API
    if _is_duplicate(topic["title"]):
        print(f"  ⚠ SKIP: Title '{topic['title']}' is a known duplicate")
        raise ValueError("DUPLICATE_TOPIC")

    content = call_deepseek(prompt, api_key)
    content = clean_html(content)
    content = insert_ads(content)

    # Generate filename from title
    slug = topic["title"].lower()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = slug.replace(" ", "-")[:80]
    slug = slug.strip("-")

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.html"

    return {
        "title": topic["title"],
        "content": content,
        "category": topic["category"],
        "keywords": topic["keywords"],
        "search_description": _generate_search_description(topic),
        "labels": _generate_labels(topic),
        "filename": filename,
    }


def generate_multiple(count: int = 1, api_key: str = None) -> list:
    """Generate multiple articles."""
    articles = []
    used_titles = set()
    for i in range(count):
        generated = False
        attempts = 0
        while not generated and attempts < 15:
            attempts += 1
            try:
                article = generate_article(api_key)
                if article["title"] not in used_titles:
                    used_titles.add(article["title"])
                    articles.append(article)
                    generated = True
                    print(f"  [{i+1}/{count}] Done: {article['filename']} (attempt {attempts})")
            except ValueError as e:
                if str(e) == "DUPLICATE_TOPIC":
                    continue
                raise
            except Exception as e:
                # Unexpected error, stop
                print(f"  [{i+1}/{count}] Error: {e}")
                raise
        if not generated:
            print(f"  [{i+1}/{count}] Skipped (too many duplicate attempts)")
    return articles


if __name__ == "__main__":
    import sys

    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"Generating {count} article(s)...")
    articles = generate_multiple(count)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "articles")
    os.makedirs(output_dir, exist_ok=True)

    for article in articles:
        filepath = os.path.join(output_dir, article["filename"])
        # Write with metadata header
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"<!-- Title: {article['title']} -->\n")
            f.write(f"<!-- Category: {article['category']} -->\n")
            f.write(f"<!-- Keywords: {', '.join(article['keywords'])} -->\n")
            f.write(f"<!-- Labels: {', '.join(article['labels'])} -->\n")
            f.write(f"<!-- Generated: {datetime.now().isoformat()} -->\n")
            f.write("\n")
            f.write(article["content"])

        print(f"  Saved: {filepath}")

    print(f"\nDone! {len(articles)} article(s) generated.")

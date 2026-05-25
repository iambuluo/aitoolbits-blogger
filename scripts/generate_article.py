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
                    "You write in pure HTML format without any markdown syntax."
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

    Strategy: insert ads after the first H2 section and at the end.
    This maximizes revenue without hurting readability.

    Args:
        content: Clean HTML article content
        provider: "monetag" or "adsense" or "none"
        zone_id: Ad zone ID (Monetag) or client ID (AdSense)

    Returns:
        HTML content with ads inserted
    """
    provider = provider or os.environ.get("AD_PROVIDER", "monetag")
    if provider == "none":
        return content

    zone_id = zone_id or os.environ.get("AD_ZONE_ID", "229646")

    if provider == "monetag":
        ad_code = f'<div style="margin:20px 0;text-align:center;"><script src="https://quge5.com/88/tag.min.js" data-zone="{zone_id}" async data-cfasync="false"></script></div>'
    elif provider == "adsense":
        client = zone_id  # For AdSense, zone_id stores the ca-pub-XXXX
        ad_code = f'<div style="margin:20px 0;text-align:center;"><ins class="adsbygoogle" style="display:block" data-ad-client="{client}" data-ad-slot="auto" data-ad-format="auto" data-full-width-responsive="true"></ins><script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script></div>'
    else:
        return content

    # Strategy: insert ad after first H2 section (after ~2-3 paragraphs)
    lines = content.split("\n")
    result_lines = []
    h2_count = 0
    inserted_first = False

    for line in lines:
        result_lines.append(line)
        if line.strip().startswith("<h2") and not inserted_first:
            h2_count += 1
            # Insert ad after the SECOND H2 (skip the intro, insert mid-article)
            if h2_count >= 2:
                result_lines.append("")
                result_lines.append(ad_code)
                result_lines.append("")
                inserted_first = True

    content_with_first_ad = "\n".join(result_lines)

    # Always add footer ad
    return content_with_first_ad + "\n\n" + ad_code


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
        "labels": [topic["category"], *[k.split()[0] for k in topic["keywords"][:2]]],
        "filename": filename,
    }


def generate_multiple(count: int = 1, api_key: str = None) -> list:
    """Generate multiple articles."""
    articles = []
    used_titles = set()
    for i in range(count):
        for _ in range(10):  # Max 10 retries to avoid duplicate titles
            article = generate_article(api_key)
            if article["title"] not in used_titles:
                used_titles.add(article["title"])
                articles.append(article)
                print(f"  [{i+1}/{count}] Done: {article['filename']}")
                break
        else:
            print(f"  [{i+1}/{count}] Skipped (duplicate title)")
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

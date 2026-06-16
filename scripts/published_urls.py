"""
Published articles tracker - prevents duplicate content generation.

This module tracks all published article URLs and titles to ensure
future article generation doesn't produce duplicate content.

Usage:
    python published_urls.py                  # List all published URLs
    python published_urls.py --update-url URL  # Add a new published URL
    python published_urls.py --remove URL      # Remove a URL
"""

import json
import os
import sys
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "published_urls.json"


def load_published_urls() -> dict:
    """Load published URLs database from JSON file."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"urls": [], "updated_at": None}


def save_published_urls(data: dict):
    """Save published URLs database to JSON file."""
    os.makedirs(DATA_FILE.parent, exist_ok=True)
    data["updated_at"] = __import__("datetime").datetime.now().isoformat()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _normalize_title(title: str) -> str:
    """Normalize a title for duplicate detection.
    
    Strips star counts, version numbers, and other volatile data
    to detect semantically identical articles.
    """
    import re
    
    # Lowercase
    t = title.lower().strip()
    
    # Strip star count patterns: "1,000+ Stars", "500 stars", "Gaining 1,200+ Stars"
    t = re.sub(r',?\d+(?:,\d+)*\+?\s*(?:stars?|star|stargazer)', '', t)
    t = re.sub(r'v\d+(?:\.\d+)*', 'vX', t)  # Version numbers -> vX
    
    # Strip "This Week" variations
    t = re.sub(r'in?\s*(the\s+)?past\s+\d+\s+days?', 'recently', t)
    t = re.sub(r'\bthis\s+week\b', 'this week', t)
    
    # Strip punctuation and extra whitespace
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    
    return t


def check_if_duplicate(title: str) -> dict:
    """Check if a title would duplicate any previously published article."""
    db = load_published_urls()
    
    normalized_title = _normalize_title(title)
    
    for item in db["urls"]:
        pub_title = item.get("title", "")
        url = item.get("url", "")
        normalized_pub = _normalize_title(pub_title)
        
        # Skip empty
        if not normalized_pub:
            continue
        
        # Exact match after normalization
        if normalized_title == normalized_pub:
            return {"duplicate": True, "match_type": "normalized_exact", "matched_url": url, "matched_title": pub_title}
        
        # If the core phrase matches (e.g. "ECC: The AI Repo" == "ECC: The AI Repo"), it's a duplicate
        # Extract first meaningful word sequence (first 5 words or first 40 chars)
        title_words = normalized_title.split()[:5]
        pub_words = normalized_pub.split()[:5]
        
        if title_words == pub_words and len(title_words) >= 3:
            return {"duplicate": True, "match_type": "core_match", "matched_url": url, "matched_title": pub_title}
        
        # GitHub trending pattern: if both contain same repo name + "repo" + similar length
        if "repo" in normalized_title and "repo" in normalized_pub:
            # Extract repo name (word before "repo")
            title_parts = normalized_title.split()
            pub_parts = normalized_pub.split()
            
            title_repo = None
            pub_repo = None
            
            for i, w in enumerate(title_parts):
                if w == "repo" and i > 0:
                    title_repo = title_parts[i-1].lower()
                    break
            
            for i, w in enumerate(pub_parts):
                if w == "repo" and i > 0:
                    pub_repo = pub_parts[i-1].lower()
                    break
            
            if title_repo and pub_repo and title_repo == pub_repo:
                return {"duplicate": True, "match_type": "repo_match", "matched_url": url, "matched_title": pub_title}
    
    return {"duplicate": False, "matched_url": None, "matched_title": None}


def add_published_url(title: str, url: str):
    """Add a new published URL to the database."""
    db = load_published_urls()
    
    # Check for duplicates first
    dup_check = check_if_duplicate(title)
    if dup_check["duplicate"]:
        print(f"⚠️  DUPLICATE DETECTED!")
        print(f"   Title: {title}")
        print(f"   Matches: {dup_check['matched_title']}")
        print(f"   URL: {dup_check['matched_url']}")
    
    # Add to database
    db["urls"].append({"url": url, "title": title})
    save_published_urls(db)
    print(f"✅ Added: {title}")
    print(f"   URL: {url}")


def remove_published_url(url: str):
    """Remove a published URL from the database."""
    db = load_published_urls()
    db["urls"] = [item for item in db["urls"] if item["url"] != url]
    save_published_urls(db)
    print(f"✅ Removed: {url}")


def list_all_published():
    """List all published URLs."""
    db = load_published_urls()
    print(f"\nPublished Articles: {len(db['urls'])} total\n")
    print(f"{'URL':<80} {'Title':<60}")
    print("-" * 140)
    
    for item in sorted(db["urls"], key=lambda x: x["url"], reverse=True)[:50]:
        url = item["url"]
        title = item["title"][:60] + "..." if len(item["title"]) > 60 else item["title"]
        print(f"{url:<80} {title:<60}")
    
    if len(db["urls"]) > 50:
        print(f"\n... and {len(db['urls']) - 50} more")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python published_urls.py                    # List all published URLs")
        print("  python published_urls.py --update-url URL    # Add a new URL")
        print("  python published_urls.py --remove URL        # Remove a URL")
        print("  python published_urls.py --check TITLE       # Check for duplicates")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_all_published()
    elif sys.argv[1] == "--check":
        title = " ".join(sys.argv[2:])
        dup_check = check_if_duplicate(title)
        if dup_check["duplicate"]:
            print(f"\n⚠️  DUPLICATE DETECTED!")
            print(f"   Title: {title}")
            print(f"   Match Type: {dup_check['match_type']}")
            print(f"   Matches: {dup_check['matched_title']}")
            print(f"   URL: {dup_check['matched_url']}")
        else:
            print(f"\n✅ No duplicate found for: {title}")
    elif sys.argv[1] == "--update-url":
        if len(sys.argv) < 4:
            print("Usage: python published_urls.py --update-url URL TITLE")
            sys.exit(1)
        url = sys.argv[2]
        title = " ".join(sys.argv[3:])
        add_published_url(title=title, url=url)
    elif sys.argv[1] == "--remove":
        url = sys.argv[2]
        remove_published_url(url=url)
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Try: python published_urls.py --help")

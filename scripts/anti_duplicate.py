"""
Anti-duplicate content checker for aitoolbits.blogspot.com.

Prevents generating duplicate or near-duplicate content by checking
against previously published articles.

Usage:
    python anti_duplicate.py TITLE CONTENT
"""

import sys
from pathlib import Path
import re

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from published_urls import load_published_urls, check_if_duplicate


def check_content_against_topics(title: str, content: str) -> dict:
    """
    Check if the new content would duplicate existing published articles.
    
    Returns:
        dict with 'duplicate' (bool) and 'reasons' (list of strings)
    """
    reasons = []
    
    # Check 1: Title exact match
    dup_check = check_if_duplicate(title)
    if dup_check["duplicate"]:
        reasons.append(f"Title matches existing article: {dup_check['matched_title']}")
    
    # Check 2: GitHub repo pattern detection
    if "GitHub" in title or "repo" in title.lower() or "stars" in title.lower():
        # Check if this is about a specific GitHub repository
        patterns = [
            r"gaining\s+\d[\d,]+\s+stars",
            r"getting\s+\d[\d,]+\s+stars",
            r"repo.*\d[\d,]+\s+stars",
        ]
        for pattern in patterns:
            if re.search(pattern, title.lower()):
                reasons.append(f"GitHub Trending pattern detected: '{title}'")
    
    # Check 3: Similar length + same keywords
    db = load_published_urls()
    title_lower = title.lower()
    keywords = set(re.findall(r'\b\w{5,}\b', title_lower))  # Words 5+ chars
    
    for item in db["urls"]:
        existing_title = item["title"].lower()
        existing_keywords = set(re.findall(r'\b\w{5,}\b', existing_title))
        
        # High keyword overlap = likely duplicate
        if len(keywords) > 0 and len(existing_keywords) > 0:
            overlap = len(keywords & existing_keywords) / len(keywords)
            if overlap > 0.6:  # 60%+ keyword overlap
                reasons.append(f"High keyword overlap with: {item['title']}")
    
    return {
        "duplicate": len(reasons) > 0,
        "reasons": reasons,
    }


def check_for_github_trending_patterns(title: str) -> bool:
    """
    Check if a title matches GitHub Trending pattern.
    
    These patterns are inherently low-quality duplicates and should be avoided.
    """
    patterns = [
        r"gaining\s+\d[\d,]*\s+stars",
        r"getting\s+\d[\d,]*\s+stars",
        r"\d[\d,]*\+\s+stars",
        r"repo.*star",
        r"github.*repo.*star",
    ]
    
    for pattern in patterns:
        if re.search(pattern, title.lower()):
            return True
    
    return False


def recommend_action(title: str, content: str) -> str:
    """
    Recommend whether to publish, skip, or revise the article.
    """
    result = check_content_against_topics(title, content)
    
    if result["duplicate"]:
        return f"SKIP - Reasons: {'; '.join(result['reasons'])}"
    
    # Check for GitHub Trending pattern
    if check_for_github_trending_patterns(title):
        return "REVISE - Avoid GitHub Trending patterns (low quality, duplicates)"
    
    return "PUBLISH - No duplicates detected"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python anti_duplicate.py TITLE CONTENT")
        sys.exit(1)
    
    title = sys.argv[1]
    content = " ".join(sys.argv[2:])
    
    recommendation = recommend_action(title, content)
    print(f"\nTitle: {title}")
    print(f"Recommendation: {recommendation}")

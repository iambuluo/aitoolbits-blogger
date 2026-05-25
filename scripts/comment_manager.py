"""
Blogger comment management tool.
Auto-cleanup spam comments and monitor blog comments.

Usage:
    python comment_manager.py stats          # View comment statistics
    python comment_manager.py cleanup         # Delete all spam comments
    python comment_manager.py list            # List recent comments
"""

import os
import json
import urllib.request
import urllib.error
import ssl
from datetime import datetime


def list_comments(access_token: str, blog_id: str, status: str = None,
                  max_results: int = 50, page_token: str = None) -> dict:
    """List comments from the blog.

    Args:
        access_token: Valid OAuth access token
        blog_id: Blogger blog ID
        status: Filter by status: "live", "pending", "spam", or None (all)
        max_results: Max comments to fetch per page (default 50)
        page_token: Pagination token for next page

    Returns:
        dict with keys: comments (list), total_count (int), next_page_token (str or None)
    """
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/comments"
    params = [f"maxResults={max_results}"]
    if status:
        params.append(f"status={status}")
    if page_token:
        params.append(f"pageToken={page_token}")
    url += "?" + "&".join(params)

    headers = {"Authorization": f"Bearer {access_token}"}
    req = urllib.request.Request(url, headers=headers)

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            error_msg = e.read().decode("utf-8") if e.fp else error_msg
        return {"comments": [], "total_count": 0, "error": error_msg}

    comments = []
    for item in data.get("items", []):
        comments.append({
            "id": item.get("id"),
            "post_id": item.get("postId") or item.get("inReplyTo", {}).get("id"),
            "author": item.get("author", {}).get("displayName", "Anonymous"),
            "content": item.get("content", "")[:200],
            "status": item.get("status", "unknown"),
            "published": item.get("published", ""),
            "url": item.get("selfLink", ""),
        })

    return {
        "comments": comments,
        "total_count": len(comments),
        "next_page_token": data.get("nextPageToken"),
    }


def delete_comment(access_token: str, blog_id: str, post_id: str,
                   comment_id: str) -> bool:
    """Delete a specific comment.

    Args:
        access_token: Valid OAuth access token
        blog_id: Blogger blog ID
        post_id: Post ID the comment belongs to
        comment_id: Comment ID to delete

    Returns:
        True if deleted successfully
    """
    url = (f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}"
           f"/posts/{post_id}/comments/{comment_id}")
    headers = {"Authorization": f"Bearer {access_token}"}
    req = urllib.request.Request(url, headers=headers, method="DELETE")

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.status < 400
    except urllib.error.HTTPError as e:
        if e.code == 204 or e.code == 200:
            return True
        print(f"  Failed to delete comment {comment_id}: HTTP {e.code}")
        return False
    except Exception as e:
        print(f"  Failed to delete comment {comment_id}: {e}")
        return False


def delete_spam_comments(access_token: str, blog_id: str,
                         dry_run: bool = False) -> dict:
    """Find and delete all spam comments.

    Args:
        access_token: Valid OAuth access token
        blog_id: Blogger blog ID
        dry_run: If True, only list spam without deleting

    Returns:
        dict with keys: found (int), deleted (int), failed (int)
    """
    print("Scanning for spam comments...")
    stats = {"found": 0, "deleted": 0, "failed": 0}

    page_token = None
    while True:
        result = list_comments(access_token, blog_id, status="spam", page_token=page_token)
        if result.get("error"):
            print(f"  Error: {result['error']}")
            break

        spam_comments = result["comments"]
        if not spam_comments:
            break

        stats["found"] += len(spam_comments)

        for comment in spam_comments:
            comment_id = comment["id"]
            post_id = comment["post_id"]
            author = comment["author"]
            preview = comment["content"][:80].replace("\n", " ")

            if dry_run:
                print(f"  [DRY RUN] Would delete: {comment_id} by {author}")
                print(f"             \"{preview}\"")
            else:
                # Validate post_id before deleting
                if not post_id:
                    print(f"  Skipped {comment_id}: missing post_id")
                    stats["failed"] += 1
                    continue

                success = delete_comment(access_token, blog_id, post_id, comment_id)
                if success:
                    stats["deleted"] += 1
                    print(f"  Deleted: {comment_id} by {author} - \"{preview}\"")
                else:
                    stats["failed"] += 1

        page_token = result.get("next_page_token")
        if not page_token:
            break

    return stats


def get_comment_stats(access_token: str, blog_id: str) -> dict:
    """Get comment statistics for the blog.

    Returns:
        dict with keys: live, pending, spam, total
    """
    stats = {}
    for status in ["live", "pending", "spam"]:
        result = list_comments(access_token, blog_id, status=status, max_results=1)
        # The API doesn't return total count, so we need to paginate
        count = 0
        page_token = None
        while True:
            result = list_comments(access_token, blog_id, status=status,
                                   max_results=50, page_token=page_token)
            count += result["total_count"]
            page_token = result.get("next_page_token")
            if not page_token or not result["comments"]:
                break
            if count > 500:  # Safety limit
                count = 500
                break
        stats[status] = count

    stats["total"] = stats["live"] + stats["pending"] + stats["spam"]
    return stats


def print_comment_stats(stats: dict):
    """Pretty-print comment statistics."""
    print("\n" + "=" * 45)
    print("  Blog Comment Statistics")
    print("=" * 45)
    print(f"  Live (published):    {stats.get('live', 0):>5}")
    print(f"  Pending (moderation): {stats.get('pending', 0):>5}")
    print(f"  Spam:                {stats.get('spam', 0):>5}")
    print("-" * 45)
    print(f"  Total:               {stats.get('total', 0):>5}")
    print("=" * 45)


def run_comment_cleanup(blog_id: str = None):
    """Main entry point for comment cleanup in GitHub Actions."""
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")
    blog_id = blog_id or os.environ.get("BLOGGER_BLOG_ID")

    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("Skipping comment cleanup: missing credentials")
        return

    # Get access token
    from publish_to_blogger import get_access_token
    access_token = get_access_token(client_id, client_secret, refresh_token)

    # Clean spam
    stats = delete_spam_comments(access_token, blog_id, dry_run=False)

    if stats["found"] > 0:
        print(f"\nComment cleanup: {stats['deleted']}/{stats['found']} spam deleted"
              f" ({stats['failed']} failed)")
    else:
        print("Comment cleanup: no spam found")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]

    # Load credentials
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing Blogger credentials. Set environment variables:")
        print("  BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET,")
        print("  BLOGGER_REFRESH_TOKEN, BLOGGER_BLOG_ID")
        sys.exit(1)

    from publish_to_blogger import get_access_token
    access_token = get_access_token(client_id, client_secret, refresh_token)

    if command == "stats":
        stats = get_comment_stats(access_token, blog_id)
        print_comment_stats(stats)

    elif command == "cleanup":
        dry_run = "--dry-run" in sys.argv
        if dry_run:
            print("DRY RUN MODE - no comments will be deleted\n")
        stats = delete_spam_comments(access_token, blog_id, dry_run=dry_run)
        print(f"\n{'Would delete' if dry_run else 'Deleted'}: "
              f"{stats['deleted']}/{stats['found']} spam comments"
              f" ({stats['failed']} failed)")

    elif command == "list":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        result = list_comments(access_token, blog_id, status=status_filter)
        print(f"\nRecent comments ({result['total_count']} found):")
        print("-" * 60)
        for c in result["comments"]:
            date = c["published"][:10] if c["published"] else "N/A"
            status_icon = {"live": "✓", "pending": "⏳", "spam": "✗"}.get(
                c["status"], "?")
            preview = c["content"][:100].replace("<", "&lt;").replace("\n", " ")
            print(f"  [{status_icon}] {date} | {c['author']}: \"{preview}\"")

    elif command == "auto-cleanup":
        # Designed for GitHub Actions - silent unless spam found
        run_comment_cleanup()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

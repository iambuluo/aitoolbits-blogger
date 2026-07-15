"""
Fix original articles: upload Agnes images via Blogger image API
(so they get a blogger.googleusercontent.com URL that Blogger keeps),
then PATCH the already-published posts to use those URLs.

Why: Blogger's posts.insert / PATCH strips external <img> hosts like
jsDelivr, but keeps images hosted on blogger.googleusercontent.com.
The 80 other articles use Pexels URLs (also kept); our 2 originals used
jsDelivr and were stripped. This script uploads locally-committed PNGs to
Blogger and rewrites the post content with the returned URLs.

Run on GitHub Actions (server can reach Google).
"""
import os
import sys
import json
import base64
import ssl
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish_to_blogger import get_access_token, _try_auto_save_refresh_token

BASE = Path(__file__).parent.parent
BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"
CTX = ssl.create_default_context()

# jsDelivr URL (currently in HTML) -> local PNG path (committed in repo)
IMG_MAP = {
    "https://cdn.jsdelivr.net/gh/iambuluo/aitoolbits-blogger@main/images/bg_cover.png":
        "images/bg_cover.png",
    "https://cdn.jsdelivr.net/gh/iambuluo/aitoolbits-blogger@main/images/bg_inline.png":
        "images/bg_inline.png",
    "https://cdn.jsdelivr.net/gh/iambuluo/aitoolbits-blogger@main/images/pipe_cover.png":
        "images/pipe_cover.png",
    "https://cdn.jsdelivr.net/gh/iambuluo/aitoolbits-blogger@main/images/pipe_inline.png":
        "images/pipe_inline.png",
}

# Article file -> published post title prefix (to locate the post)
ARTICLES = {
    "original_i_tested_10_bg_removers.html": "I Ran the Same Photo Through 10",
    "original_my_ai_writing_pipeline.html": "My AI Writing Pipeline",
}


def upload_image(token, blog_id, post_id, png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    url = f"{BLOGGER_API}/{blog_id}/posts/{post_id}/images"
    req = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps({"data": b64}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return json.loads(r.read().decode()).get("url")


def get_all_posts(token, blog_id):
    posts = []
    page_token = None
    while True:
        url = f"{BLOGGER_API}/{blog_id}/posts?maxResults=500&status=live&fetchBodies=false"
        if page_token:
            url += f"&pageToken={page_token}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
            data = json.loads(r.read().decode())
        posts.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return posts


def patch_post(token, blog_id, post_id, content):
    url = f"{BLOGGER_API}/{blog_id}/posts/{post_id}?revertDraft=false"
    req = urllib.request.Request(
        url,
        method="PATCH",
        data=json.dumps({"content": content}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return json.loads(r.read().decode())


def main():
    # Idempotency guard: if no jsDelivr URLs remain in any article HTML,
    # the fix was already applied (Blogger post patched) — skip re-upload.
    remaining = 0
    for fn in ARTICLES:
        try:
            html = (BASE / "articles" / fn).read_text(encoding="utf-8")
            remaining += html.count("jsdelivr.net")
        except FileNotFoundError:
            pass
    if remaining == 0:
        print("No jsDelivr URLs found in article HTML — images already fixed. Skipping.")
        return

    cid = os.environ["BLOGGER_CLIENT_ID"]
    csec = os.environ["BLOGGER_CLIENT_SECRET"]
    rtk = os.environ["BLOGGER_REFRESH_TOKEN"]
    bid = os.environ["BLOGGER_BLOG_ID"]

    token = get_access_token(cid, csec, rtk, on_new_refresh=_try_auto_save_refresh_token)
    posts = get_all_posts(token, bid)

    for fn, prefix in ARTICLES.items():
        art = [p for p in posts if p["title"].startswith(prefix)]
        if not art:
            print(f"WARN: published post not found for {fn} (prefix={prefix!r})")
            continue
        post_id = art[0]["id"]
        html = (BASE / "articles" / fn).read_text(encoding="utf-8")

        for jsurl, local in IMG_MAP.items():
            if jsurl in html:
                gu = upload_image(token, bid, post_id, BASE / local)
                print(f"  uploaded {local} -> {gu}")
                html = html.replace(jsurl, gu)

        patch_post(token, bid, post_id, html)
        print(f"PATCHED {fn} (post {post_id}); jsdelivr left: "
              f"{html.count('jsdelivr.net')}")


if __name__ == "__main__":
    main()

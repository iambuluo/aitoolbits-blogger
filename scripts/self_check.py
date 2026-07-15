"""
AdSense Readiness Self-Check (real audit, runs on GitHub Actions).

Verifies live blog state:
1. Trust/policy pages (About/Contact/Disclaimer/Privacy)
2. No duplicate post titles
3. Original articles published (by ENGLISH title + "Original" label)
4. Content-quality: thin-post ratio, image coverage, Original-label count

Run via GitHub Actions (can't access Google from mainland China).
"""
import os
import sys
import json
import re
import ssl
import urllib.request
import urllib.parse
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish_to_blogger import get_access_token, _try_auto_save_refresh_token

BASE_DIR = Path(__file__).parent.parent
CTX = ssl.create_default_context()
BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"

THIN_WORDS = 350
TARGET_ORIGINALS = [
    "i ran the same photo through 10 ai background removers",
    "my ai writing pipeline",
]


def load_credentials():
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "")
    if not all([client_id, client_secret, refresh_token, blog_id]):
        tokens_path = BASE_DIR / "blogger_tokens.json"
        if tokens_path.exists():
            with open(tokens_path, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = client_id or tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = client_secret or tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = refresh_token or tokens.get("BLOGGER_REFRESH_TOKEN", "")
            blog_id = blog_id or tokens.get("BLOGGER_BLOG_ID", "")
    return client_id, client_secret, refresh_token, blog_id


def get_all_posts(access_token, blog_id):
    all_posts = []
    page_token = None
    api_base = f"{BLOGGER_API}/{blog_id}/posts"
    for _ in range(10):
        params = {"maxResults": "500", "status": "live"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{api_base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {access_token}")
        try:
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                all_posts.extend(data.get("items", []))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"  Error fetching posts: {e}")
            break
    return all_posts


def get_all_pages(access_token, blog_id):
    pages = []
    page_token = None
    api_base = f"{BLOGGER_API}/{blog_id}/pages"
    for _ in range(5):
        params = {"maxResults": "100"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{api_base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {access_token}")
        try:
            with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages.extend(data.get("items", []))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        except Exception as e:
            print(f"  Error fetching pages: {e}")
            break
    return pages


def _strip(html):
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def _wc(html):
    t = _strip(html)
    words = re.findall(r"[A-Za-z0-9']+", t)
    cjk = re.findall(r"[\u4e00-\u9fff]", t)
    return max(len(words), len(cjk))


def main():
    print("=" * 64)
    print("  AdSense Readiness SELF-CHECK (real audit)")
    print("=" * 64)

    client_id, client_secret, refresh_token, blog_id = load_credentials()
    if not all([client_id, client_secret, refresh_token, blog_id]):
        print("ERROR: Missing credentials")
        sys.exit(1)

    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_try_auto_save_refresh_token,
    )

    # 1. Trust / policy pages
    print("\n[1] Trust / policy pages")
    pages = get_all_pages(access_token, blog_id)
    ptitles = {p.get("title", "").strip().lower() for p in pages}
    required = {"about": False, "contact": False, "disclaimer": False, "privacy": False}
    for t in ptitles:
        if "about" in t: required["about"] = True
        if "contact" in t: required["contact"] = True
        if "disclaimer" in t: required["disclaimer"] = True
        if "privacy" in t: required["privacy"] = True
    for k, v in required.items():
        print(f"  {'OK ' if v else 'MISS'} {k.capitalize()} page")
    pages_ok = all(required.values())

    # 2. Posts + quality
    print("\n[2] Live posts — content quality")
    posts = get_all_posts(access_token, blog_id)
    total = len(posts)
    wc = []
    thin = []
    with_img = 0
    orig_label = 0
    title_groups = defaultdict(list)
    for p in posts:
        html = p.get("content", "")
        w = _wc(html)
        wc.append(w)
        if w < THIN_WORDS:
            thin.append((p.get("title", ""), w))
        if "<img" in (html or ""):
            with_img += 1
        labels = [l.lower() for l in p.get("labels", [])]
        if "original" in labels:
            orig_label += 1
        title_groups[p.get("title", "").strip().lower()].append(p.get("title", ""))

    wc_sorted = sorted(wc)
    median = wc_sorted[len(wc_sorted)//2] if wc_sorted else 0
    avg = sum(wc)//total if total else 0
    thin_n = len(thin)
    print(f"  Total live posts         : {total}")
    print(f"  Median / avg words/post  : {median} / {avg}")
    print(f"  Thin posts (<{THIN_WORDS} words): {thin_n} ({100*thin_n//total if total else 0}%)")
    print(f"  Posts with >=1 image     : {with_img} ({100*with_img//total if total else 0}%)")
    print(f"  Posts labeled 'Original' : {orig_label}")

    # 3. Duplicate titles
    print("\n[3] Duplicate titles")
    dups = {k: v for k, v in title_groups.items() if len(v) > 1}
    print(f"  Exact-duplicate title groups: {len(dups)}")
    for k in list(dups)[:8]:
        print(f"    - {k[:55]} (x{len(dups[k])})")
    no_dupes = len(dups) == 0

    # 4. Target English originals
    print("\n[4] Target English original articles")
    found_originals = 0
    for t in TARGET_ORIGINALS:
        matches = [p for p in posts if t in p.get("title", "").strip().lower()]
        ok = bool(matches)
        has_img = any("<img" in (m.get("content", "")) for m in matches)
        w = _wc(matches[0].get("content", "")) if matches else 0
        print(f"  {'OK ' if ok else 'MISS'} {t[:45]!r} img={has_img} words={w}")
        if ok:
            found_originals += 1
        # DUMP raw content for ground-truth check
        if matches:
            c = matches[0].get("content", "")
            imgs = re.findall(r'<img[^>]*src="([^"]+)"', c)
            print(f"    -> raw <img> count: {len(imgs)}")
            for s in imgs[:3]:
                print(f"       src: {s[:90]}")
            if not imgs:
                print(f"    -> content head: {re.sub(r'\\s+',' ', c)[:160]}")
    orig_ok = found_originals == len(TARGET_ORIGINALS)

    # 5. VERDICT
    print("\n" + "=" * 64)
    print("  VERDICT")
    print("=" * 64)
    thin_ratio = 100*thin_n//total if total else 100
    print(f"  Trust/policy pages complete : {'PASS' if pages_ok else 'FAIL'}")
    print(f"  No duplicate titles         : {'PASS' if no_dupes else 'FAIL (%d)' % len(dups)}")
    print(f"  Target originals present    : {found_originals}/{len(TARGET_ORIGINALS)}")
    print(f"  Thin-content ratio          : {thin_ratio}%  (want <40%)")
    print(f"  Image coverage              : {100*with_img//total if total else 0}%")
    print(f"  Original-labeled posts      : {orig_label}  (want >=5)")

    structural_ok = pages_ok and no_dupes
    ready = structural_ok and thin_ratio < 40 and orig_ok and orig_label >= 5
    print("-" * 64)
    print(f"  READY TO APPLY? : {'YES (cautiously)' if ready else 'NO — not yet'}")
    if not ready:
        reasons = []
        if not pages_ok: reasons.append("trust/policy pages incomplete")
        if dups: reasons.append("duplicate titles exist")
        if thin_ratio >= 40: reasons.append(f"{thin_ratio}% of posts are thin (<{THIN_WORDS} words)")
        if not orig_ok: reasons.append("target originals missing")
        if orig_label < 5: reasons.append(f"only {orig_label} Original-labeled posts")
        print("  Blockers:")
        for r in reasons:
            print(f"    - {r}")
    print("=" * 64)

    # Do NOT hard-fail the workflow on quality heuristics; just report.
    # (Previous version exited(1) on stale Chinese-title checks — removed.)


if __name__ == "__main__":
    main()

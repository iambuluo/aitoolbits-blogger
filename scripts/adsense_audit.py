"""
AdSense Readiness AUDIT — runs on GitHub Actions (can reach Google/Blogger).

Does a REAL content-quality audit, not just surface checks:
  1. Trust pages (About/Contact/Disclaimer/Privacy)
  2. Live post count + word-count distribution (thin-content detection)
  3. Duplicate / near-duplicate title clusters
  4. How many posts carry the "Original" label (genuine first-hand content)
  5. The 2 target English original articles present? with images?
  6. Honest AdSense-readiness verdict with hard numbers.

Run via GitHub Actions (mainland can't reach Google).
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

THIN_WORDS = 350          # below this = likely thin/low-value
TARGET_ORIGINALS = [
    "i ran the same photo through 10 ai background removers",
    "my ai writing pipeline",
]


def strip_html(html):
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def word_count(html):
    text = strip_html(html)
    # count words; for cjk-heavy text fall back to char count
    words = re.findall(r"[A-Za-z0-9']+", text)
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    return max(len(words), len(cjk))


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
    posts = []
    page_token = None
    api_base = f"{BLOGGER_API}/{blog_id}/posts"
    for _ in range(20):
        params = {"maxResults": "500", "status": "live", "fetchBodies": "true"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{api_base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
        try:
            with urllib.request.urlopen(req, timeout=60, context=CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            posts.extend(data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        except Exception as e:
            print(f"  Error fetching posts: {e}")
            break
    return posts


def get_all_pages(access_token, blog_id):
    pages = []
    page_token = None
    api_base = f"{BLOGGER_API}/{blog_id}/pages"
    for _ in range(5):
        params = {"maxResults": "100"}
        if page_token:
            params["pageToken"] = page_token
        url = f"{api_base}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
        try:
            with urllib.request.urlopen(req, timeout=60, context=CTX) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages.extend(data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        except Exception as e:
            print(f"  Error fetching pages: {e}")
            break
    return pages


def main():
    print("=" * 64)
    print("  AdSense READINESS AUDIT (real content-quality check)")
    print("=" * 64)

    cid, csec, rtk, bid = load_credentials()
    if not all([cid, csec, rtk, bid]):
        print("ERROR: Missing credentials"); sys.exit(1)

    at = get_access_token(cid, csec, rtk, on_new_refresh=_try_auto_save_refresh_token)

    # ---- 1. Trust pages ----
    print("\n[1] Trust / policy pages")
    pages = get_all_pages(at, bid)
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

    # ---- 2. Posts ----
    print("\n[2] Live posts — content quality")
    posts = get_all_posts(at, bid)
    total = len(posts)
    wc = []
    thin = []
    with_img = 0
    orig_label = 0
    title_groups = defaultdict(list)
    for p in posts:
        html = p.get("content", "")
        w = word_count(html)
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
    print(f"  Total live posts     : {total}")
    print(f"  Median words/post    : {median}")
    print(f"  Average words/post   : {avg}")
    print(f"  Posts < {THIN_WORDS} words (thin): {thin_n} ({100*thin_n//total if total else 0}%)")
    print(f"  Posts with >=1 image : {with_img} ({100*with_img//total if total else 0}%)")
    print(f"  Posts labeled Original: {orig_label}")

    # ---- 3. Duplicate titles ----
    print("\n[3] Duplicate / near-duplicate titles")
    dups = {k: v for k, v in title_groups.items() if len(v) > 1}
    print(f"  Exact duplicate title groups: {len(dups)}")
    for k in list(dups)[:10]:
        print(f"    - {k[:55]} (x{len(dups[k])})")

    # ---- 4. Target originals ----
    print("\n[4] Target English original articles")
    ptitles_lower = [p.get("title", "").strip().lower() for p in posts]
    found_originals = 0
    for t in TARGET_ORIGINALS:
        matches = [p for p in posts if t in p.get("title", "").strip().lower()]
        ok = bool(matches)
        has_img = any("<img" in (m.get("content","")) for m in matches)
        w = word_count(matches[0].get("content","")) if matches else 0
        print(f"  {'OK ' if ok else 'MISS'} {t[:45]!r}  img={has_img} words={w}")
        if ok:
            found_originals += 1

    # ---- 5. VERDICT ----
    print("\n" + "=" * 64)
    print("  VERDICT")
    print("=" * 64)
    print(f"  Trust pages complete      : {'PASS' if pages_ok else 'FAIL'}")
    print(f"  No exact-duplicate titles : {'PASS' if not dups else 'FAIL (%d groups)' % len(dups)}")
    print(f"  Target originals present  : {found_originals}/{len(TARGET_ORIGINALS)}")
    print(f"  Thin-content ratio        : {100*thin_n//total if total else 0}%  (lower is better)")
    print(f"  Image coverage            : {100*with_img//total if total else 0}%")
    print(f"  Original-labeled posts    : {orig_label}")

    # Heuristic readiness: structural OK + thin ratio < 40% + enough originals
    structural_ok = pages_ok and not dups
    thin_ratio = 100*thin_n//total if total else 100
    ready = structural_ok and thin_ratio < 40 and found_originals == len(TARGET_ORIGINALS) and orig_label >= 5
    print("-" * 64)
    print(f"  READY TO APPLY? : {'YES (cautiously)' if ready else 'NO — not yet'}")
    if not ready:
        reasons = []
        if not pages_ok: reasons.append("trust/policy pages incomplete")
        if dups: reasons.append("duplicate titles exist")
        if thin_ratio >= 40: reasons.append(f"{thin_ratio}% of posts are thin (<{THIN_WORDS} words)")
        if found_originals != len(TARGET_ORIGINALS): reasons.append("target originals missing")
        if orig_label < 5: reasons.append(f"only {orig_label} Original-labeled posts (need more genuine content)")
        print("  Reasons not ready:")
        for r in reasons:
            print(f"    - {r}")
    print("=" * 64)


if __name__ == "__main__":
    main()

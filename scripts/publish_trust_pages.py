"""
Publish Trust Pages (About, Contact, Disclaimer) to Blogger.
Uses Blogger Pages API (separate from blog posts).

These pages address AdSense "low value content" rejection by providing
real site identity, contactability, and accountability signals.

Usage:
    python scripts/publish_trust_pages.py
"""
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publish_to_blogger import get_access_token, _try_auto_save_refresh_token


# ==================== About Page HTML ====================

ABOUT_HTML = """
<div style="max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; font-size: 16px; color: #333;">

<h2>About AI Tool Bits</h2>

<p>Hi, I'm <strong>dengf</strong> — an independent developer and AI tools enthusiast behind <strong>AI Tool Bits</strong>.</p>

<p>I started this site in 2026 because I was spending hours every week testing AI writing tools, image generators, coding assistants, and productivity apps. There were plenty of "Top 10 Best AI Tools" listicles out there, but most felt hollow — written by people who clearly hadn't actually used the tools they were ranking. I wanted a place where the reviews came from <em>real, repeated hands-on use</em>, not from scraping a vendor's homepage.</p>

<h3>What You'll Find Here</h3>
<ul>
<li><strong>Honest tool comparisons</strong> — I put competing tools side by side and actually run the same task through each one.</li>
<li><strong>Field-tested tutorials</strong> — Step-by-step guides based on workflows I use myself.</li>
<li><strong>Industry observations</strong> — Occasionally I write about where the AI tooling space is heading, based on what I see building and shipping software.</li>
</ul>

<h3>My Background</h3>
<p>I've been building software for over a decade — currently focused on WordPress plugins, desktop utilities, and AI-assisted automation. I run multiple side projects and care a lot about tools that genuinely save time rather than adding noise. When a tool earns a recommendation here, it's because I reached for it again the next day.</p>

<h3>How I Test</h3>
<p>Every tool reviewed on this site goes through the same process:</p>
<ol>
<li>I sign up with a real account (free or paid).</li>
<li>I run 3+ real tasks that a typical user would run.</li>
<li>I note what broke, what surprised me, and what I'd change.</li>
<li>I update the post when the tool changes significantly.</li>
</ol>

<p>The goal is simple: if you're deciding between two AI tools and you read my comparison, you should be able to make the call without opening either one. That's the bar I hold myself to.</p>

<h3>A Note on This Site</h3>
<p>AI Tool Bits is hosted on Blogger (Google's platform) and is supported by display advertising and, in some cases, affiliate links to the tools I cover. Affiliate relationships never affect what I recommend — a tool has to earn its spot first. See the <a href="/p/disclaimer.html">Disclaimer</a> for details.</p>

<p>Got a tool you think I should test? <a href="/p/contact.html">Get in touch</a> — I read every message.</p>

<p>— dengf</p>

</div>
"""


# ==================== Contact Page HTML ====================

CONTACT_HTML = """
<div style="max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; font-size: 16px; color: #333;">

<h2>Contact</h2>

<p>I personally read and respond to every message. If you have a question about a tool I've reviewed, a correction, a tool suggestion, or just want to say hi — reach out.</p>

<h3>Email</h3>
<p>The fastest way to reach me:</p>
<ul>
<li><strong>General &amp; tool suggestions:</strong> <a href="mailto:iambuluo@gmail.com">iambuluo@gmail.com</a></li>
</ul>

<h3>Social &amp; Code</h3>
<ul>
<li><strong>GitHub:</strong> <a href="https://github.com/iambuluo" target="_blank" rel="noopener">@iambuluo</a></li>
<li><strong>Project repo:</strong> <a href="https://github.com/iambuluo/aitoolbits-blogger" target="_blank" rel="noopener">aitoolbits-blogger</a></li>
</ul>

<h3>What to Expect</h3>
<ul>
<li><strong>Response time:</strong> Usually within 2–3 business days.</li>
<li><strong>Tool requests:</strong> I can't promise to review every suggestion, but I keep a running list and prioritize tools my readers ask about most.</li>
<li><strong>Corrections:</strong> If you spot an error in a post, tell me — I'd rather fix it than leave wrong info up.</li>
</ul>

<p>This is a one-person operation, so thanks for your patience. I genuinely appreciate every message.</p>

</div>
"""


# ==================== Disclaimer Page HTML ====================

DISCLAIMER_HTML = """
<div style="max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; font-size: 16px; color: #333;">

<h2>Disclaimer</h2>
<p>Last updated: July 15, 2026</p>

<p>This Disclaimer governs your use of <strong>AI Tool Bits</strong> (accessible at <a href="https://aitoolbits.blogspot.com">https://aitoolbits.blogspot.com</a>). By using this website, you agree to the terms below.</p>

<h3>1. Editorial Independence</h3>
<p>All reviews, comparisons, and recommendations on this site reflect the hands-on testing and opinions of the site owner. We are not affiliated with, sponsored by, or endorsed by most of the tools we cover unless explicitly stated. Tool rankings are based on actual usage, not payment.</p>

<h3>2. Affiliate Links</h3>
<p>Some articles on AI Tool Bits contain affiliate links. This means if you click a link to a tool and later sign up for a paid plan, we may earn a commission at no extra cost to you. This does not influence our reviews — a tool must earn a recommendation through genuine quality before any link is placed. We only join affiliate programs for tools we have personally used.</p>

<h3>3. No Warranties</h3>
<p>The information on this site is provided "as is" for general informational purposes. We make no warranties regarding accuracy, completeness, or reliability. AI tools change rapidly — features, pricing, and policies described in our posts may be outdated by the time you read them. Always verify current details on the tool's official website before making a purchase decision.</p>

<h3>4. External Links</h3>
<p>Our content may link to third-party websites. We are not responsible for the content, privacy practices, or availability of those external sites. Linking to a site does not imply endorsement of its content or views.</p>

<h3>5. Test Results May Vary</h3>
<p>AI tool outputs are non-deterministic. Your results with a tool may differ from what we describe due to model updates, prompt phrasing, account tier, or regional availability. Screenshots and examples shown in posts are from specific test sessions and may not exactly match what you see.</p>

<h3>6. Advertising</h3>
<p>This site displays advertisements served by Google AdSense and other third-party networks. Advertisers have no influence over editorial content. For details on advertising cookies, see our <a href="/p/privacy-policy.html">Privacy Policy</a>.</p>

<h3>7. Limitation of Liability</h3>
<p>To the fullest extent permitted by law, AI Tool Bits and its owner shall not be liable for any indirect, incidental, or consequential damages arising from your use of, or inability to use, this website or any tool mentioned on it.</p>

<h3>8. Contact</h3>
<p>Questions about this Disclaimer? Reach us at <a href="mailto:iambuluo@gmail.com">iambuluo@gmail.com</a> or via the <a href="/p/contact.html">Contact page</a>.</p>

</div>
"""


# ==================== Blogger Page API ====================

BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"


def publish_page(access_token: str, blog_id: str, title: str, content: str) -> dict:
    """Publish a standalone page (not a blog post) to Blogger."""
    import urllib.request
    import ssl

    url = f"{BLOGGER_API}/{blog_id}/pages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "kind": "blogger#page",
        "title": title,
        "content": content,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "page_id": result.get("id"),
                "url": result.get("url"),
                "title": title,
            }
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, "read"):
            error_msg = e.read().decode("utf-8") if e.fp else error_msg
        return {
            "success": False,
            "title": title,
            "error": error_msg,
        }


PAGES = [
    ("About", ABOUT_HTML),
    ("Contact", CONTACT_HTML),
    ("Disclaimer", DISCLAIMER_HTML),
]


def main():
    # Load credentials
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    if not client_id or not refresh_token:
        token_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "blogger_tokens.json"
        )
        if os.path.exists(token_file):
            with open(token_file, "r", encoding="utf-8") as f:
                tokens = json.load(f)
            client_id = client_id or tokens.get("BLOGGER_CLIENT_ID", "")
            client_secret = client_secret or tokens.get("BLOGGER_CLIENT_SECRET", "")
            refresh_token = refresh_token or tokens.get("BLOGGER_REFRESH_TOKEN", "")
            blog_id = blog_id or tokens.get("BLOGGER_BLOG_ID", "")

    missing = []
    if not client_id:
        missing.append("BLOGGER_CLIENT_ID")
    if not client_secret:
        missing.append("BLOGGER_CLIENT_SECRET")
    if not refresh_token:
        missing.append("BLOGGER_REFRESH_TOKEN")
    if not blog_id:
        missing.append("BLOGGER_BLOG_ID")

    if missing:
        print(f"ERROR: Missing credentials: {', '.join(missing)}")
        sys.exit(1)

    print("Authenticating with Blogger API...")

    def _handle_token_rotation(new_token: str):
        _try_auto_save_refresh_token(new_token)

    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_handle_token_rotation,
    )
    print("  Access token obtained.")

    results = []
    for title, html in PAGES:
        print(f"\nPublishing '{title}' page...")
        result = publish_page(
            access_token=access_token,
            blog_id=blog_id,
            title=title,
            content=html,
        )
        results.append(result)
        if result["success"]:
            print(f"  SUCCESS! URL: {result['url']} (ID: {result['page_id']})")
        else:
            print(f"  FAILED: {result['error']}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n=== Summary: {success_count}/{len(PAGES)} pages published ===")

    if success_count < len(PAGES):
        sys.exit(1)


if __name__ == "__main__":
    main()

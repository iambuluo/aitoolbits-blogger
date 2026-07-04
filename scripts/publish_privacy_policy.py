"""
Publish Privacy Policy page to Blogger.
Uses Blogger Pages API (separate from blog posts).

Usage:
    # Local (needs blogger_tokens.json)
    python scripts/publish_privacy_policy.py

    # GitHub Actions (env vars)
    python scripts/publish_privacy_policy.py
"""
import os
import json
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from publish_to_blogger import get_access_token, _try_auto_save_refresh_token


# ==================== Privacy Policy HTML ====================

PRIVACY_POLICY_HTML = """
<div style="max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; font-size: 16px; color: #333;">

<h2>Privacy Policy</h2>
<p>Last updated: July 4, 2026</p>

<p>At <strong>AI Tool Bits</strong> ("we," "us," or "our"), accessible from <a href="https://aitoolbits.blogspot.com">https://aitoolbits.blogspot.com</a>, we respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, and protect your information when you visit our website.</p>

<h3>1. Information We Collect</h3>
<p>We may collect the following types of information:</p>
<ul>
<li><strong>Personal Information:</strong> We do not directly collect personal information such as your name, email, or phone number unless you voluntarily provide it (e.g., by leaving a comment or contacting us).</li>
<li><strong>Non-Personal Information:</strong> We may collect non-personal information such as your browser type, device type, operating system, referring website, pages visited, and time spent on our site. This information is used for analytics and website improvement purposes.</li>
<li><strong>Log Data:</strong> Like most websites, our platform (Blogger) automatically collects log information including IP address, browser type, and access time when you visit our site.</li>
</ul>

<h3>2. How We Use Your Information</h3>
<p>We use the information we collect for the following purposes:</p>
<ul>
<li>To operate, maintain, and improve our website and content</li>
<li>To understand how visitors interact with our articles and features</li>
<li>To display relevant advertisements</li>
<li>To respond to your comments, questions, and feedback</li>
<li>To monitor and analyze trends, usage, and activities in connection with our website</li>
<li>To prevent fraudulent activity and abuse of our website</li>
</ul>

<h3>3. Cookies and Tracking Technologies</h3>
<p>Our website uses cookies and similar tracking technologies to track the activity on our site and store certain information. Cookies are files with a small amount of data which may include an anonymous unique identifier.</p>
<p>You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. If you do not accept cookies, some portions of our website may not function properly.</p>
<p>We use the following types of cookies:</p>
<ul>
<li><strong>Essential Cookies:</strong> Required for the website to function correctly.</li>
<li><strong>Analytics Cookies:</strong> Help us understand how visitors interact with our website.</li>
<li><strong>Advertising Cookies:</strong> Used to display personalized ads based on your interests.</li>
</ul>

<h3>4. Google AdSense and Third-Party Advertising</h3>
<p>We use <strong>Google AdSense</strong> to display advertisements on our website. Google AdSense is a service provided by Google LLC that uses cookies to serve ads based on your prior visits to this and other websites.</p>
<ul>
<li>Google uses cookies (including the <strong>DoubleClick DART cookie</strong>) to serve ads to our users based on their visit to our site and other sites on the Internet.</li>
<li>Users may opt out of the use of the DART cookie by visiting the <strong>Google Ads Settings page</strong>: <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">https://www.google.com/settings/ads</a></li>
<li>Third-party vendors, including Google, use cookies to serve ads based on a user's previous visits to our website or other websites.</li>
<li>Google's use of advertising cookies enables it and its partners to serve ads to our users based on their visit to our site and/or other sites on the Internet.</li>
</ul>
<p>For more information about how Google uses data, please visit: <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">Google's Partner Sites Policy</a></p>

<h3>5. Third-Party Links and Services</h3>
<p>Our website may contain links to third-party websites or services. We are not responsible for the privacy practices or the content of these third-party sites. We encourage you to review the privacy policies of any third-party sites you visit.</p>
<p>Third-party services we may use include:</p>
<ul>
<li><strong>Google Analytics:</strong> For website traffic analysis</li>
<li><strong>Google AdSense:</strong> For displaying advertisements</li>
<li><strong>Blogger (Google):</strong> Our hosting platform</li>
<li><strong>Social Media Plugins:</strong> Buttons or widgets from social media platforms</li>
</ul>

<h3>6. Data Security</h3>
<p>We take reasonable measures to protect your information from unauthorized access, alteration, disclosure, or destruction. However, no method of transmission over the Internet or method of electronic storage is 100% secure, and we cannot guarantee absolute security.</p>

<h3>7. Your Data Protection Rights</h3>
<p>Depending on your location, you may have the following rights regarding your personal data:</p>
<ul>
<li><strong>Right to Access:</strong> You can request copies of your personal data.</li>
<li><strong>Right to Rectification:</strong> You can request that we correct any information you believe is inaccurate or incomplete.</li>
<li><strong>Right to Erasure:</strong> You can request that we erase your personal data.</li>
<li><strong>Right to Restrict Processing:</strong> You can request that we restrict the processing of your personal data.</li>
<li><strong>Right to Object:</strong> You can object to our processing of your personal data.</li>
<li><strong>Right to Data Portability:</strong> You can request a copy of your data in a structured, machine-readable format.</li>
</ul>
<p>If you are in the European Economic Area (EEA) or the United Kingdom, you have rights under the <strong>General Data Protection Regulation (GDPR)</strong>. If you are in California, you have rights under the <strong>California Consumer Privacy Act (CCPA)</strong>.</p>
<p>To exercise any of these rights, please contact us using the information provided in the "Contact Us" section below.</p>

<h3>8. Children's Privacy</h3>
<p>Our website is not directed to children under the age of 13. We do not knowingly collect personal information from children under 13. If you are a parent or guardian and believe your child has provided us with personal information, please contact us so we can take appropriate action to delete such information.</p>

<h3>9. Do Not Track Signals</h3>
<p>Some browsers offer a "Do Not Track" feature. Our website does not currently respond to "Do Not Track" signals, as there is no industry consensus on what "Do Not Track" means. However, you can opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener">Google Ads Settings</a> or <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener">AboutAds Choices</a>.</p>

<h3>10. Changes to This Privacy Policy</h3>
<p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last updated" date at the top. You are advised to review this Privacy Policy periodically for any changes.</p>

<h3>11. Consent</h3>
<p>By using our website, you hereby consent to our Privacy Policy and agree to its terms.</p>

<h3>12. Contact Us</h3>
<p>If you have any questions or concerns about this Privacy Policy, please contact us at:</p>
<ul>
<li>Email: <a href="mailto:iambuluo@gmail.com">iambuluo@gmail.com</a></li>
<li>Website: <a href="https://aitoolbits.blogspot.com">https://aitoolbits.blogspot.com</a></li>
<li>GitHub: <a href="https://github.com/iambuluo/aitoolbits-blogger" target="_blank" rel="noopener">https://github.com/iambuluo/aitoolbits-blogger</a></li>
</ul>

</div>
"""


# ==================== Blogger Page API ====================

BLOGGER_API = "https://www.googleapis.com/blogger/v3/blogs"


def publish_page(access_token: str, blog_id: str, title: str, content: str) -> dict:
    """Publish a standalone page (not a blog post) to Blogger.
    
    Uses the Blogger Pages API.
    """
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


def main():
    # Load credentials
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    # Fallback: load from blogger_tokens.json
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
        print("Set them as environment variables or in blogger_tokens.json")
        sys.exit(1)

    # Get access token
    print("Authenticating with Blogger API...")

    def _handle_token_rotation(new_token: str):
        _try_auto_save_refresh_token(new_token)

    access_token = get_access_token(
        client_id, client_secret, refresh_token,
        on_new_refresh=_handle_token_rotation,
    )
    print("  Access token obtained.")

    # Publish Privacy Policy page
    print("\nPublishing Privacy Policy page...")
    result = publish_page(
        access_token=access_token,
        blog_id=blog_id,
        title="Privacy Policy",
        content=PRIVACY_POLICY_HTML,
    )

    if result["success"]:
        print(f"\n  SUCCESS!")
        print(f"  Page URL: {result['url']}")
        print(f"  Page ID:  {result['page_id']}")
        print("\n  NOTE: The page is published as a Blogger Page.")
        print("  You may need to add it to your blog's navigation menu.")
        print("  Go to Blogger Layout -> Add a Gadget -> Pages -> select 'Privacy Policy'.")
    else:
        print(f"\n  FAILED: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

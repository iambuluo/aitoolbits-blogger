"""OAuth setup script for Blogger API - simplified version."""
import json
import urllib.request
import urllib.parse
import webbrowser
import sys

CLIENT_ID = sys.argv[1] if len(sys.argv) > 1 else ""
CLIENT_SECRET = sys.argv[2] if len(sys.argv) > 2 else ""

REDIRECT_URI = "http://localhost"
SCOPE = "https://www.googleapis.com/auth/blogger"
AUTH_URL = (
    f"https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"response_type=code&"
    f"scope={SCOPE}&"
    f"access_type=offline&"
    f"prompt=consent"
)

TOKEN_URL = "https://oauth2.googleapis.com/token"

print("=" * 60)
print("Blogger OAuth Authorization")
print("=" * 60)
print()
print("Step 1: Open this URL in your browser:")
print(AUTH_URL)
print()

# Auto-open browser
webbrowser.open(AUTH_URL)
print("Browser should have opened automatically.")
print()
print("Step 2: Authorize the app, then copy the FULL URL from the")
print("browser address bar (it will show an error page, that's OK).")
print()
print("Step 3: Paste the URL below:")
print()

auth_code = input("Paste URL here: ").strip()

# Extract code from URL
if "code=" in auth_code:
    code = auth_code.split("code=")[1].split("&")[0]
else:
    print("ERROR: No authorization code found in URL!")
    sys.exit(1)

print(f"\nAuthorization code received: {code[:20]}...")

# Exchange code for tokens
print("\nExchanging code for tokens...")
token_data = {
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}

req = urllib.request.Request(
    TOKEN_URL,
    data=urllib.parse.urlencode(token_data).encode(),
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode())
except Exception as e:
    print(f"ERROR exchanging code: {e}")
    sys.exit(1)

refresh_token = tokens.get("refresh_token")
access_token = tokens.get("access_token")

if not refresh_token:
    print("ERROR: No refresh_token in response!")
    print(f"Response keys: {list(tokens.keys())}")
    sys.exit(1)

print(f"Access token: {access_token[:20]}...")
print(f"Refresh token: {refresh_token[:20]}...")

# Get blog ID
print("\nFetching Blogger blogs...")
blogs_url = "https://www.googleapis.com/blogger/v3/blogs"
req2 = urllib.request.Request(blogs_url)
req2.add_header("Authorization", f"Bearer {access_token}")

try:
    with urllib.request.urlopen(req2) as resp2:
        blogs_data = json.loads(resp2.read().decode())
except Exception as e:
    print(f"ERROR fetching blogs: {e}")
    sys.exit(1)

blog_id = None
blog_name = None
if "items" in blogs_data:
    for blog in blogs_data["items"]:
        if "aitoolbits" in blog.get("url", "").lower():
            blog_id = blog["id"]
            blog_name = blog["name"]
            break
    if not blog_id:
        blog_id = blogs_data["items"][0]["id"]
        blog_name = blogs_data["items"][0]["name"]
else:
    print(f"ERROR: {blogs_data}")
    sys.exit(1)

print(f"\nBlog: {blog_name}")
print(f"Blog ID: {blog_id}")

# Save to file for later use
output = {
    "BLOGGER_CLIENT_ID": CLIENT_ID,
    "BLOGGER_CLIENT_SECRET": CLIENT_SECRET,
    "BLOGGER_REFRESH_TOKEN": refresh_token,
    "BLOGGER_BLOG_ID": blog_id,
    "BLOG_NAME": blog_name,
    "BLOG_URL": f"https://aitoolbits.blogspot.com",
}

with open("blogger_tokens.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 60)
print("SUCCESS! Tokens saved to blogger_tokens.json")
print("=" * 60)
print(f"""
GitHub Secrets to configure:

  BLOGGER_CLIENT_ID     = {CLIENT_ID}
  BLOGGER_CLIENT_SECRET = {CLIENT_SECRET}
  BLOGGER_REFRESH_TOKEN = {refresh_token}
  BLOGGER_BLOG_ID       = {blog_id}

Also need:
  DEEPSEEK_API_KEY      = (your key)

Optional (Ad settings):
  AD_PROVIDER           = monetag
  AD_ZONE_ID            = 229646
""")

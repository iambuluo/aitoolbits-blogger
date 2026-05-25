# AI ToolBits - Automated Blogger

Auto-publish AI tool reviews & tutorials to [aitoolbits.blogspot.com](https://aitoolbits.blogspot.com) using GitHub Actions.

## How It Works

```
GitHub Actions (3x daily)
    → DeepSeek API generates article ($0.01/article)
    → Blogger API publishes to blog
    → Done! No manual work needed
```

## Setup (One-Time, ~10 minutes)

### Step 1: Create Google Cloud OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g., "blogger-auto-publisher")
3. Go to **APIs & Services > Library** → Search "Blogger API" → **Enable**
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth client ID**
6. Application type: **Desktop app**
7. Name: `Blogger Auto Publisher`
8. Click **Create** → Copy **Client ID** and **Client Secret**

### Step 2: Get DeepSeek API Key

1. Go to [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. Sign up / Log in
3. Create a new API key → Copy it
4. Cost: ~$0.01 per article (1500-2000 words)

### Step 3: Run OAuth Setup Script

```bash
cd scripts
python setup_oauth.py
```

This will:
1. Open your browser for Google authorization
2. Ask you to paste the authorization code
3. Exchange it for tokens
4. Print your GitHub Secrets

### Step 4: Create GitHub Repository & Add Secrets

```bash
# Create repo on GitHub, then:
cd /path/to/aitoolbits-blogger
git init
git remote add origin https://github.com/YOUR_USERNAME/aitoolbits-blogger.git
git add .
git commit -m "Initial commit: auto blog publisher"
git push -u origin main
```

Then go to your GitHub repo → **Settings > Secrets and variables > Actions** → Add these:

| Secret Name | Value |
|-------------|-------|
| `BLOGGER_CLIENT_ID` | Your Google OAuth Client ID |
| `BLOGGER_CLIENT_SECRET` | Your Google OAuth Client Secret |
| `BLOGGER_REFRESH_TOKEN` | From setup_oauth.py output |
| `BLOGGER_BLOG_ID` | From setup_oauth.py output |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key |
| `AD_PROVIDER` | `monetag` (default), `adsense`, or `none` |
| `AD_ZONE_ID` | Monetag zone ID or AdSense `ca-pub-XXXX` |

### Step 5: Done!

The automation will now run **3 times daily**:
- 8:17 AM Beijing time
- 2:42 PM Beijing time
- 9:08 PM Beijing time

## Manual Trigger

Go to **GitHub repo > Actions > Auto Publish Blog Articles > Run workflow**

Options:
- `article_count`: Number of articles (default: 1)
- `is_draft`: Save as draft instead of publishing

## Local Testing

```bash
# Generate articles (no publishing)
python scripts/generate_article.py 1

# Generate and publish (requires OAuth tokens)
export BLOGGER_CLIENT_ID="..."
export BLOGGER_CLIENT_SECRET="..."
export BLOGGER_REFRESH_TOKEN="..."
export BLOGGER_BLOG_ID="..."
export DEEPSEEK_API_KEY="..."
python scripts/publish_to_blogger.py 1 --draft  # Test as draft first
```

## Project Structure

```
aitoolbits-blogger/
├── .github/workflows/
│   └── publish-article.yml    # GitHub Actions workflow
├── scripts/
│   ├── generate_article.py    # AI article generation
│   ├── publish_to_blogger.py  # Blogger API publishing
│   ├── setup_oauth.py         # One-time OAuth setup wizard
│   └── topics.py              # 60+ article topic pool
├── articles/                  # Pre-written & generated articles
└── published/                 # Published article records
```

## Ad Revenue Strategy

### Phase 1: Now (Monetag)
- Every article auto-inserts **2 Monetag ad units** (mid-article + footer)
- Start earning from the very first article
- AD_PROVIDER = `monetag` (default)

### Phase 2: After 30+ Articles (Apply AdSense)
- Go to Blogger Dashboard → **Earnings** → Sign up for AdSense
- Blogger's native AdSense approval is much more lenient than standalone sites
- Wait for approval (usually 1-2 weeks)

### Phase 3: After AdSense Approved (Switch)
- Change `AD_PROVIDER` secret to `adsense`
- Set `AD_ZONE_ID` to your `ca-pub-XXXXXX` client ID
- AdSense will also appear via Blogger's built-in placement
- You can keep both (Monetag in-article + AdSense sidebar/header via Blogger)

## Cost Estimate

| Item | Cost |
|------|------|
| DeepSeek API | ~$0.01/article × 3/day ≈ $0.03/day ≈ **$1/month** |
| GitHub Actions | **Free** (public repo) |
| Blogger hosting | **Free** |
| Blogger domain | **Free** |
| **Total** | **~$1/month** |

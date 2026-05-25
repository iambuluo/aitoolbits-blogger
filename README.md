# AI ToolBits - Automated Blogger

Auto-publish AI tool reviews & tutorials to [aitoolbits.blogspot.com](https://aitoolbits.blogspot.com) using GitHub Actions.

> **Full documentation**: See [MAINTENANCE.md](./MAINTENANCE.md) for operations guide, troubleshooting, and ad revenue strategy.

## How It Works

```
GitHub Actions (3x daily, runs on GitHub cloud - no local machine needed)
    → Random topic selection from 89 topics (10 categories)
    → DeepSeek API generates 1800-2500 word article ($0.01/article)
    → Auto SEO: product links, E-E-A-T, smart labels, search descriptions
    → Blogger API v3 publishes with OAuth 2.0 (auto token refresh)
    → Done! Fully automated, zero manual work
```

### Key Features

| Feature | Details |
|---------|---------|
| Article count | 89 topics, 10 categories |
| Word count | 1800-2500 words/article |
| SEO | Product links, E-E-A-T, LSI keywords, meta descriptions |
| Labels | Smart auto-generated (5-6 per article) |
| Ad placements | 3 positions (configurable: none/monetag/adsense) |
| Publishing | Blogger API v3 with OAuth 2.0 auto-refresh |
| Scheduling | 3x daily (Beijing 08:17, 14:42, 21:08) |
| Cost | ~$1/month (DeepSeek API only) |

## Setup (One-Time)

### Step 1: Google Cloud OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable [Blogger API](https://console.cloud.google.com/apis/library/blogger.googleapis.com)
3. Create **OAuth 2.0 Client ID** (Desktop app type)
4. Add your email as test user in OAuth consent screen
5. Copy Client ID and Client Secret

### Step 2: DeepSeek API Key

1. Go to [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. Create API key (~$0.01/article, $1/month for 3 articles/day)

### Step 3: Run OAuth Setup

```bash
cd scripts
python setup_oauth.py
```

This opens browser for Google auth, exchanges code for tokens, and prints your Secrets.

### Step 4: GitHub Repository + Secrets

Push to GitHub, then add 7 Secrets at **Settings > Secrets > Actions**:

| Secret | Value |
|--------|-------|
| `BLOGGER_CLIENT_ID` | Your Google OAuth Client ID |
| `BLOGGER_CLIENT_SECRET` | Your Google OAuth Client Secret |
| `BLOGGER_REFRESH_TOKEN` | From setup_oauth.py output |
| `BLOGGER_BLOG_ID` | From setup_oauth.py output |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key |
| `AD_PROVIDER` | `none` (no ads), `monetag`, or `adsense` |
| `AD_ZONE_ID` | Monetag zone ID or AdSense `ca-pub-XXXX` |

### Step 5: Done!

Automation runs 3x daily on GitHub cloud. No local machine needed.

## Manual Trigger

Go to **Actions > Auto Publish Blog Articles > Run workflow**
- `article_count`: Number of articles (default: 1)
- `is_draft`: Save as draft (default: false)

## Local Testing

```bash
# Generate only (no publishing)
python scripts/generate_article.py 3

# Generate + publish
export BLOGGER_CLIENT_ID="..." BLOGGER_CLIENT_SECRET="..." \
       BLOGGER_REFRESH_TOKEN="..." BLOGGER_BLOG_ID="..." \
       DEEPSEEK_API_KEY="..."
python scripts/publish_to_blogger.py 1 --draft
```

## Project Structure

```
aitoolbits-blogger/
├── .github/workflows/
│   └── publish-article.yml    # GitHub Actions (3x daily cron)
├── scripts/
│   ├── topics.py              # 89 topics, 10 categories
│   ├── generate_article.py    # DeepSeek generator + SEO optimizer
│   ├── publish_to_blogger.py  # Blogger API publisher (main entry)
│   ├── setup_oauth.py         # One-time OAuth wizard
│   └── oauth_setup.py         # OAuth authorization tool
├── articles/                  # Generated article archive
├── .gitignore                 # Excludes all JSON (protects secrets)
└── requirements.txt
```

## Ad Revenue Strategy

| Phase | Articles | Action | AD_PROVIDER |
|-------|----------|--------|-------------|
| Now | 0-30 | Build content, no ads | `none` |
| After 30+ | 30+ | Apply AdSense via Blogger dashboard | `none` |
| Approved | 30+ | Enable ads | `adsense` |

## Cost Estimate

| Item | Cost |
|------|------|
| DeepSeek API | ~$0.01 x 3/day ≈ **$1/month** |
| GitHub Actions | **Free** (public repo: 2000 min/month, uses ~180) |
| Blogger hosting | **Free** |
| Blogger domain | **Free** |
| **Total** | **~$1/month** |

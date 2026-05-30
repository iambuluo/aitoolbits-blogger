"""
Article topic pool for aitoolbits.blogspot.com
Organized by categories with infinite expandable topics.
"""

TOPICS = [
    # === AI Image Generation (High traffic) ===
    {
        "title": "Best AI Image Generators in {year}: Complete Comparison",
        "category": "AI Image Generation",
        "keywords": ["AI image generator", "text to image", "AI art", "best AI tools {year}"],
        "type": "comparison",
    },
    {
        "title": "Midjourney V{version} Review: Everything You Need to Know",
        "category": "AI Image Generation",
        "keywords": ["Midjourney review", "Midjourney V{version}", "AI art tool"],
        "type": "review",
    },
    {
        "title": "DALL-E 3 vs Midjourney vs Stable Diffusion: Which Is Best?",
        "category": "AI Image Generation",
        "keywords": ["DALL-E 3", "Midjourney", "Stable Diffusion", "AI image comparison"],
        "type": "comparison",
    },
    {
        "title": "How to Create Stunning AI Art: A Beginner's Guide",
        "category": "AI Image Generation",
        "keywords": ["AI art tutorial", "how to create AI art", "beginner guide"],
        "type": "tutorial",
    },
    {
        "title": "Top 10 AI Background Removers: Free and Paid",
        "category": "AI Image Generation",
        "keywords": ["AI background remover", "remove background", "free AI tool"],
        "type": "list",
    },
    {
        "title": "AI Logo Generators Compared: Which Creates the Best Brand Logos?",
        "category": "AI Image Generation",
        "keywords": ["AI logo generator", "brand logo", "AI design tool"],
        "type": "comparison",
    },
    {
        "title": "Flux AI Image Generator Review: Is It Worth the Hype?",
        "category": "AI Image Generation",
        "keywords": ["Flux AI", "AI image generator", "Black Forest Labs"],
        "type": "review",
    },
    {
        "title": "Best AI Upscaling Tools: Enhance Photos to 4K Resolution",
        "category": "AI Image Generation",
        "keywords": ["AI upscaling", "image enhancement", "4K upscaling", "AI photo tool"],
        "type": "list",
    },

    # === AI Video Generation (Growing fast) ===
    {
        "title": "Best AI Video Generators in {year}: Create Professional Videos",
        "category": "AI Video Generation",
        "keywords": ["AI video generator", "text to video", "AI video {year}"],
        "type": "comparison",
    },
    {
        "title": "Runway Gen-3 vs Kling AI vs Sora: AI Video Showdown",
        "category": "AI Video Generation",
        "keywords": ["Runway Gen-3", "Kling AI", "Sora", "AI video comparison"],
        "type": "comparison",
    },
    {
        "title": "How to Make AI Videos for YouTube: Complete Workflow",
        "category": "AI Video Generation",
        "keywords": ["AI video for YouTube", "YouTube automation", "AI content creation"],
        "type": "tutorial",
    },
    {
        "title": "Pika AI Video Generator Review: Pros, Cons, and Pricing",
        "category": "AI Video Generation",
        "keywords": ["Pika AI", "AI video generator review", "text to video"],
        "type": "review",
    },
    {
        "title": "Best Free AI Video Editing Tools for Content Creators",
        "category": "AI Video Generation",
        "keywords": ["AI video editing", "free video editor", "content creator tools"],
        "type": "list",
    },
    {
        "title": "AI Avatar Video Generators: Create Talking Head Videos Easily",
        "category": "AI Video Generation",
        "keywords": ["AI avatar", "talking head video", "AI presenter"],
        "type": "list",
    },

    # === AI Writing & Content ===
    {
        "title": "Best AI Writing Tools in {year}: ChatGPT, Claude, and Beyond",
        "category": "AI Writing",
        "keywords": ["AI writing tool", "best AI writer", "AI content {year}"],
        "type": "comparison",
    },
    {
        "title": "ChatGPT vs Claude vs Gemini: The Ultimate {year} Comparison",
        "category": "AI Writing",
        "keywords": ["ChatGPT vs Claude", "ChatGPT vs Gemini", "AI chatbot comparison"],
        "type": "comparison",
    },
    {
        "title": "How to Write a Blog Post with AI: 10x Your Content Output",
        "category": "AI Writing",
        "keywords": ["AI blog writing", "AI content creation", "blog automation"],
        "type": "tutorial",
    },
    {
        "title": "Jasper AI Review: Is It Still Worth It in {year}?",
        "category": "AI Writing",
        "keywords": ["Jasper AI review", "AI copywriting", "content marketing AI"],
        "type": "review",
    },
    {
        "title": "Best AI Tools for SEO Content Writing",
        "category": "AI Writing",
        "keywords": ["AI SEO tool", "SEO content writing", "AI content optimization"],
        "type": "list",
    },
    {
        "title": "How to Use AI to Write YouTube Scripts That Get Views",
        "category": "AI Writing",
        "keywords": ["YouTube script AI", "AI script writing", "YouTube automation"],
        "type": "tutorial",
    },
    {
        "title": "Grammarly vs Wordtune vs QuillBot: Which AI Writing Assistant Wins?",
        "category": "AI Writing",
        "keywords": ["Grammarly", "Wordtune", "QuillBot", "AI writing assistant"],
        "type": "comparison",
    },

    # === AI Coding & Development ===
    {
        "title": "Best AI Coding Assistants in {year}: Cursor, Copilot, and More",
        "category": "AI Coding",
        "keywords": ["AI coding assistant", "Cursor AI", "GitHub Copilot", "AI programmer"],
        "type": "comparison",
    },
    {
        "title": "Cursor AI vs GitHub Copilot: Which Makes You More Productive?",
        "category": "AI Coding",
        "keywords": ["Cursor AI vs Copilot", "AI code editor", "developer productivity"],
        "type": "comparison",
    },
    {
        "title": "How to Build a Full Website with AI (No Coding Required)",
        "category": "AI Coding",
        "keywords": ["AI website builder", "no-code AI", "AI web development"],
        "type": "tutorial",
    },
    {
        "title": "DeepSeek Coder vs GPT-4 for Programming: Benchmark Results",
        "category": "AI Coding",
        "keywords": ["DeepSeek Coder", "AI programming", "code generation benchmark"],
        "type": "comparison",
    },
    {
        "title": "Top 10 AI Tools Every Developer Should Know in {year}",
        "category": "AI Coding",
        "keywords": ["AI tools for developers", "programmer tools", "AI development"],
        "type": "list",
    },
    {
        "title": "v0 by Vercel Review: Generate React Components with AI",
        "category": "AI Coding",
        "keywords": ["v0.dev", "Vercel AI", "React AI generator", "AI UI"],
        "type": "review",
    },
    {
        "title": "Bolt.new vs Lovable vs Replit Agent: AI App Builders Compared",
        "category": "AI Coding",
        "keywords": ["Bolt.new", "Lovable", "Replit Agent", "AI app builder"],
        "type": "comparison",
    },

    # === AI Audio & Music ===
    {
        "title": "Best AI Music Generators in {year}: Create Songs with AI",
        "category": "AI Audio",
        "keywords": ["AI music generator", "Suno AI", "AI song creation"],
        "type": "comparison",
    },
    {
        "title": "Suno AI vs Udio: Which AI Music Generator Sounds Better?",
        "category": "AI Audio",
        "keywords": ["Suno vs Udio", "AI music comparison", "AI song"],
        "type": "comparison",
    },
    {
        "title": "Best AI Voice Generators: Create Realistic Voiceovers",
        "category": "AI Audio",
        "keywords": ["AI voice generator", "text to speech", "AI voiceover"],
        "type": "list",
    },
    {
        "title": "ElevenLabs Review: The Most Realistic AI Voice Generator",
        "category": "AI Audio",
        "keywords": ["ElevenLabs", "AI voice", "voice cloning", "text to speech"],
        "type": "review",
    },
    {
        "title": "AI Podcast Generation: Create Full Podcast Episodes Automatically",
        "category": "AI Audio",
        "keywords": ["AI podcast", "automated podcast", "AI content creation"],
        "type": "tutorial",
    },

    # === AI Productivity & Automation ===
    {
        "title": "Best AI Productivity Tools in {year}: Work 10x Faster",
        "category": "AI Productivity",
        "keywords": ["AI productivity", "AI tools", "work faster AI"],
        "type": "list",
    },
    {
        "title": "Notion AI vs Obsidian Copilot: Best AI Note-Taking App",
        "category": "AI Productivity",
        "keywords": ["Notion AI", "Obsidian", "AI note taking", "productivity app"],
        "type": "comparison",
    },
    {
        "title": "How to Automate Your Workflow with AI: Practical Guide",
        "category": "AI Productivity",
        "keywords": ["AI automation", "workflow automation", "AI productivity"],
        "type": "tutorial",
    },
    {
        "title": "Zapier vs Make.com vs n8n: Best AI Automation Platform",
        "category": "AI Productivity",
        "keywords": ["Zapier", "Make.com", "n8n", "AI automation platform"],
        "type": "comparison",
    },
    {
        "title": "Best AI Meeting Assistants: Never Miss Important Details",
        "category": "AI Productivity",
        "keywords": ["AI meeting assistant", "Otter.ai", "meeting transcription"],
        "type": "list",
    },
    {
        "title": "AI Email Assistants: Write Better Emails in Half the Time",
        "category": "AI Productivity",
        "keywords": ["AI email assistant", "email automation", "AI writing tool"],
        "type": "list",
    },

    # === AI Design & Creative ===
    {
        "title": "Best AI Design Tools in {year}: Canva AI, Figma AI, and More",
        "category": "AI Design",
        "keywords": ["AI design tool", "Canva AI", "Figma AI", "AI graphic design"],
        "type": "comparison",
    },
    {
        "title": "Canva AI vs Adobe Firefly: Which Design Tool Should You Use?",
        "category": "AI Design",
        "keywords": ["Canva AI", "Adobe Firefly", "AI design comparison"],
        "type": "comparison",
    },
    {
        "title": "Best AI Presentation Makers: Create Slides in Minutes",
        "category": "AI Design",
        "keywords": ["AI presentation", "Gamma AI", "Tome AI", "slide maker"],
        "type": "list",
    },
    {
        "title": "Framer AI Review: Build Beautiful Websites Without Coding",
        "category": "AI Design",
        "keywords": ["Framer AI", "AI website builder", "no-code design"],
        "type": "review",
    },
    {
        "title": "AI UI Design Tools: Generate App Interfaces Automatically",
        "category": "AI Design",
        "keywords": ["AI UI design", "interface generator", "app design AI"],
        "type": "list",
    },

    # === Free AI Tools (Highest search volume) ===
    {
        "title": "Top 20 Completely Free AI Tools You Should Use in {year}",
        "category": "Free AI Tools",
        "keywords": ["free AI tools", "free AI", "best free AI {year}"],
        "type": "list",
    },
    {
        "title": "Best Free AI Image Generators (No Watermark, No Sign-Up)",
        "category": "Free AI Tools",
        "keywords": ["free AI image generator", "no watermark AI", "free AI art"],
        "type": "list",
    },
    {
        "title": "Free Alternatives to ChatGPT: AI Chatbots That Cost Nothing",
        "category": "Free AI Tools",
        "keywords": ["free ChatGPT alternative", "free AI chatbot", "no cost AI"],
        "type": "list",
    },
    {
        "title": "Best Free AI Tools for Students: Study Smarter, Not Harder",
        "category": "Free AI Tools",
        "keywords": ["AI tools for students", "free study AI", "student productivity"],
        "type": "list",
    },
    {
        "title": "Free AI Video Generators: Create Videos Without Paying a Cent",
        "category": "Free AI Tools",
        "keywords": ["free AI video", "no cost video generator", "free video AI"],
        "type": "list",
    },

    # === AI Marketing & SEO ===
    {
        "title": "Best AI Marketing Tools in {year}: Dominate Your Strategy",
        "category": "AI Marketing",
        "keywords": ["AI marketing tools", "AI marketing", "digital marketing AI"],
        "type": "list",
    },
    {
        "title": "How to Use AI for SEO: A Complete Guide for Beginners",
        "category": "AI Marketing",
        "keywords": ["AI for SEO", "SEO automation", "AI search optimization"],
        "type": "tutorial",
    },
    {
        "title": "Best AI Ad Copy Generators: Boost Your Click-Through Rates",
        "category": "AI Marketing",
        "keywords": ["AI ad copy", "AI copywriting", "ad generator"],
        "type": "list",
    },
    {
        "title": "AI Social Media Tools: Automate Your Content Calendar",
        "category": "AI Marketing",
        "keywords": ["AI social media", "content scheduling", "social media automation"],
        "type": "list",
    },

    # === AI for Business ===
    {
        "title": "Best AI Tools for Small Business Owners in {year}",
        "category": "AI Business",
        "keywords": ["AI for small business", "business AI tools", "SME automation"],
        "type": "list",
    },
    {
        "title": "How to Start an AI-Powered Business: Practical Ideas",
        "category": "AI Business",
        "keywords": ["AI business ideas", "AI startup", "AI entrepreneurship"],
        "type": "tutorial",
    },
    {
        "title": "AI Customer Service Tools: Chatbots That Actually Work",
        "category": "AI Business",
        "keywords": ["AI customer service", "AI chatbot", "customer support AI"],
        "type": "list",
    },
    {
        "title": "Best AI Analytics Tools: Make Data-Driven Decisions",
        "category": "AI Business",
        "keywords": ["AI analytics", "data analysis AI", "business intelligence AI"],
        "type": "list",
    },

    # === AI Image Generation (Extended - Long-tail) ===
    {
        "title": "Best AI Headshot Generators: Professional Photos in Minutes",
        "category": "AI Image Generation",
        "keywords": ["AI headshot generator", "professional photo AI", "headshot AI"],
        "type": "list",
    },
    {
        "title": "AI Avatar Generators: Create Your Digital Persona",
        "category": "AI Image Generation",
        "keywords": ["AI avatar generator", "digital avatar", "AI profile picture"],
        "type": "list",
    },
    {
        "title": "Best AI Product Photography Tools for E-Commerce",
        "category": "AI Image Generation",
        "keywords": ["AI product photography", "e-commerce AI", "product photo AI"],
        "type": "list",
    },
    {
        "title": "AI Meme Generators: Create Viral Memes with AI",
        "category": "AI Image Generation",
        "keywords": ["AI meme generator", "meme maker AI", "funny AI images"],
        "type": "list",
    },

    # === AI Video Generation (Extended) ===
    {
        "title": "Best AI Video Translators: Dub Videos into Any Language",
        "category": "AI Video Generation",
        "keywords": ["AI video translator", "video dubbing AI", "multilingual video"],
        "type": "list",
    },
    {
        "title": "AI Video Enhancers: Upscale Old Videos to 4K Quality",
        "category": "AI Video Generation",
        "keywords": ["AI video enhancer", "video upscaling AI", "video quality AI"],
        "type": "list",
    },
    {
        "title": "Best AI Screen Recorders: Record and Edit with AI",
        "category": "AI Video Generation",
        "keywords": ["AI screen recorder", "screen recording AI", "video recording tool"],
        "type": "list",
    },

    # === AI Writing (Extended) ===
    {
        "title": "Best AI Paraphrasing Tools: Rewrite Content Like a Pro",
        "category": "AI Writing",
        "keywords": ["AI paraphrasing tool", "rewriter AI", "content spinner"],
        "type": "list",
    },
    {
        "title": "AI Story Generators: Write Fiction and Novels with AI",
        "category": "AI Writing",
        "keywords": ["AI story generator", "AI novel writing", "fiction AI"],
        "type": "list",
    },
    {
        "title": "Best AI Resume Builders: Land Your Dream Job",
        "category": "AI Writing",
        "keywords": ["AI resume builder", "resume AI", "CV generator"],
        "type": "list",
    },

    # === AI Coding (Extended) ===
    {
        "title": "Best AI Code Review Tools: Catch Bugs Automatically",
        "category": "AI Coding",
        "keywords": ["AI code review", "code analysis AI", "bug detection AI"],
        "type": "list",
    },
    {
        "title": "AI App Builders for Non-Programmers: No-Code Solutions",
        "category": "AI Coding",
        "keywords": ["AI app builder", "no-code AI", "app development AI"],
        "type": "list",
    },

    # === AI Audio (Extended) ===
    {
        "title": "Best AI Audio Enhancers: Clean Up Bad Audio Recordings",
        "category": "AI Audio",
        "keywords": ["AI audio enhancer", "audio cleanup AI", "noise reduction AI"],
        "type": "list",
    },
    {
        "title": "AI Song Cover Generators: Create Cover Versions with AI",
        "category": "AI Audio",
        "keywords": ["AI song cover", "AI music cover", "voice clone music"],
        "type": "list",
    },

    # === Free AI Tools (Extended - Highest search volume) ===
    {
        "title": "Free AI Tools for Teachers: Revolutionize Your Classroom",
        "category": "Free AI Tools",
        "keywords": ["AI tools for teachers", "free education AI", "teaching AI"],
        "type": "list",
    },
    {
        "title": "Best Free AI Photo Editors: No Subscription Required",
        "category": "Free AI Tools",
        "keywords": ["free AI photo editor", "photo editing AI", "no cost image editor"],
        "type": "list",
    },
    {
        "title": "Free AI Website Builders: Create a Site Without Paying",
        "category": "Free AI Tools",
        "keywords": ["free AI website builder", "free website AI", "no cost website"],
        "type": "list",
    },

    # === AI Marketing (Extended) ===
    {
        "title": "Best AI Email Marketing Tools: Boost Open Rates with AI",
        "category": "AI Marketing",
        "keywords": ["AI email marketing", "email automation AI", "marketing AI tool"],
        "type": "list",
    },
    {
        "title": "AI Influencer Marketing Tools: Find the Right Creators",
        "category": "AI Marketing",
        "keywords": ["AI influencer marketing", "influencer AI", "creator discovery AI"],
        "type": "list",
    },

    # === AI Productivity (Extended) ===
    {
        "title": "Best AI Scheduling Assistants: Never Double-Book Again",
        "category": "AI Productivity",
        "keywords": ["AI scheduling assistant", "calendar AI", "AI meeting scheduler"],
        "type": "list",
    },
    {
        "title": "AI Presentation Generators: Create Slideshows in Seconds",
        "category": "AI Productivity",
        "keywords": ["AI presentation generator", "AI slideshow", "auto presentation"],
        "type": "list",
    },
    {
        "title": "Best AI Transcription Tools: Convert Audio to Text Instantly",
        "category": "AI Productivity",
        "keywords": ["AI transcription", "speech to text AI", "audio transcription tool"],
        "type": "list",
    },

    # === AI Design (Extended) ===
    {
        "title": "AI Icon Generators: Create App Icons and Logos with AI",
        "category": "AI Design",
        "keywords": ["AI icon generator", "app icon AI", "icon design AI"],
        "type": "list",
    },
    {
        "title": "Best AI Font Generators: Create Custom Typography",
        "category": "AI Design",
        "keywords": ["AI font generator", "custom font AI", "typography AI"],
        "type": "list",
    },

    # === Emerging / Trending (High growth potential) ===
    {
        "title": "Best AI Agents in {year}: Autonomous AI That Works for You",
        "category": "AI Productivity",
        "keywords": ["AI agents", "autonomous AI", "AI assistant {year}"],
        "type": "list",
    },
    {
        "title": "AI Search Engines Compared: Perplexity vs You.com vs Bing Chat",
        "category": "AI Productivity",
        "keywords": ["AI search engine", "Perplexity AI", "AI search comparison"],
        "type": "comparison",
    },
    {
        "title": "Best AI Chrome Extensions for Productivity in {year}",
        "category": "Free AI Tools",
        "keywords": ["AI Chrome extension", "browser AI", "productivity extension"],
        "type": "list",
    },
    {
        "title": "AI Data Visualization Tools: Turn Data into Beautiful Charts",
        "category": "AI Business",
        "keywords": ["AI data visualization", "chart generator AI", "data viz AI"],
        "type": "list",
    },
    {
        "title": "Best AI PowerPoint Alternatives: Better Presentations with AI",
        "category": "AI Design",
        "keywords": ["AI PowerPoint alternative", "AI presentation", "slide design AI"],
        "type": "list",
    },
    {
        "title": "AI Background Noise Removal: Crystal Clear Audio for Calls",
        "category": "AI Audio",
        "keywords": ["AI noise removal", "background noise AI", "audio cleanup"],
        "type": "list",
    },
    {
        "title": "Best AI Tools for Freelancers: Boost Your Income in {year}",
        "category": "AI Business",
        "keywords": ["AI for freelancers", "freelancer AI tools", "side hustle AI"],
        "type": "list",
    },
    {
        "title": "AI Legal Tools: How AI Is Changing the Legal Industry",
        "category": "AI Business",
        "keywords": ["AI legal tools", "legal AI", "law AI technology"],
        "type": "list",
    },
]

# Dynamic parameters for title generation
import random
from datetime import datetime

def get_random_topic():
    """Get a random topic with parameters filled in."""
    topic = random.choice(TOPICS)
    year = datetime.now().year
    title = topic["title"].format(year=year, version=f"{random.randint(6,8)}.{random.randint(0,2)}")
    return {
        "title": title,
        "category": topic["category"],
        "keywords": [kw.format(year=year) for kw in topic["keywords"]],
        "type": topic["type"],
    }


def get_article_prompt(topic):
    """Generate a detailed prompt for AI article generation based on topic type."""
    base = f"""Write a comprehensive, SEO-optimized blog article in English.

Title: {topic['title']}
Category: {topic['category']}
Primary Keywords: {', '.join(topic['keywords'])}
Article Type: {topic['type'].upper()}

SEO & GEO REQUIREMENTS:
1. Length: 1800-2500 words minimum (longer = better for SEO)
2. HTML format: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>, <blockquote>, <a>
3. COMPELLING INTRODUCTION: Hook the reader in 2-3 paragraphs. Address the reader's pain point or question directly. Include the primary keyword naturally in the first 100 words.
4. STRUCTURE: Clear H2/H3 heading hierarchy. Each H2 section should be 200-400 words.
5. PRODUCT LINKS: Every AI tool/product mentioned MUST include its official website link on the FIRST mention only. Use format: <a href="https://official-site.com" target="_blank" rel="nofollow noopener">Product Name</a>
6. PRACTICAL VALUE: Include specific pricing, real feature comparisons, data points, and actionable advice. Never be vague.
7. LSI KEYWORDS: Naturally weave related terms throughout (e.g., for "AI image generator" include: "text-to-image AI", "AI art generator", "AI image creation", "artificial intelligence art", "machine learning image generation")
8. CALL-TO-ACTION: End with a meaningful conclusion that answers "what should I do next?"
9. TONE: Conversational expert. Use "you" and "I". Be opinionated but fair. Short paragraphs (2-3 sentences max).
10. UNIQUE CONTENT: No filler, no fluff. Every paragraph must add value. Include original analysis, not just feature lists.
11. FORMAT: Pure HTML only - NO markdown syntax, NO code blocks
12. NO H1 TAG: The blog platform handles the title. Start directly with the first H2.

"""

    type_specific = {
        "comparison": """For this comparison article:
- Create a detailed HTML comparison table near the beginning with columns: Tool, Best For, Pricing, Key Feature, Rating
- Cover each tool/product individually (3-5 paragraphs each) with pros and cons
- Include the official website link for EVERY product on first mention
- Include specific pricing tiers (free plan, pro plan, enterprise) with real numbers
- End with a clear "Which One Should You Choose?" recommendation section with specific use cases
- Mention at least 5 different tools/products
- Add a quick-summary box at the end using blockquote for the winner
""",
        "review": """For this review article:
- Start with a brief overview including the official website link
- Cover key features in detail with real-world use examples
- Include specific pricing tiers and value-for-money analysis
- Create detailed pros and cons lists with concrete examples
- Compare with 2-3 main competitors (include their links too)
- Give an overall rating (e.g., "8.5/10") with a breakdown by category
- Include a "Who Should Use This?" section with specific user personas
- Mention recent updates or version changes if applicable
""",
        "tutorial": """For this tutorial article:
- Start with "What You'll Need" section (include tool links)
- Use numbered step-by-step instructions with clear action verbs
- Include a "Before We Begin" expectations section
- Add troubleshooting tips for common issues using blockquote tags
- Include "Pro Tips" callout boxes for advanced users
- End with a comprehensive FAQ section (at least 5 common questions with answers)
- Include a "Time & Cost Estimate" section at the beginning
- Link to all tools/resources mentioned on first mention
""",
        "github_trending": """For this GitHub Trending article:
- You are introducing a SPECIFIC GitHub repository that is trending this week
- The repo details (name, description, stars, URL) will be provided - use them accurately
- Start with a hook about WHY this repo is gaining attention (mention the star count)
- Cover: what it does, key features, getting started, why it's trending, who should use it
- Link to the GitHub repo using: <a href="REPO_URL" target="_blank" rel="noopener noreferrer">View on GitHub</a>
- Structure with clear H2 sections: What Is It, Key Features, Getting Started, Why It's Trending, Who Should Use It, Bottom Line
- Include practical value: what can developers BUILD with this?
- Mention 1-2 alternative/similar repos briefly for context
- End with a call-to-action encouraging readers to star/bookmark the repo
""",
        "list": f"""For this listicle article:
- Cover at least 8-10 items in your list
- Each item MUST have: official name with website link, 2-3 sentence description, key features (bullet list), pricing (specific tiers), "Best for" one-liner
- Order items from best/recommended to least recommended
- Include a comparison summary table at the end
- Highlight the top 3 picks with extra detail and clear reasoning
- Add a "How to Choose" section before the list with decision criteria
- Use H3 headings for each item for clear scannability
""",
    }

    return base + type_specific.get(topic["type"], "")


if __name__ == "__main__":
    # Test: print 3 random topics
    for _ in range(3):
        t = get_random_topic()
        print(f"  [{t['type'].upper()}] {t['title']}")
    print(f"\nTotal topics in pool: {len(TOPICS)}")

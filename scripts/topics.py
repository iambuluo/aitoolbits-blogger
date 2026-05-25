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
Target Keywords: {', '.join(topic['keywords'])}
Article Type: {topic['type'].upper()}

REQUIREMENTS:
1. Length: 1500-2000 words minimum
2. Use proper HTML format: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>, <blockquote>
3. Include a compelling introduction (2-3 paragraphs)
4. Break content into clear sections with H2 and H3 headings
5. Include practical tips, real examples, and actionable advice
6. Add a conclusion with a call-to-action
7. Write in a conversational but professional tone
8. Use short paragraphs (2-4 sentences max) for readability
9. Include relevant statistics or data points where possible
10. IMPORTANT: Do NOT use any markdown formatting - use pure HTML tags only
11. Do NOT include the title as an H1 tag (the blog platform handles that)
12. Start directly with the first H2 section

"""

    type_specific = {
        "comparison": """For this comparison article:
- Create a detailed comparison table near the beginning
- Cover each tool/product individually with pros and cons
- Include pricing information for each option
- End with a clear "Which One Should You Choose?" recommendation section
- Mention at least 5 different tools/products
""",
        "review": """For this review article:
- Start with a brief overview of what the tool does
- Cover key features in detail with examples
- Discuss pricing and value for money
- Include pros and cons lists
- Compare with 2-3 main competitors
- Give an overall rating or verdict
- Mention who this tool is best for
""",
        "tutorial": """For this tutorial article:
- Start with "What You'll Need" section
- Use numbered step-by-step instructions
- Include screenshots placeholders (describe what the user should see)
- Add troubleshooting tips for common issues
- Include "Pro Tips" callout boxes using blockquote tags
- End with a FAQ section (at least 5 common questions)
""",
        "list": f"""For this listicle article:
- Cover at least 8-10 items in your list
- Each item should have: name, description, key features, pricing, best for
- Order items from best to worst (or free to paid)
- Include a comparison summary at the end
- Highlight the top pick with extra detail
""",
    }

    return base + type_specific.get(topic["type"], "")


if __name__ == "__main__":
    # Test: print 3 random topics
    for _ in range(3):
        t = get_random_topic()
        print(f"  [{t['type'].upper()}] {t['title']}")
    print(f"\nTotal topics in pool: {len(TOPICS)}")

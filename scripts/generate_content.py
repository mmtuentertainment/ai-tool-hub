#!/usr/bin/env python3
"""
AI Tool Hub — Automated Content Pipeline
=========================================
This script is designed to be run by Hermes Agent on a cron schedule.
It generates a new article, builds the site, and commits to git.

Usage:
    python3 scripts/generate_content.py [--topic "specific topic"]

When run without --topic, it picks from the content calendar.
The article is written to content/ as markdown, then the site is rebuilt.

This script is meant to be called by Hermes as part of a cron job.
Hermes does the actual writing (it's the AI). This script handles the
plumbing: topic selection, file creation, site rebuild, git commit.
"""

import sys
import os
import random
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content"

# Content calendar — topics that have affiliate revenue potential
# Each topic maps to a keyword cluster with buyer intent
TOPIC_CALENDAR = [
    "Best AI tools for email marketing in 2026 — pricing, features, verdict",
    "AI accounting tools for freelancers: comparison and real costs",
    "How to use AI for competitor analysis — a step-by-step workflow",
    "AI-powered CRM tools compared: which one fits your business size",
    "Building an AI chatbot for your website — no-code tools ranked",
    "AI tools for social media scheduling that actually work",
    "How small law firms use AI to save 15 hours per week",
    "AI content tools for e-commerce: product descriptions at scale",
    "Best AI project management tools for remote teams in 2026",
    "AI tools for lead generation: what works and what's hype",
    "How to automate your invoicing with AI — complete setup guide",
    "AI transcription tools compared: accuracy, speed, price",
    "AI tools for real estate agents: listings, leads, and closing",
    "How gyms and fitness studios use AI to retain members",
    "AI resume screening tools for small business hiring",
    "Best AI tools for webinar and event automation",
    "AI-powered SEO tools that actually improve rankings",
    "How restaurants use AI for inventory and ordering",
    "AI tools for nonprofit organizations — free and low-cost options",
    "Design tools for non-designers: AI-powered alternatives to Adobe",
    "AI tools for podcast production: editing, transcripts, clips",
    "How to build an AI-powered FAQ bot for your store",
    "AI sales tools: lead scoring, outreach, and follow-up automation",
    "Best AI tools for YouTube creators in 2026",
    "AI for appointment booking and scheduling — tools compared",
]

# Affiliate-friendly topics with high CPL (cost per lead) payouts
HIGH_PAYOUT_TOPICS = [
    "AI tools for accounting and bookkeeping — QuickBooks alternatives",
    "Best AI CRM software for small business — HubSpot vs Salesforce vs Pipedrive",
    "AI email marketing platforms — Brevo vs Mailchimp vs Klaviyo",
    "AI website builders compared — which is best for small business",
    "AI payroll tools for small business — Gusto vs Rippling vs Deel",
]


def get_topic():
    """Get today's topic from the calendar or from command line"""
    if "--topic" in sys.argv:
        idx = sys.argv.index("--topic")
        return sys.argv[idx + 1]
    
    # Use day of year to pick from calendar, so it's deterministic per day
    day_of_year = datetime.now().timetuple().tm_yday
    return TOPIC_CALENDAR[day_of_year % len(TOPIC_CALENDAR)]


def slugify(text):
    """Convert topic to filename slug"""
    slug = text.lower()
    # Remove punctuation after colons/dashes
    slug = slug.split(":")[0].split("—")[0].strip()
    slug = "".join(c for c in slug if c.isalnum() or c in " -")
    slug = slug.replace(" ", "-").replace("--", "-").strip("-")
    return slug[:80]  # Keep filenames reasonable


def create_article_placeholder(topic, slug, date_str):
    """Create the article file — Hermes fills in the actual content"""
    filepath = CONTENT_DIR / f"{slug}.md"
    
    if filepath.exists():
        print(f"  ⚠️  Article already exists: {filepath.name}")
        return filepath
    
    header = f"""# {topic}

**Date:** {date_str}
**Tags:** ai-tools, comparison
**Description:** [Hermes will fill in — practical, tested advice on {topic}]

---

[Hermes Agent will write the full article here. The content should be:
- 1500-3000 words
- Practical and specific (real prices, real features, real comparisons)
- Include a comparison table where appropriate
- Include affiliate-friendly tool mentions (Jasper, HubSpot, Brevo, Surfer SEO, etc.)
- Honest tone — acknowledge drawbacks, not just hype
- SEO-optimized for the topic keyword
- End with a clear recommendation and next steps]
"""
    filepath.write_text(header)
    print(f"  ✓ Created: {filepath.name}")
    return filepath


def main():
    print("=" * 60)
    print("AI Tool Hub — Content Generation Pipeline")
    print("=" * 60)
    
    topic = get_topic()
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(topic)
    
    print(f"\n📅 Date: {date_str}")
    print(f"📝 Topic: {topic}")
    print(f"📄 Slug: {slug}")
    
    # Step 1: Create the article placeholder
    print("\n--- Step 1: Create article ---")
    article_path = create_article_placeholder(topic, slug, date_str)
    
    # Step 2: Build the site
    print("\n--- Step 2: Build site ---")
    os.system(f"cd {ROOT} && python3 scripts/build_site.py")
    
    # Step 3: Git commit
    print("\n--- Step 3: Git commit ---")
    os.system(f'cd {ROOT} && git add -A && git commit -m "content: {topic[:60]}" 2>&1 | tail -3')
    
    print(f"\n✅ Pipeline complete!")
    print(f"   Article: {article_path}")
    print(f"   Next step: Hermes writes the full article content")
    print(f"   The article file is ready at: {article_path}")
    print(f"\n   To have Hermes write the content, run:")
    print(f"   hermes chat -q 'Read {article_path} and write the full article. "
          f"Follow the style of existing articles in {CONTENT_DIR}. "
          f"Make it 1500-3000 words, practical, with real prices and comparisons. "
          f"Include a comparison table. Be honest about drawbacks.'")
    
    return article_path


if __name__ == "__main__":
    main()
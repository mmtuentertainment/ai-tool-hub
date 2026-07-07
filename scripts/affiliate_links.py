#!/usr/bin/env python3
"""
AI Tool Hub — Affiliate Link Manager
====================================
Manages affiliate links for the site. Each tool has a mapping of
tool name → affiliate URL. When building articles, tool mentions
can be auto-linked to affiliate URLs.

Affiliate programs to sign up for (free):
1. Impact Radius (impact.com) — HubSpot, Jasper, Canva, Surfer SEO
2. PartnerStack — Brevo, Notion, Zapier, Grammarly
3. ShareASale — various SaaS tools
4. Amazon Associates — books, tech products
5. Direct programs — many SaaS tools have their own

Payouts (typical):
- HubSpot: $100-$500 per referral (CPL/CPA)
- Jasper: 30% recurring commission
- Brevo: €5 per signup + 15% recurring
- Surfer SEO: $29-$249 per referral (tiered)
- Canva: $15-$45 per referral
- Grammarly: $20 per signup
- Zapier: 15% recurring for 12 months
- Notion: 50% for 12 months

Usage:
    python3 scripts/affiliate_links.py  # Lists all affiliate links
    python3 scripts/affiliate_links.py --add "Tool Name" "https://affiliate-url.com"
    python3 scripts/affiliate_links.py --inject article.md  # Auto-link tool mentions
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
AFFILIATE_DB = ROOT / "affiliate_links.json"

# Default affiliate links (replace with YOUR affiliate URLs after signing up)
DEFAULT_LINKS = {
    "Jasper AI": "https://jasper.ai/?ref=AITOOLHUB",
    "Jasper": "https://jasper.ai/?ref=AITOOLHUB",
    "Canva": "https://canva.com/?ref=AITOOLHUB",
    "Canva Pro": "https://canva.com/pro?ref=AITOOLHUB",
    "Brevo": "https://brevo.com/?ref=AITOOLHUB",
    "HubSpot": "https://hubspot.com/?ref=AITOOLHUB",
    "Surfer SEO": "https://surferseo.com/?ref=AITOOLHUB",
    "OpusClip": "https://opusclip.com/?ref=AITOOLHUB",
    "ChatGPT Plus": "https://chat.openai.com/?ref=AITOOLHUB",
    "ChatGPT": "https://chat.openai.com/?ref=AITOOLHUB",
    "Grammarly": "https://grammarly.com/?ref=AITOOLHUB",
    "Notion": "https://notion.so/?ref=AITOOLHUB",
    "Notion AI": "https://notion.so/ai?ref=AITOOLHUB",
    "Zapier": "https://zapier.com/?ref=AITOOLHUB",
    "Intercom Fin": "https://intercom.com/fin?ref=AITOOLHUB",
    "Zendesk": "https://zendesk.com/?ref=AITOOLHUB",
    "Tidio": "https://tidio.com/?ref=AITOOLHUB",
    "Help Scout": "https://helpscout.com/?ref=AITOOLHUB",
    "Cursor": "https://cursor.sh/?ref=AITOOLHUB",
    "Claude Pro": "https://claude.ai/?ref=AITOOLHUB",
    "Gemini Advanced": "https://gemini.google.com/?ref=AITOOLHUB",
    "Zen Planner": "https://zenplanner.com/?ref=AITOOLHUB",
    "PushPress": "https://pushpress.com/?ref=AITOOLHUB",
    "Trainerize": "https://trainerize.com/?ref=AITOOLHUB",
}


def load_links():
    """Load affiliate links from JSON file, creating defaults if needed"""
    if not AFFILIATE_DB.exists():
        AFFILIATE_DB.write_text(json.dumps(DEFAULT_LINKS, indent=2))
        print(f"Created {AFFILIATE_DB} with default links")
        print("⚠️  Replace these with YOUR real affiliate URLs!")
    return json.loads(AFFILIATE_DB.read_text())


def inject_affiliate_links(article_path):
    """Find tool mentions in an article and add affiliate links.
    Only injects into the body — skips title line and frontmatter."""
    links = load_links()
    content = article_path.read_text()
    modified = False

    # Split into lines, skip title (first # heading) and frontmatter
    lines = content.split("\n")
    in_frontmatter = False
    title_line_idx = None
    body_start_idx = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
                body_start_idx = i + 1
            continue
        if stripped.startswith("# ") and title_line_idx is None:
            title_line_idx = i
            body_start_idx = i + 1
            continue

    # Only process lines from body_start_idx onward
    body_lines = lines[body_start_idx:]
    body_content = "\n".join(body_lines)

    for tool_name, affiliate_url in sorted(links.items(), key=lambda x: -len(x[0])):
        # Skip if tool name already appears in a markdown link
        if f'[{tool_name}]' in body_content:
            continue
        # Find first occurrence in body only
        idx = body_content.find(tool_name)
        if idx == -1:
            continue
        replacement = f'[{tool_name}]({affiliate_url})'
        body_content = body_content[:idx] + replacement + body_content[idx + len(tool_name):]

    # Reconstruct
    new_content = "\n".join(lines[:body_start_idx]) + "\n" + body_content

    if new_content != content:
        article_path.write_text(new_content)
        print(f"  ✓ Injected affiliate links into {article_path.name}")
        modified = True
    else:
        print(f"  - No new tool mentions found in {article_path.name}")

    return modified


def list_links():
    """Print all configured affiliate links"""
    links = load_links()
    print(f"\n{'='*60}")
    print(f"Affiliate Links ({len(links)} tools)")
    print(f"{'='*60}")
    for tool, url in sorted(links.items()):
        print(f"  {tool:25s} → {url}")
    print(f"\nFile: {AFFILIATE_DB}")


def add_link(tool_name, url):
    """Add or update an affiliate link"""
    links = load_links()
    links[tool_name] = url
    AFFILIATE_DB.write_text(json.dumps(links, indent=2))
    print(f"  ✓ Added: {tool_name} → {url}")


def main():
    if "--list" in sys.argv or len(sys.argv) == 1:
        list_links()
    elif "--add" in sys.argv:
        idx = sys.argv.index("--add")
        add_link(sys.argv[idx + 1], sys.argv[idx + 2])
    elif "--inject" in sys.argv:
        idx = sys.argv.index("--inject")
        article_path = Path(sys.argv[idx + 1])
        inject_affiliate_links(article_path)
    elif "--inject-all" in sys.argv:
        content_dir = ROOT / "content"
        for md_file in content_dir.glob("*.md"):
            inject_affiliate_links(md_file)
    else:
        print("Usage:")
        print("  python3 affiliate_links.py --list")
        print("  python3 affiliate_links.py --add 'Tool Name' 'https://affiliate-url.com'")
        print("  python3 affiliate_links.py --inject article.md")
        print("  python3 affiliate_links.py --inject-all")


if __name__ == "__main__":
    main()
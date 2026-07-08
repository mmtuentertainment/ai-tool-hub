#!/usr/bin/env python3
"""
AI Tool Hub - Static Site Generator
Converts markdown articles to HTML, builds index pages, copies static assets.
No dependencies — uses only Python stdlib.
"""

import os
import re
import shutil
import html
from datetime import datetime
from pathlib import Path

# Paths
ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "public"


def parse_frontmatter(text):
    """Parse simple YAML-like frontmatter (Date, Tags, Description)"""
    lines = text.strip().split("\n")
    meta = {}
    body_start = 0

    # Check for frontmatter block
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            line = lines[i]
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip().lower()] = val.strip()
            i += 1
        body_start = i + 1  # Skip closing ---

    # If no frontmatter block, parse leading metadata
    if not meta:
        for i, line in enumerate(lines):
            if line.startswith("#"):
                body_start = i
                break
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip().lower()] = val.strip()

    body = "\n".join(lines[body_start:])
    return meta, body


def md_to_html(md_text):
    """Convert markdown to HTML (minimal subset, no deps)"""
    # Extract title (first # heading)
    title_match = re.match(r"^#\s+(.+)$", md_text, re.MULTILINE)
    title = title_match.group(1) if title_match else "Untitled"

    # Remove the title from body (we'll render it separately)
    body = re.sub(r"^#\s+.+\n", "", md_text, count=1)

    # Convert
    html_body = body

    # Code blocks (```)
    html_body = re.sub(
        r"```(\w*)\n(.*?)```",
        lambda m: f'<pre><code>{html.escape(m.group(2))}</code></pre>',
        html_body,
        flags=re.DOTALL
    )

    # Headings
    html_body = re.sub(r"^###\s+(.+)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^##\s+(.+)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)

    # Bold
    html_body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_body)

    # Italic
    html_body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html_body)

    # Links
    html_body = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" rel="noopener" target="_blank">\1</a>',
        html_body,
    )

    # Images
    html_body = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        r'<img src="\2" alt="\1">',
        html_body,
    )

    # Tables (basic support)
    if "|" in html_body and "---" in html_body:
        lines = html_body.split("\n")
        result = []
        in_table = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if all(re.match(r"^[-:]+$", c) for c in cells):
                    # Header separator row — skip
                    continue
                if not in_table:
                    result.append("<table>")
                    result.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
                    in_table = True
                else:
                    result.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            else:
                if in_table:
                    result.append("</table>")
                    in_table = False
                result.append(line)
        if in_table:
            result.append("</table>")
        html_body = "\n".join(result)

    # Blockquotes
    html_body = re.sub(
        r"^>\s*(.+)$",
        r"<blockquote>\1</blockquote>",
        html_body,
        flags=re.MULTILINE,
    )

    # Unordered lists
    html_body = re.sub(
        r"^- (.+)$",
        r"<li>\1</li>",
        html_body,
        flags=re.MULTILINE,
    )
    # Wrap consecutive <li> in <ul>
    html_body = re.sub(
        r"(<li>.*?</li>\n?)+",
        lambda m: f"<ul>{m.group(0)}</ul>",
        html_body,
        flags=re.DOTALL,
    )

    # Ordered lists
    html_body = re.sub(
        r"^\d+\.\s+(.+)$",
        r"<li>\1</li>",
        html_body,
        flags=re.MULTILINE,
    )

    # Horizontal rule
    html_body = re.sub(r"^---+$", r"<hr>", html_body, flags=re.MULTILINE)

    # Callout blocks (> blockquote with strong)
    html_body = re.sub(
        r"<blockquote>(.+?)</blockquote>",
        r'<div class="callout">\1</div>',
        html_body,
        flags=re.DOTALL,
    )

    # Paragraphs (split on double newline, wrap text that isn't already a tag)
    paragraphs = []
    for block in html_body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        # Skip if block already starts with a block-level tag
        if re.match(r"^<(h[1-3]|ul|ol|li|pre|table|tr|td|th|hr|div|blockquote)", block):
            paragraphs.append(block)
        else:
            # It's a paragraph
            block = block.replace("\n", "<br>\n")
            paragraphs.append(f"<p>{block}</p>")

    html_body = "\n\n".join(paragraphs)

    return title, html_body


def load_template():
    """Load the base HTML template"""
    template_path = TEMPLATES_DIR / "base.html"
    with open(template_path) as f:
        return f.read()


def load_blog_template():
    """Load the blog article HTML template (relative paths for /blog/ pages)"""
    template_path = TEMPLATES_DIR / "blog_base.html"
    with open(template_path) as f:
        return f.read()


def slugify(text):
    """Convert title to URL slug"""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug


def build_article_page(template, title, body_html, meta):
    """Build a full article HTML page"""
    page = template.replace("{{title}}", html.escape(title))
    page = page.replace("{{meta_description}}", html.escape(meta.get("description", title)))

    article_html = f"""<article>
<h1>{html.escape(title)}</h1>
<div class="meta">Published {meta.get('date', 'Recently')} · {meta.get('tags', '')}</div>
{body_html}
</article>"""

    page = page.replace("{{content}}", article_html)
    return page


def build_index_page(template, articles):
    """Build the blog index page with article cards"""
    cards = []
    for article in sorted(articles, key=lambda a: a.get("date", ""), reverse=True):
        slug = article["slug"]
        title = article["title"]
        date = article.get("date", "")
        desc = article.get("description", "")
        card = f"""<a href="blog/{slug}.html" class="article-card">
<h2>{html.escape(title)}</h2>
<div class="meta">{date}</div>
<p>{html.escape(desc[:150])}...</p>
</a>"""
        cards.append(card)

    content = f"""<h1>AI Tool Hub</h1>
<p>Practical, tested advice on AI tools for small businesses and startups. No fluff, no hype — just what actually works.</p>
<div class="article-grid">
{chr(10).join(cards)}
</div>"""

    page = template.replace("{{title}}", "AI Tool Hub")
    page = page.replace("{{meta_description}}", "Practical AI tool reviews and guides for small businesses")
    page = page.replace("{{content}}", content)
    return page


def build():
    """Build the entire site"""
    # Clean output dir
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Copy static files
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, OUTPUT_DIR / "static")

    template = load_template()
    blog_template = load_blog_template()

    # Process all markdown articles
    articles = []
    for md_file in sorted(CONTENT_DIR.glob("*.md")):
        with open(md_file) as f:
            text = f.read()

        meta, body_md = parse_frontmatter(text)
        title, body_html = md_to_html(body_md)
        slug = slugify(title)

        # Save article metadata for index
        articles.append({
            "title": title,
            "slug": slug,
            "date": meta.get("date", ""),
            "description": meta.get("description", ""),
            "tags": meta.get("tags", ""),
        })

        # Build article page (use blog template with relative paths)
        page_html = build_article_page(blog_template, title, body_html, meta)

        # Write to /blog/slug.html
        blog_dir = OUTPUT_DIR / "blog"
        blog_dir.mkdir(exist_ok=True)
        with open(blog_dir / f"{slug}.html", "w") as f:
            f.write(page_html)

        print(f"  ✓ {slug}.html")

    # Build index page (homepage)
    index_html = build_index_page(template, articles)
    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(index_html)
    print("  ✓ index.html")

    # Build /blog.html (all articles listing)
    blog_index = build_index_page(template, articles)
    blog_dir = OUTPUT_DIR / "blog"
    blog_dir.mkdir(exist_ok=True)
    with open(blog_dir / "index.html", "w") as f:
        f.write(blog_index)
    print("  ✓ blog/index.html")

    # Build about page
    about_html = template.replace("{{title}}", "About")
    about_html = about_html.replace("{{meta_description}}", "About AI Tool Hub")
    about_content = """<article>
<h1>About AI Tool Hub</h1>
<p>AI Tool Hub provides practical, hands-on reviews and guides about AI tools for small businesses. We test every tool we recommend. We don't write fluff. We don't promote tools we haven't used.</p>
<h2>Affiliate Disclosure</h2>
<p>Some links on this site are affiliate links. If you click through and sign up, we may earn a commission at no extra cost to you. This helps us keep the site running. We only recommend tools we've actually tested and believe in.</p>
</article>"""
    about_html = about_html.replace("{{content}}", about_content)
    with open(OUTPUT_DIR / "about.html", "w") as f:
        f.write(about_html)
    print("  ✓ about.html")

    print(f"\n✅ Site built: {OUTPUT_DIR}")
    print(f"   {len(articles)} articles published")
    return articles


if __name__ == "__main__":
    print("Building AI Tool Hub...")
    build()
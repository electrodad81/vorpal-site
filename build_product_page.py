#!/usr/bin/env python3
"""
build_product_page.py — Generate single-product landing pages for affiliate conversion.

Each page lives at {site-repo}/{slug}/index.html, mapping to vorpalcollectibles.com/{slug}.
Designed for mobile-first, single-CTA conversion from YouTube Shorts verbal callouts.

Usage:
    python build_product_page.py \
      --sku blfbas72219 \
      --slug godzilla \
      --amazon-url "https://amzn.to/XXXXX" \
      --ee-url "https://ee.toys/PVVZVJ" \
      --data-dir ~/ee-shortmaker/out/images \
      --manifest ~/ee-shortmaker/data/manifest.json

    # Bundle with multiple SKUs:
    python build_product_page.py \
      --skus "blfbas72219,mst25645,mst25980" \
      --slug godzilla \
      --ee-url "https://ee.toys/PVVZVJ"
"""

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GA4_ID = "G-GHHF8WK335"
YOUTUBE_CHANNEL = "https://youtube.com/@VorpalCollectibles"


def load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        print(f"WARNING: Manifest not found at {manifest_path}", file=sys.stderr)
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scraped_json(sku: str, data_dir: Path) -> dict:
    json_path = data_dir / sku / f"{sku}.json"
    if not json_path.exists():
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_opinion(video_script: str) -> str:
    """Extract first 2 sentences from video_script for the opinion blurb."""
    if not video_script:
        return ""
    # Strip the "Title: " prefix that some scripts have
    text = re.sub(r'^[^:]+:\s*', '', video_script, count=1)
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:2]).strip()


def get_product_data(sku: str, manifest: dict, data_dir: Path) -> dict:
    """Gather product data from manifest and scraped JSON."""
    m = manifest.get(sku, manifest.get(sku.upper(), manifest.get(sku.lower(), {})))
    scraped = load_scraped_json(sku, data_dir)

    title = m.get("title") or scraped.get("title") or scraped.get("name") or ""
    image_url = m.get("image_url") or scraped.get("image_url") or ""
    if not image_url and scraped.get("imageUrls"):
        image_url = scraped["imageUrls"][0]

    video_id = m.get("youtube_video_id") or ""
    video_script = m.get("video_script") or ""
    price = m.get("price") or scraped.get("price") or ""
    brand = m.get("brand") or scraped.get("brand") or ""

    return {
        "title": title,
        "image_url": image_url,
        "video_id": video_id,
        "opinion": extract_opinion(video_script),
        "price": price,
        "brand": brand,
    }


def escape(s: str) -> str:
    """HTML-escape a string."""
    return html.escape(s, quote=True)


def build_landing_html(
    slug: str,
    products: list[dict],
    amazon_url: str | None,
    ee_url: str | None,
) -> str:
    """Generate the landing page HTML."""
    # Use first product as primary
    primary = products[0]
    title = primary["title"]
    image_url = primary["image_url"]
    opinion = primary["opinion"]
    price = primary["price"]

    # For bundles, combine titles
    if len(products) > 1:
        title = " + ".join(p["title"] for p in products if p["title"])

    year = datetime.now().year

    # Build CTA buttons
    cta_html = ""
    if amazon_url and ee_url:
        cta_html = f"""
            <a href="{escape(amazon_url)}" target="_blank" rel="noopener" class="btn-cta btn-amazon"
               onclick="trackClick('amazon_click', '{escape(slug)}', '{escape(title)}')">
                Buy on Amazon
            </a>
            <a href="{escape(ee_url)}" target="_blank" rel="noopener" class="btn-cta btn-ee"
               onclick="trackClick('ee_click', '{escape(slug)}', '{escape(title)}')">
                Buy at Entertainment Earth
            </a>"""
    elif amazon_url:
        cta_html = f"""
            <a href="{escape(amazon_url)}" target="_blank" rel="noopener" class="btn-cta btn-amazon"
               onclick="trackClick('amazon_click', '{escape(slug)}', '{escape(title)}')">
                Buy on Amazon
            </a>"""
    elif ee_url:
        cta_html = f"""
            <a href="{escape(ee_url)}" target="_blank" rel="noopener" class="btn-cta btn-ee-primary"
               onclick="trackClick('ee_click', '{escape(slug)}', '{escape(title)}')">
                Buy at Entertainment Earth
            </a>"""

    # Price display
    price_html = f'<div class="product-price">{escape(str(price))}</div>' if price else ""

    # Opinion text
    opinion_html = f'<p class="product-opinion">{escape(opinion)}</p>' if opinion else ""

    # Product image
    image_html = ""
    if image_url:
        image_html = f"""
        <div class="product-image">
            <img src="{escape(image_url)}" alt="{escape(title)}" loading="eager">
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA4_ID}');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} — Vorpal Collectibles</title>
    <meta name="description" content="{escape(opinion[:160] if opinion else title)}">
    <meta property="og:title" content="{escape(title)} — Vorpal Collectibles">
    <meta property="og:description" content="{escape(opinion[:200] if opinion else title)}">
    <meta property="og:image" content="{escape(image_url)}">
    <meta property="og:type" content="product">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0c;
            --bg-card: #131318;
            --border-subtle: #1e1e28;
            --text-primary: #e8e6f0;
            --text-secondary: #8a879a;
            --text-muted: #5c596a;
            --accent-vorpal: #c94a4a;
            --font-display: 'Oswald', sans-serif;
            --font-body: 'Source Sans 3', sans-serif;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-body);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* Logo bar */
        .logo-bar {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-subtle);
        }}

        .logo-bar a {{
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            text-decoration: none;
            color: var(--text-primary);
        }}

        .logo-icon {{
            width: 36px;
            height: 36px;
            background: var(--accent-vorpal);
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.2rem;
            color: white;
        }}

        .logo-text {{
            font-family: var(--font-display);
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}

        .logo-text span {{ color: var(--accent-vorpal); }}

        /* Main content */
        .landing-content {{
            max-width: 480px;
            margin: 0 auto;
            padding: 1.5rem 1.25rem 3rem;
        }}

        /* Product image */
        .product-image {{
            text-align: center;
            margin-bottom: 1.5rem;
        }}

        .product-image img {{
            max-width: 100%;
            max-height: 400px;
            object-fit: contain;
            border-radius: 8px;
        }}

        /* Product title */
        .product-title {{
            font-family: var(--font-display);
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            line-height: 1.3;
            margin-bottom: 0.5rem;
            text-align: center;
        }}

        /* Price */
        .product-price {{
            font-family: var(--font-display);
            font-size: 1.4rem;
            font-weight: 600;
            text-align: center;
            margin-bottom: 0.75rem;
        }}

        /* Opinion */
        .product-opinion {{
            color: var(--text-secondary);
            font-size: 1rem;
            font-weight: 400;
            text-align: center;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }}

        /* CTA buttons */
        .cta-section {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-bottom: 2rem;
        }}

        .btn-cta {{
            display: block;
            text-align: center;
            text-decoration: none;
            font-family: var(--font-display);
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            transition: all 0.2s;
            font-size: 1.1rem;
        }}

        .btn-amazon {{
            background: #2e8b57;
            color: white;
            font-size: 1.2rem;
            padding: 1.1rem 1.5rem;
        }}

        .btn-amazon:hover {{
            background: #3aa06a;
            transform: scale(1.02);
        }}

        .btn-ee {{
            background: var(--bg-card);
            color: var(--text-primary);
            border: 1px solid var(--border-subtle);
            font-size: 1rem;
        }}

        .btn-ee:hover {{
            border-color: var(--accent-vorpal);
            background: rgba(201, 74, 74, 0.1);
        }}

        /* When EE is the only/primary button */
        .btn-ee-primary {{
            background: var(--accent-vorpal);
            color: white;
            font-size: 1.2rem;
            padding: 1.1rem 1.5rem;
        }}

        .btn-ee-primary:hover {{
            background: #d65a5a;
            transform: scale(1.02);
        }}

        /* Footer */
        .landing-footer {{
            text-align: center;
            padding: 1.5rem 1rem;
            border-top: 1px solid var(--border-subtle);
        }}

        .affiliate-note {{
            font-size: 0.75rem;
            color: var(--text-muted);
            line-height: 1.5;
        }}

        .footer-copy {{
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }}
    </style>
</head>
<body>

    <div class="logo-bar">
        <a href="{YOUTUBE_CHANNEL}" target="_blank" rel="noopener">
            <div class="logo-icon">V</div>
            <div class="logo-text">Vorpal <span>Collectibles</span></div>
        </a>
    </div>

    <main class="landing-content">
        {image_html}

        <h1 class="product-title">{escape(title)}</h1>
        {price_html}
        {opinion_html}

        <div class="cta-section">
            {cta_html}
        </div>
    </main>

    <footer class="landing-footer">
        <p class="affiliate-note">Affiliate links — purchases support Vorpal Collectibles at no extra cost to you.</p>
        <p class="footer-copy">&copy; {year} Vorpal Collectibles / DR Commerce LLC</p>
    </footer>

    <script>
    function trackClick(event, slug, title) {{
        if (typeof gtag !== 'undefined') {{
            gtag('event', event, {{
                'product_slug': slug,
                'product_title': title
            }});
        }}
    }}
    </script>

</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Build a single-product landing page for affiliate conversion.",
    )
    sku_group = parser.add_mutually_exclusive_group(required=True)
    sku_group.add_argument("--sku", help="Single product SKU")
    sku_group.add_argument("--skus", help="Comma-separated SKUs for bundles")

    parser.add_argument("--slug", required=True, help="URL slug (e.g. 'godzilla')")
    parser.add_argument("--amazon-url", default=None, help="Amazon affiliate URL")
    parser.add_argument("--ee-url", default=None, help="Entertainment Earth affiliate URL")
    parser.add_argument(
        "--data-dir", type=Path,
        default=Path(__file__).resolve().parent.parent / "business_docs" / "ee-shortmaker" / "out" / "images",
        help="Path to scraped images directory",
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path(__file__).resolve().parent.parent / "business_docs" / "ee-shortmaker" / "data" / "manifest.json",
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--site-dir", type=Path, default=SCRIPT_DIR,
        help="Path to vorpal-site repo root (default: this script's directory)",
    )
    parser.add_argument("--deploy", action="store_true", help="Git add, commit, push after build")

    args = parser.parse_args()

    if not args.amazon_url and not args.ee_url:
        print("ERROR: At least one of --amazon-url or --ee-url is required.", file=sys.stderr)
        sys.exit(1)

    skus = [args.sku] if args.sku else [s.strip() for s in args.skus.split(",") if s.strip()]

    manifest = load_manifest(args.manifest)

    products = []
    for sku in skus:
        data = get_product_data(sku, manifest, args.data_dir)
        if not data["title"]:
            print(f"WARNING: No title found for SKU {sku}", file=sys.stderr)
        products.append(data)

    html_content = build_landing_html(
        slug=args.slug,
        products=products,
        amazon_url=args.amazon_url,
        ee_url=args.ee_url,
    )

    output_dir = args.site_dir / args.slug
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"Built landing page: {output_path}", file=sys.stderr)
    print(f"  URL: vorpalcollectibles.com/{args.slug}", file=sys.stderr)
    print(f"  SKUs: {', '.join(skus)}", file=sys.stderr)
    print(f"  Amazon: {args.amazon_url or 'none'}", file=sys.stderr)
    print(f"  EE: {args.ee_url or 'none'}", file=sys.stderr)

    if args.deploy:
        import subprocess
        site_dir = args.site_dir
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        cmds = [
            ["git", "add", f"{args.slug}/index.html"],
            ["git", "commit", "-m", f"Add {args.slug} landing page ({timestamp})"],
            ["git", "push"],
        ]
        for cmd in cmds:
            print(f"[DEPLOY] {' '.join(cmd)}", file=sys.stderr)
            result = subprocess.run(cmd, cwd=str(site_dir))
            if result.returncode != 0:
                print(f"[DEPLOY] Failed: {cmd}", file=sys.stderr)
                sys.exit(1)
        print(f"[DEPLOY] Pushed. Page will be live at vorpalcollectibles.com/{args.slug}", file=sys.stderr)


if __name__ == "__main__":
    main()

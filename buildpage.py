#!/usr/bin/env python3
"""
Build the Vorpal Collectibles shop page from product_hub_data.json.

Reads product data from the video pipeline's export and generates a complete
shop/index.html in the vorpal-site repo, then optionally git commits and pushes
to trigger Netlify auto-deploy.

Usage:
    # Generate shop page only
    python scripts/build_shop.py

    # Generate and auto-deploy (git add + commit + push)
    python scripts/build_shop.py --deploy

    # Custom paths
    python scripts/build_shop.py --data path/to/product_hub_data.json --site-repo path/to/vorpal-site

    # Dry run (print stats, don't write)
    python scripts/build_shop.py --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# Default paths — adjust if your repos are elsewhere
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "product_hub_data.json"
DEFAULT_SITE_REPO = PROJECT_ROOT

# Brand display names: slug -> label
BRAND_DISPLAY = {
    "hasbro": "Hasbro",
    "iron-studios": "Iron Studios",
    "mcfarlane": "McFarlane",
    "playmates": "Playmates",
    "mezco": "Mezco",
    "super7": "Super7",
    "bandai": "Bandai",
    "funko": "Funko",
    "mondo": "Mondo",
    "dc-direct": "DC Direct",
    "neca": "NECA",
    "hot-toys": "Hot Toys",
    "kotobukiya": "Kotobukiya",
    "lego": "LEGO",
    "four-horsemen": "Four Horsemen",
    "joy-toy": "Joy Toy",
    "warhammer": "Warhammer",
    "blokees": "Blokees",
    "youtooz": "Youtooz",
    "hiya-toys": "Hiya Toys",
    "beast-kingdom": "Beast Kingdom",
    "banpresto": "Banpresto",
    "takara-tomy": "Takara Tomy",
    "mattel": "Mattel",
}

# Minimum product count for a brand to get its own filter button
BRAND_FILTER_THRESHOLD = 3


def load_products(data_path: Path) -> list:
    """Load and validate product_hub_data.json."""
    if not data_path.exists():
        print(f"ERROR: Product data not found at {data_path}", file=sys.stderr)
        print("Run: python scripts/export_product_hub.py", file=sys.stderr)
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Filter to active only
    active = [p for p in products if p.get("status") == "active"]
    print(f"Loaded {len(products)} products, {len(active)} active", file=sys.stderr)
    return active


def build_filter_buttons(products: list) -> str:
    """Generate filter button HTML from product brand distribution."""
    brand_counts = Counter(p.get("brand", "unknown") for p in products)

    # Brands with enough products to warrant a filter, sorted by count desc
    filter_brands = [
        brand
        for brand, count in brand_counts.most_common()
        if count >= BRAND_FILTER_THRESHOLD and brand != "unknown"
    ]

    buttons = ['        <button class="filter-btn active" data-brand="all">All</button>']
    for slug in filter_brands:
        label = BRAND_DISPLAY.get(slug, slug.replace("-", " ").title())
        buttons.append(
            f'        <button class="filter-btn" data-brand="{slug}">{label}</button>'
        )

    return "\n".join(buttons)


def escape_js_string(s: str) -> str:
    """Escape a string for safe embedding in a JS double-quoted string literal."""
    if not s:
        return ""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
        .replace("</", "<\\/")
    )


def build_product_js_array(products: list) -> str:
    """Generate the JavaScript products array from product data."""
    lines = []
    for p in products:
        # Build each product object on one line for compact output
        obj_parts = []
        for key in [
            "id", "title", "brand", "description", "price", "preorder",
            "eta", "affiliate_url", "video_id", "video_type", "image_url",
            "date_added", "date_published", "date_uploaded", "status",
        ]:
            val = p.get(key, "")
            if isinstance(val, bool):
                obj_parts.append(f'{key}: {"true" if val else "false"}')
            elif isinstance(val, (int, float)):
                obj_parts.append(f"{key}: {val}")
            else:
                obj_parts.append(f'{key}: "{escape_js_string(str(val))}"')

        # Add vorpal_url if present
        vorpal_url = p.get("vorpal_url", "")
        if vorpal_url:
            obj_parts.append(f'vorpal_url: "{escape_js_string(vorpal_url)}"')

        lines.append(f"        {{ {', '.join(obj_parts)} }}")

    return ",\n".join(lines)


def build_html(products: list) -> str:
    """Generate the complete shop/index.html."""
    filter_buttons = build_filter_buttons(products)
    product_js = build_product_js_array(products)
    year = datetime.now().year

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-GHHF8WK335"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-GHHF8WK335');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vorpal Collectibles</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0c;
            --bg-card: #131318;
            --bg-card-hover: #1a1a22;
            --border-subtle: #1e1e28;
            --border-accent: #2a2a38;
            --text-primary: #e8e6f0;
            --text-secondary: #8a879a;
            --text-muted: #5c596a;
            --accent-vorpal: #c94a4a;
            --accent-vorpal-glow: rgba(201, 74, 74, 0.15);
            --accent-gold: #d4a853;
            --btn-buy: #2e8b57;
            --btn-buy-hover: #3aa06a;
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

        .site-header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(10, 10, 12, 0.92);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-subtle);
        }}

        .header-inner {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .logo-area {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .logo-icon {{
            width: 40px;
            height: 40px;
            background: var(--accent-vorpal);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.4rem;
            color: white;
        }}

        .logo-text {{
            font-family: var(--font-display);
            font-size: 1.3rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}

        .logo-text span {{ color: var(--accent-vorpal); }}

        .header-tagline {{
            font-size: 0.8rem;
            color: var(--text-muted);
            letter-spacing: 2px;
            text-transform: uppercase;
            font-weight: 500;
        }}

        .social-bar {{
            display: flex;
            gap: 1rem;
        }}

        .social-link {{
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            transition: color 0.2s;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .social-link:hover {{ color: var(--accent-vorpal); }}
        .social-link svg {{ width: 18px; height: 18px; fill: currentColor; }}

        .hero {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 3rem 1.5rem 2rem;
            text-align: center;
        }}

        .hero h1 {{
            font-family: var(--font-display);
            font-size: 2.4rem;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-vorpal) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .hero p {{
            color: var(--text-secondary);
            font-size: 1.05rem;
            max-width: 600px;
            margin: 0 auto;
            font-weight: 300;
        }}

        .filter-bar {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1.5rem 2rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            justify-content: center;
        }}

        .filter-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-family: var(--font-display);
            font-size: 0.85rem;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 0.5rem 1.1rem;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .filter-btn:hover {{
            border-color: var(--accent-vorpal);
            color: var(--text-primary);
            background: var(--accent-vorpal-glow);
        }}

        .filter-btn.active {{
            background: var(--accent-vorpal);
            border-color: var(--accent-vorpal);
            color: white;
        }}

        .products-grid {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1.5rem 4rem;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1.5rem;
        }}

        .product-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateY(20px);
            animation: cardIn 0.5s ease forwards;
        }}

        .product-card:hover {{
            border-color: var(--border-accent);
            background: var(--bg-card-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        }}

        @keyframes cardIn {{
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .product-card:nth-child(1) {{ animation-delay: 0.05s; }}
        .product-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .product-card:nth-child(3) {{ animation-delay: 0.15s; }}
        .product-card:nth-child(4) {{ animation-delay: 0.2s; }}
        .product-card:nth-child(5) {{ animation-delay: 0.25s; }}
        .product-card:nth-child(6) {{ animation-delay: 0.3s; }}

        .card-badge-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 1rem 0;
        }}

        .card-badge {{
            font-family: var(--font-display);
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--accent-gold);
        }}

        .card-date {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .card-media {{
            margin: 0.75rem 1rem;
            border-radius: 8px;
            overflow: hidden;
            aspect-ratio: 16/9;
            background: linear-gradient(135deg, #1a1a22 0%, #0a0a0c 100%);
            position: relative;
        }}

        .card-media iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}

        .card-media img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}

        .card-media .media-badge {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(201, 74, 74, 0.9);
            color: white;
            font-family: var(--font-display);
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            pointer-events: none;
        }}

        .card-media .coming-soon {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .card-body {{
            padding: 0.75rem 1rem 1rem;
        }}

        .card-title {{
            font-family: var(--font-display);
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            line-height: 1.3;
            margin-bottom: 0.4rem;
        }}

        .card-desc {{
            font-size: 0.88rem;
            color: var(--text-secondary);
            font-weight: 300;
            line-height: 1.5;
            margin-bottom: 1rem;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .card-footer {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
        }}

        .card-price {{
            font-family: var(--font-display);
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .card-price .preorder-note {{
            display: block;
            font-family: var(--font-body);
            font-size: 0.72rem;
            font-weight: 400;
            color: var(--accent-gold);
            letter-spacing: 0.5px;
        }}

        .btn-buy {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: var(--btn-buy);
            color: white;
            text-decoration: none;
            font-family: var(--font-display);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 0.65rem 1.2rem;
            border-radius: 6px;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .btn-buy:hover {{
            background: var(--btn-buy-hover);
            transform: scale(1.03);
        }}

        .btn-vorpal {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: #2563eb;
            color: white;
            text-decoration: none;
            font-family: var(--font-display);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 0.65rem 1.2rem;
            border-radius: 6px;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .btn-vorpal:hover {{
            background: #3b82f6;
            transform: scale(1.03);
        }}

        .btn-vorpal svg {{
            width: 14px;
            height: 14px;
            fill: currentColor;
        }}

        .btn-buy svg {{
            width: 14px;
            height: 14px;
            fill: currentColor;
        }}

        .site-footer {{
            border-top: 1px solid var(--border-subtle);
            padding: 2rem 1.5rem;
            text-align: center;
        }}

        .footer-inner {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .footer-affiliate-notice, .footer-copy {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}

        .no-results {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        @media (max-width: 768px) {{
            .header-tagline {{ display: none; }}
            .hero h1 {{ font-size: 1.7rem; }}
            .hero p {{ font-size: 0.95rem; }}
            .products-grid {{ grid-template-columns: 1fr; }}
            .card-footer {{
                flex-direction: column;
                align-items: stretch;
                text-align: center;
            }}
            .btn-buy {{ justify-content: center; }}
        }}
    </style>
</head>
<body>

    <!-- HEADER -->
    <header class="site-header">
        <div class="header-inner">
            <div class="logo-area">
                <div class="logo-icon">V</div>
                <div>
                    <div class="logo-text">Vorpal <span>Collectibles</span></div>
                </div>
            </div>
            <span class="header-tagline">As Seen on Our Channel</span>
            <div class="social-bar">
                <a href="https://youtube.com/@VorpalCollectibles" target="_blank" class="social-link">
                    <svg viewBox="0 0 24 24"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2 31.5 31.5 0 0 0 0 12a31.5 31.5 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1A31.5 31.5 0 0 0 24 12a31.5 31.5 0 0 0-.5-5.8zM9.6 15.6V8.4l6.3 3.6-6.3 3.6z"/></svg>
                    YouTube
                </a>
                <a href="https://tiktok.com/@VorpalCollectibles" target="_blank" class="social-link">
                    <svg viewBox="0 0 24 24"><path d="M19.3 5.3A4.5 4.5 0 0 1 16.5 2h-3.4v13.5a2.8 2.8 0 1 1-2-2.7V9.3a6.3 6.3 0 1 0 5.4 6.2V9.8a7.8 7.8 0 0 0 4.5 1.4V7.8a4.5 4.5 0 0 1-1.7-2.5z"/></svg>
                    TikTok
                </a>
            </div>
        </div>
    </header>

    <!-- HERO -->
    <section class="hero">
        <h1>Curated Collectibles Picks</h1>
        <p>Hand-picked action figures, statues, and collectibles featured on our channel. Every link supports Vorpal Collectibles.</p>
    </section>

    <!-- FILTERS -->
    <div class="filter-bar" id="filterBar">
{filter_buttons}
    </div>

    <!-- PRODUCTS -->
    <div class="products-grid" id="productsGrid"></div>

    <!-- FOOTER -->
    <footer class="site-footer">
        <div class="footer-inner">
            <p class="footer-affiliate-notice">Links on this page are affiliate links. Purchases made through these links help support Vorpal Collectibles at no extra cost to you.</p>
            <p class="footer-copy">&copy; {year} Vorpal Collectibles / DR Commerce LLC</p>
        </div>
    </footer>

    <script>
    const products = [
{product_js}
    ];

    const grid = document.getElementById('productsGrid');
    const filterBar = document.getElementById('filterBar');

    function renderProducts(filter) {{
        const active = products.filter(p => p.status === 'active');
        const filtered = filter === 'all'
            ? active
            : active.filter(p => {{
                if (filter === 'bandai') return p.brand.startsWith('bandai');
                return p.brand === filter;
            }});

        if (filtered.length === 0) {{
            grid.innerHTML = '<div class="no-results">No products found for this brand yet. Stay tuned!</div>';
            return;
        }}

        grid.innerHTML = filtered.map(p => {{
            let mediaContent;
            if (p.video_id) {{
                mediaContent = `
                    <iframe src="https://www.youtube.com/embed/${{p.video_id}}" loading="lazy" allowfullscreen></iframe>
                    <span class="media-badge">Watch Review</span>`;
            }} else if (p.image_url) {{
                mediaContent = `<img src="${{p.image_url}}" alt="${{p.title}}" loading="lazy">`;
            }} else {{
                mediaContent = `<div class="coming-soon">Coming soon</div>`;
            }}

            const priceDisplay = p.price
                ? `<div class="card-price">${{p.price}}</div>`
                : ``;

            const displayDate = p.date_published || p.date_uploaded || p.date_added;
            const dateStr = new Date(displayDate + 'T00:00:00').toLocaleDateString('en-US', {{
                month: 'short', day: 'numeric', year: 'numeric'
            }});

            return `
                <article class="product-card">
                    <div class="card-badge-row">
                        <span class="card-badge">${{p.brand.replace(/-/g, ' ')}}</span>
                        <span class="card-date">${{dateStr}}</span>
                    </div>
                    <div class="card-media">${{mediaContent}}</div>
                    <div class="card-body">
                        <h2 class="card-title">${{p.title}}</h2>
                        <p class="card-desc">${{p.description}}</p>
                        <div class="card-footer">
                            ${{priceDisplay}}
                            ${{p.vorpal_url
                                ? `<a href="${{p.vorpal_url}}" target="_blank" rel="noopener" class="btn-vorpal">
                                    <svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm10 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM7.2 14.8l.1-.2L8.1 13h7.5c.7 0 1.4-.4 1.7-1l3.9-7-1.7-1-3.9 7H8.5L4.3 2H1v2h2l3.6 7.6L5.2 14c-.1.3-.2.6-.2 1 0 1.1.9 2 2 2h12v-2H7.4c-.1 0-.2-.1-.2-.2z"/></svg>
                                    Buy from Vorpal
                                </a>`
                                : `<a href="${{p.affiliate_url}}" target="_blank" rel="noopener" class="btn-buy">
                                    <svg viewBox="0 0 24 24"><path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm10 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM7.2 14.8l.1-.2L8.1 13h7.5c.7 0 1.4-.4 1.7-1l3.9-7-1.7-1-3.9 7H8.5L4.3 2H1v2h2l3.6 7.6L5.2 14c-.1.3-.2.6-.2 1 0 1.1.9 2 2 2h12v-2H7.4c-.1 0-.2-.1-.2-.2z"/></svg>
                                    Buy at EE
                                </a>`
                            }}
                        </div>
                    </div>
                </article>`;
        }}).join('');
    }}

    filterBar.addEventListener('click', (e) => {{
        if (!e.target.classList.contains('filter-btn')) return;
        filterBar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        renderProducts(e.target.dataset.brand);
    }});

    renderProducts('all');

    // GA4 event tracking
    filterBar.addEventListener('click', function(e) {{
        if (!e.target.classList.contains('filter-btn')) return;
        if (typeof gtag !== 'undefined') {{
            gtag('event', 'filter_click', {{
                'filter_brand': e.target.dataset.brand
            }});
        }}
    }});

    document.addEventListener('click', function(e) {{
        const buyBtn = e.target.closest('.btn-buy');
        if (!buyBtn) return;
        const card = buyBtn.closest('.product-card');
        if (typeof gtag !== 'undefined') {{
            gtag('event', 'affiliate_click', {{
                'product_title': card.querySelector('.card-title')?.textContent || '',
                'product_brand': card.dataset.brand || '',
                'affiliate_url': buyBtn.href
            }});
        }}
    }});

    document.addEventListener('click', function(e) {{
        const vorpalBtn = e.target.closest('.btn-vorpal');
        if (!vorpalBtn) return;
        const card = vorpalBtn.closest('.product-card');
        if (typeof gtag !== 'undefined') {{
            gtag('event', 'vorpal_click', {{
                'product_title': card.querySelector('.card-title')?.textContent || '',
                'product_brand': card.dataset.brand || '',
                'vorpal_url': vorpalBtn.href
            }});
        }}
    }});

    </script>

</body>
</html>'''


def deploy(site_repo: Path) -> bool:
    """Git add, commit, push the vorpal-site repo."""
    try:
        os.chdir(site_repo)

        # Check if there are changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True,
        )
        if not result.stdout.strip():
            print("No changes to deploy.", file=sys.stderr)
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "add", "-A"], check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Auto-update shop page ({timestamp})"],
            check=True,
        )
        subprocess.run(["git", "push"], check=True)
        print("Deployed to Netlify via git push.", file=sys.stderr)
        return True

    except subprocess.CalledProcessError as e:
        print(f"Deploy failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Build Vorpal shop page from product data")
    parser.add_argument(
        "--data", type=Path, default=DEFAULT_DATA_PATH,
        help=f"Path to product_hub_data.json (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--site-repo", type=Path, default=DEFAULT_SITE_REPO,
        help=f"Path to vorpal-site git repo (default: {DEFAULT_SITE_REPO})",
    )
    parser.add_argument("--deploy", action="store_true", help="Git commit and push after build")
    parser.add_argument("--dry-run", action="store_true", help="Print stats only, don't write")
    args = parser.parse_args()

    products = load_products(args.data)

    if args.dry_run:
        brand_counts = Counter(p.get("brand", "unknown") for p in products)
        print(f"\n{'Brand':<20} {'Count':>5}")
        print("-" * 27)
        for brand, count in brand_counts.most_common():
            print(f"{brand:<20} {count:>5}")
        print(f"\nTotal active products: {len(products)}")
        print(f"With video: {sum(1 for p in products if p.get('video_id'))}")
        print(f"With image: {sum(1 for p in products if p.get('image_url'))}")
        print(f"With price: {sum(1 for p in products if p.get('price'))}")
        return

    html = build_html(products)

    output_dir = args.site_repo / "shop"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Wrote {len(products)} products to {output_path}", file=sys.stderr)

    if args.deploy:
        deploy(args.site_repo)


if __name__ == "__main__":
    main()
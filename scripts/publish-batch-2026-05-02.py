#!/usr/bin/env python3
"""
Publish script for batch 2026-05-02 (20 articles).
Fetches stock images from Unsplash (Pexels fallback), then POSTs to Shopify.

Usage:
    SHOPIFY_TOKEN=xxx UNSPLASH_ACCESS_KEY=yyy python3 scripts/publish-batch-2026-05-02.py
    # Optionally also set PEXELS_API_KEY for Pexels fallback

Requirements: requests (pip install requests)
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")

ARTICLES_DIR = Path(__file__).parent.parent / "articles"

ARTICLES = [
    "vitamin-d-bone-health-women-after-40",
    "calcium-absorption-after-40-women",
    "omega-3-joint-health-after-40",
    "berberine-vs-inositol-insulin-resistance-after-40",
    "berberine-gut-health-microbiome-after-40",
    "stress-eating-after-40-women",
    "magnesium-glycinate-vs-malate-women-over-40",
    "does-coq10-help-energy-honest-review-after-40",
    "signs-you-need-more-copper-after-40",
    "signs-you-need-more-b6-after-40",
    "what-is-ampk-longevity-after-40",
    "what-are-telomeres-aging-after-40",
    "does-nmn-actually-work-honest-review-after-40",
    "how-to-improve-focus-concentration-after-40",
    "what-is-alpha-gpc-memory-after-40",
    "retinol-after-40-women-guide",
    "what-is-inositol-women-over-40",
    "exercise-heart-health-women-after-40",
    "alcohol-liver-health-after-40-women",
    "what-is-pqq-brain-energy-after-40",
]


def fetch_unsplash(query: str, orientation: str = "landscape") -> dict | None:
    """Return {url, credit_html} or None."""
    if not UNSPLASH_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1, "orientation": orientation},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=10,
        )
        data = resp.json()
        results = data.get("results", [])
        if not results:
            return None
        photo = results[0]
        url = photo["urls"]["regular"]
        name = photo["user"]["name"]
        profile = photo["user"]["links"]["html"]
        credit = (
            f'<p class="image-credit">Photo by '
            f'<a href="{profile}?utm_source=happy_aging&utm_medium=referral">{name}</a> on '
            f'<a href="https://unsplash.com/?utm_source=happy_aging&utm_medium=referral">Unsplash</a></p>'
        )
        return {"url": url, "credit_html": credit}
    except Exception as e:
        print(f"    Unsplash error: {e}")
        return None


def fetch_pexels(query: str) -> dict | None:
    """Return {url, credit_html} or None."""
    if not PEXELS_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": PEXELS_KEY},
            timeout=10,
        )
        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        photo = photos[0]
        url = photo["src"]["large"]
        name = photo["photographer"]
        profile = photo["photographer_url"]
        credit = (
            f'<p class="image-credit">Photo by '
            f'<a href="{profile}">({name})</a> on '
            f'<a href="https://www.pexels.com">Pexels</a></p>'
        )
        return {"url": url, "credit_html": credit}
    except Exception as e:
        print(f"    Pexels error: {e}")
        return None


def get_image(query: str) -> dict:
    """Try Unsplash, then Pexels, then return placeholder."""
    # Extract concise search terms from the DALL-E style prompt
    # Use first 8 words after "Photograph of a" if present
    match = re.search(r"Photograph of a (.+?)(?:,|shot on|editorial)", query, re.I)
    search_query = match.group(1).strip() if match else query[:80]

    result = fetch_unsplash(search_query)
    if result:
        print(f"    Image: Unsplash OK")
        return result

    result = fetch_pexels(search_query)
    if result:
        print(f"    Image: Pexels OK")
        return result

    print(f"    Image: no result — using placeholder")
    return {"url": "https://via.placeholder.com/1200x628?text=Happy+Aging", "credit_html": ""}


def inject_images(html: str, cover: dict, body_images: list[dict]) -> str:
    """Replace FETCH_FROM_API placeholder in product card; insert cover at top."""
    # Insert cover image after H1
    cover_html = (
        f'<img src="{cover["url"]}" alt="" class="article-cover" '
        f'style="width:100%;max-width:1200px;margin-bottom:1.5rem;">\n'
        f'{cover["credit_html"]}\n'
    )
    html = re.sub(r"(<h1>[^<]+</h1>)", r"\1\n" + cover_html, html, count=1)

    # Replace FETCH_FROM_API in product card with first body image URL (reasonable fallback)
    product_img_url = body_images[0]["url"] if body_images else cover["url"]
    html = html.replace('src="FETCH_FROM_API"', f'src="{product_img_url}"', 1)

    return html


def publish_article(slug: str) -> dict:
    meta_path = ARTICLES_DIR / f"{slug}.meta.json"
    html_path = ARTICLES_DIR / f"{slug}-final.html"

    if not meta_path.exists():
        return {"slug": slug, "status": "error", "detail": "meta.json not found"}
    if not html_path.exists():
        return {"slug": slug, "status": "error", "detail": "html file not found"}

    meta = json.loads(meta_path.read_text())
    html = html_path.read_text()

    print(f"\n[{slug}]")

    # Fetch cover image
    print("  Fetching cover image...")
    cover = get_image(meta.get("image_prompt", slug))

    # Fetch body images
    body_images = []
    for i, prompt in enumerate(meta.get("body_image_prompts", [])[:3]):
        print(f"  Fetching body image {i+1}...")
        body_images.append(get_image(prompt))
        time.sleep(0.5)  # rate-limit courtesy pause

    # Inject images into HTML
    final_html = inject_images(html, cover, body_images)

    # Build Shopify payload
    payload = {
        "article": {
            "title": meta["title"],
            "body_html": final_html,
            "author": "Happy Aging Team",
            "tags": meta.get("tags", ""),
            "published": True,
            "template_suffix": "timeline",
        }
    }

    # POST to Shopify
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={
                "X-Shopify-Access-Token": SHOPIFY_TOKEN,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            article_id = resp.json().get("article", {}).get("id", "unknown")
            print(f"  Published: Shopify article ID {article_id}")
            return {"slug": slug, "status": "published", "article_id": article_id}
        else:
            print(f"  Shopify error {resp.status_code}: {resp.text[:200]}")
            return {"slug": slug, "status": "error", "detail": f"HTTP {resp.status_code}", "body": resp.text[:400]}
    except Exception as e:
        print(f"  Request exception: {e}")
        return {"slug": slug, "status": "error", "detail": str(e)}


def main():
    if not SHOPIFY_TOKEN:
        print("ERROR: SHOPIFY_TOKEN env var not set", file=sys.stderr)
        sys.exit(1)
    if not UNSPLASH_KEY:
        print("WARNING: UNSPLASH_ACCESS_KEY not set — images will use placeholder")

    results = []
    for slug in ARTICLES:
        result = publish_article(slug)
        results.append(result)
        time.sleep(1)  # stay under Shopify rate limits (40 req/s leaky bucket)

    # Summary
    published = [r for r in results if r["status"] == "published"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"\n{'='*60}")
    print(f"Batch 2026-05-02 publish complete")
    print(f"  Published : {len(published)}/{len(ARTICLES)}")
    print(f"  Errors    : {len(errors)}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e['slug']}: {e.get('detail','')}")

    # Write results JSON
    results_path = ARTICLES_DIR / "batch-2026-05-02-publish-results.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()

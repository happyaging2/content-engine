#!/usr/bin/env python3
"""
Batch publish script for 2026-05-06 JARVIS content batch.
Publishes 20 articles to Shopify via REST API.
Usage: SHOPIFY_TOKEN=... python3 batch-2026-05-06-publish.py
"""

import os
import json
import time
import requests
from pathlib import Path

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
ARTICLES_DIR = Path(__file__).parent

BATCH_SLUGS = [
    "ampk-autophagy-connection-after-40",
    "phosphatidylserine-dosing-protocol-after-40",
    "best-time-to-take-supplements-guide-after-40",
    "how-long-supplements-take-to-work-after-40",
    "natural-ways-to-boost-dhea-after-40",
    "collagen-peptides-vs-bone-broth-after-40",
    "butyrate-gut-health-after-40",
    "iodine-deficiency-signs-after-40",
    "magnesium-anxiety-perimenopause-after-40",
    "manganese-bone-collagen-after-40",
    "epa-dha-omega3-difference-after-40",
    "whey-protein-women-over-40",
    "anti-aging-skincare-routine-after-40",
    "sleep-quality-markers-track-after-40",
    "gut-microbiome-weight-loss-connection-after-40",
    "nattokinase-heart-health-after-40",
    "vitamin-a-skin-women-over-40",
    "probiotics-skin-after-40",
    "what-is-glucomannan-after-40",
    "how-menopause-affects-muscle-mass-after-40",
]


def publish_article(slug: str) -> dict:
    html_path = ARTICLES_DIR / f"{slug}.html"
    meta_path = ARTICLES_DIR / f"{slug}.meta.json"

    if not html_path.exists() or not meta_path.exists():
        return {"slug": slug, "status": "error", "message": "Missing file"}

    body_html = html_path.read_text(encoding="utf-8")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    summary = meta.get("summary_html", "")
    if not summary:
        # Use first paragraph as meta description
        import re
        match = re.search(r"<p>(.*?)</p>", body_html, re.DOTALL)
        if match:
            summary = re.sub(r"<[^>]+>", "", match.group(1)).strip()[:155]

    payload = {
        "article": {
            "title": meta["title"],
            "body_html": body_html,
            "author": meta.get("author", "Happy Aging Team"),
            "tags": meta.get("tags", ""),
            "published": True,
            "template_suffix": "timeline",
            "metafields": [
                {
                    "key": "description_tag",
                    "value": summary,
                    "type": "single_line_text_field",
                    "namespace": "global",
                }
            ],
        }
    }

    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 201:
            article_id = resp.json()["article"]["id"]
            # Persist article ID back to meta
            meta["shopify_article_id"] = article_id
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            return {"slug": slug, "status": "published", "article_id": article_id}
        else:
            return {
                "slug": slug,
                "status": "error",
                "http_status": resp.status_code,
                "message": resp.text[:300],
            }
    except Exception as e:
        return {"slug": slug, "status": "error", "message": str(e)}


def main():
    if not SHOPIFY_TOKEN:
        print("ERROR: SHOPIFY_TOKEN environment variable not set")
        return

    results = []
    for i, slug in enumerate(BATCH_SLUGS, 1):
        print(f"[{i:02d}/20] Publishing {slug}...")
        result = publish_article(slug)
        results.append(result)
        print(f"       -> {result['status']}" + (f" (id={result.get('article_id')})" if result.get("article_id") else f": {result.get('message', '')}"))
        if i < len(BATCH_SLUGS):
            time.sleep(0.5)  # Rate limiting: 2 req/sec Shopify limit

    published = [r for r in results if r["status"] == "published"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"\n=== PUBLISH COMPLETE ===")
    print(f"Published: {len(published)}/20")
    print(f"Errors:    {len(errors)}/20")

    if errors:
        print("\nFailed articles:")
        for r in errors:
            print(f"  - {r['slug']}: {r.get('message', 'unknown')}")

    # Save results log
    log_path = ARTICLES_DIR / "batch-2026-05-06-publish-log.json"
    log_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nLog saved to: {log_path}")


if __name__ == "__main__":
    main()

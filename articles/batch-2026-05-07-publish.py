#!/usr/bin/env python3
"""
JARVIS Batch 26 — 2026-05-07
Publishes 20 articles to Shopify blog 109440303424
"""

import json
import os
import sys
import time
import requests

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "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")
API_URL = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))

ARTICLES = [
    "tart-cherry-sleep-after-40",
    "lemon-balm-sleep-anxiety-after-40",
    "apigenin-sleep-supplement-after-40",
    "maca-root-menopause-after-40",
    "red-clover-hot-flashes-after-40",
    "evening-primrose-oil-menopause-after-40",
    "turkey-tail-mushroom-immunity-after-40",
    "boswellia-joint-pain-after-40",
    "zeaxanthin-lutein-eye-health-after-40",
    "probiotics-vaginal-health-after-40",
    "how-to-heal-leaky-gut-after-40",
    "gut-serotonin-menopause-after-40",
    "saw-palmetto-hair-loss-women-after-40",
    "folate-skin-health-after-40",
    "why-skin-gets-dry-after-menopause",
    "saffron-mood-memory-after-40",
    "matcha-vs-coffee-brain-after-40",
    "l-theanine-focus-anxiety-after-40",
    "vitamin-d3-k2-synergy-after-40",
    "electrolytes-menopause-hydration-after-40",
]


def load_article(slug):
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")
    with open(html_path, "r") as f:
        body_html = f.read()
    with open(meta_path, "r") as f:
        meta = json.load(f)
    return body_html, meta


def publish_article(slug, dry_run=False):
    body_html, meta = load_article(slug)
    payload = {
        "article": {
            "title": meta["title"],
            "body_html": body_html,
            "author": meta["author"],
            "tags": meta["tags"],
            "published": True,
            "template_suffix": "timeline",
        }
    }
    if dry_run:
        print(f"  [DRY RUN] Would publish: {meta['title']}")
        return True, None

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json",
    }
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        article_id = resp.json().get("article", {}).get("id")
        return True, article_id
    else:
        return False, resp.text


def main():
    dry_run = "--dry-run" in sys.argv
    results = []
    print(f"JARVIS Batch 26 Publisher — 2026-05-07")
    print(f"Publishing {len(ARTICLES)} articles to blog {BLOG_ID}")
    print(f"Dry run: {dry_run}")
    print("-" * 60)

    for i, slug in enumerate(ARTICLES, 1):
        print(f"[{i:02d}/{len(ARTICLES)}] {slug}")
        try:
            ok, result = publish_article(slug, dry_run=dry_run)
            if ok:
                print(f"  OK — article_id: {result}")
                results.append({"slug": slug, "status": "published", "id": result})
            else:
                print(f"  FAILED — {result}")
                results.append({"slug": slug, "status": "failed", "error": result})
        except Exception as e:
            print(f"  ERROR — {e}")
            results.append({"slug": slug, "status": "error", "error": str(e)})
        if not dry_run:
            time.sleep(0.5)

    print("-" * 60)
    published = sum(1 for r in results if r["status"] == "published")
    failed = sum(1 for r in results if r["status"] in ("failed", "error"))
    print(f"Published: {published} | Failed: {failed}")

    out_path = os.path.join(ARTICLES_DIR, "batch-2026-05-07-publish-results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

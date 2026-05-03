#!/usr/bin/env python3
"""
Batch 2026-05-03 Shopify Publisher
Publishes 20 articles to shop-happy-aging.myshopify.com
"""

import json
import os
import time
import requests

SHOPIFY_TOKEN = "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"
SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
AUTHOR = "Happy Aging Team"
TEMPLATE_SUFFIX = "timeline"

API_URL = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"

ARTICLES = [
    "what-is-nicotinamide-riboside-nr-after-40",
    "citicoline-vs-alpha-gpc-focus-after-40",
    "rhodiola-rosea-fatigue-cognitive-after-40",
    "cortisol-sleep-disruption-after-40",
    "niacinamide-skin-health-after-40",
    "silicon-bone-collagen-after-40",
    "coq10-blood-pressure-heart-after-40",
    "chromium-blood-sugar-insulin-after-40",
    "zinc-carnosine-gut-lining-after-40",
    "thyroid-perimenopause-overlap-after-40",
    "nad-niacin-flushing-explained-after-40",
    "omega-3-triglycerides-menopause",
    "peptides-skin-aging-after-40",
    "pregnenolone-hormones-stress-after-40",
    "liver-detox-pathways-phase-1-phase-2-after-40",
    "best-time-to-take-coq10-women-after-40",
    "lactoferrin-immune-gut-health-after-40",
    "5-htp-mood-sleep-after-40",
    "mitochondria-aging-decline-after-40",
    "dry-eyes-estrogen-omega3-after-40",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

results = []

for slug in ARTICLES:
    meta_path = os.path.join(BASE_DIR, f"{slug}.meta.json")
    html_path = os.path.join(BASE_DIR, f"{slug}-final.html")

    with open(meta_path) as f:
        meta = json.load(f)

    with open(html_path) as f:
        body_html = f.read()

    title = meta["title"]
    tags = meta.get("tags", "")

    payload = {
        "article": {
            "title": title,
            "body_html": body_html,
            "author": AUTHOR,
            "tags": tags,
            "published": True,
            "template_suffix": TEMPLATE_SUFFIX,
        }
    }

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        status = resp.status_code
        if status == 201:
            article_id = resp.json()["article"]["id"]
            results.append({"slug": slug, "status": "published", "id": article_id})
            print(f"PUBLISHED [{status}]: {slug} -> id={article_id}")
        else:
            results.append({"slug": slug, "status": f"error_{status}", "body": resp.text[:200]})
            print(f"ERROR [{status}]: {slug} -> {resp.text[:200]}")
    except Exception as e:
        results.append({"slug": slug, "status": "exception", "error": str(e)})
        print(f"EXCEPTION: {slug} -> {e}")

    time.sleep(0.5)  # Rate limiting

print("\n=== SUMMARY ===")
published = [r for r in results if r["status"] == "published"]
errors = [r for r in results if r["status"] != "published"]
print(f"Published: {len(published)}/20")
print(f"Errors: {len(errors)}")

with open(os.path.join(BASE_DIR, "batch-2026-05-03-publish-results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("Results saved to batch-2026-05-03-publish-results.json")

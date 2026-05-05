#!/usr/bin/env python3
"""
Batch publish script for 2026-05-05.
Usage: SHOPIFY_TOKEN=... python3 articles/batch-2026-05-05-publish.py
"""

import os
import json
import time
import urllib.request
import urllib.error

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
TEMPLATE_SUFFIX = "timeline"

ARTICLES = [
    "menopause-fatigue-complete-guide-after-40",
    "taurine-benefits-heart-longevity-after-40",
    "iron-deficiency-fatigue-women-after-40",
    "best-magnesium-forms-women-over-40",
    "valerian-root-sleep-after-40",
    "evening-routine-better-sleep-after-40",
    "how-to-increase-progesterone-naturally-after-40",
    "what-is-shbg-women-over-40",
    "adaptogens-perimenopause-which-help-after-40",
    "vitamin-c-serum-after-40-guide",
    "omega-3-skin-hair-nails-after-40",
    "hyaluronic-acid-after-40-guide",
    "balance-blood-sugar-naturally-after-40",
    "l-carnitine-weight-loss-review-after-40",
    "what-is-hmb-muscle-after-40",
    "quercetin-benefits-complete-guide-after-40",
    "coq10-vs-ubiquinol-women-over-40",
    "what-is-pterostilbene-aging-after-40",
    "gut-motility-constipation-after-40",
    "signs-liver-needs-support-after-40",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_article(slug):
    meta_path = os.path.join(BASE_DIR, f"{slug}.meta.json")
    html_path = os.path.join(BASE_DIR, f"{slug}.html")
    with open(meta_path) as f:
        meta = json.load(f)
    with open(html_path) as f:
        body_html = f.read()
    return meta, body_html


def publish_article(slug):
    meta, body_html = load_article(slug)
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    payload = {
        "article": {
            "title": meta["title"],
            "body_html": body_html,
            "author": meta.get("author", "Happy Aging Team"),
            "tags": meta.get("tags", ""),
            "published": True,
            "template_suffix": TEMPLATE_SUFFIX,
            "handle": slug,
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            article_id = result["article"]["id"]
            return True, article_id
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, f"HTTP {e.code}: {body[:200]}"
    except Exception as ex:
        return False, str(ex)


def main():
    if not SHOPIFY_TOKEN:
        print("ERROR: SHOPIFY_TOKEN not set")
        return

    results = []
    for slug in ARTICLES:
        print(f"Publishing: {slug} ... ", end="", flush=True)
        ok, info = publish_article(slug)
        if ok:
            print(f"OK (id={info})")
            results.append({"slug": slug, "status": "published", "id": info})
        else:
            print(f"FAIL: {info}")
            results.append({"slug": slug, "status": "failed", "error": info})
        time.sleep(0.5)

    published = sum(1 for r in results if r["status"] == "published")
    failed = sum(1 for r in results if r["status"] == "failed")
    print(f"\nSummary: {published} published, {failed} failed")

    report_path = os.path.join(BASE_DIR, "batch-2026-05-05-publish-log.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Log written to {report_path}")


if __name__ == "__main__":
    main()

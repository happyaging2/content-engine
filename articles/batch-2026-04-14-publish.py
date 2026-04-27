#!/usr/bin/env python3
"""
Batch 2026-04-14 Shopify publish script.
Usage: SHOPIFY_TOKEN=shpat_... python3 batch-2026-04-14-publish.py
Note: articles use .html (not -final.html) for this batch.
"""

import os
import json
import time
import urllib.request
import urllib.error

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
AUTHOR = "Happy Aging Team"
TEMPLATE_SUFFIX = "timeline"
ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))

SLUGS = [
    "does-nad-plus-work-for-energy-after-40",
    "root-causes-chronic-fatigue-after-40",
    "what-to-eat-for-energy-after-40",
    "does-magnesium-actually-improve-sleep-after-40",
    "what-to-eat-for-better-sleep-after-40",
    "does-nmn-help-hormonal-balance-women-over-40",
    "root-causes-hormonal-imbalance-after-40",
    "what-to-eat-for-hormone-balance-after-40",
    "does-coq10-help-metabolism-weight-after-40",
    "root-causes-slow-metabolism-after-40-guide",
    "does-marine-collagen-work-for-skin-after-40",
    "what-to-eat-for-glowing-skin-after-40",
    "does-glutathione-work-for-gut-health-after-40",
    "what-to-eat-for-gut-health-after-40",
    "does-neuro-creamer-work-for-brain-focus-after-40",
    "root-causes-brain-fog-after-40-science",
    "what-to-eat-to-clear-brain-fog-after-40",
    "does-curcumin-work-for-inflammation-after-40",
    "root-causes-chronic-inflammation-after-40",
    "what-to-eat-fight-inflammation-after-40",
]


def load_article(slug):
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")
    # This batch has .html only (no -final.html)
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
    if not os.path.exists(html_path):
        html_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
    with open(meta_path, "r") as f:
        meta = json.load(f)
    with open(html_path, "r") as f:
        body_html = f.read()
    return meta, body_html


def publish_article(token, meta, body_html):
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    payload = {
        "article": {
            "title": meta["title"],
            "body_html": body_html,
            "author": AUTHOR,
            "tags": meta["tags"],
            "published": True,
            "template_suffix": TEMPLATE_SUFFIX,
            "handle": meta["slug"],
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    token = os.environ.get("SHOPIFY_TOKEN", "").strip()
    if not token:
        raise SystemExit("ERROR: Set SHOPIFY_TOKEN environment variable.")

    results = []
    total = len(SLUGS)
    for i, slug in enumerate(SLUGS, 1):
        print(f"[{i:02d}/{total}] Publishing {slug}...", end=" ", flush=True)
        try:
            meta, body_html = load_article(slug)
            resp = publish_article(token, meta, body_html)
            article_id = resp.get("article", {}).get("id", "?")
            print(f"OK (id={article_id})")
            results.append({"slug": slug, "status": "ok", "id": article_id})
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"FAILED HTTP {e.code}: {body[:200]}")
            results.append({"slug": slug, "status": f"http_{e.code}", "error": body[:200]})
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({"slug": slug, "status": "error", "error": str(e)})
        if i < total:
            time.sleep(0.6)

    ok = sum(1 for r in results if r["status"] == "ok")
    failed = total - ok
    print(f"\nDone: {ok}/{total} published, {failed} failed.")
    if failed:
        print("Failed slugs:")
        for r in results:
            if r["status"] != "ok":
                print(f"  {r['slug']}: {r.get('error', r['status'])}")


if __name__ == "__main__":
    main()

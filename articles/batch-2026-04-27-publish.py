#!/usr/bin/env python3
"""
Batch 2026-04-27 Shopify publish script.
Usage: SHOPIFY_TOKEN=shpat_... python3 batch-2026-04-27-publish.py
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
    "signs-low-vitamin-b6-after-40",
    "copper-deficiency-signs-after-40",
    "what-is-ergothioneine-after-40",
    "what-is-urolithin-a-after-40",
    "what-is-rapamycin-longevity-after-40",
    "nad-iv-vs-oral-supplements-after-40",
    "melatonin-dose-guide-women-over-40",
    "blue-light-sleep-after-40",
    "does-ashwagandha-help-perimenopause-symptoms",
    "how-stress-hormones-affect-sleep-after-40",
    "best-protein-sources-women-over-40",
    "spermidine-foods-autophagy-after-40",
    "what-is-sibo-after-40",
    "what-is-tributyrin-gut-health-after-40",
    "acetylcholine-memory-after-40",
    "what-is-bacopa-monnieri-after-40",
    "ceramides-skin-barrier-after-40",
    "collagen-type-1-vs-type-3-skin-after-40",
    "joint-inflammation-menopause-after-40",
    "heart-health-protocol-women-over-40",
]


def load_article(slug):
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
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
    for i, slug in enumerate(SLUGS, 1):
        print(f"[{i:02d}/20] Publishing {slug}...", end=" ", flush=True)
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
        if i < len(SLUGS):
            time.sleep(0.6)

    ok = sum(1 for r in results if r["status"] == "ok")
    failed = len(results) - ok
    print(f"\nDone: {ok}/20 published, {failed} failed.")
    if failed:
        print("Failed slugs:")
        for r in results:
            if r["status"] != "ok":
                print(f"  {r['slug']}: {r.get('error', r['status'])}")


if __name__ == "__main__":
    main()

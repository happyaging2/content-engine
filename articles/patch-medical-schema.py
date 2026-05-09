#!/usr/bin/env python3
"""
patch-medical-schema.py — Retroactively inject MedicalWebPage / Article schema
+ reviewer Person + HowTo on every published Shopify article.

Run once after deploying lib_medical_schema.py:
    SHOPIFY_TOKEN=shpat_... python3 articles/patch-medical-schema.py

Use --dry-run to preview without writing back to Shopify.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ARTICLES_DIR)
from lib_medical_schema import inject_medical_schema  # noqa: E402

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
DRY = "--dry-run" in sys.argv

if not TOKEN:
    raise SystemExit("ERROR: set SHOPIFY_TOKEN")

API = f"https://{SHOPIFY_STORE}/admin/api/2024-01"
HEADERS = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}


def _req(url, data=None, method="GET"):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def list_articles():
    out, page_info = [], None
    while True:
        qs = {"limit": 250}
        if page_info:
            qs["page_info"] = page_info
        url = f"{API}/blogs/{BLOG_ID}/articles.json?" + urllib.parse.urlencode(qs)
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        out.extend(data.get("articles", []))
        link = resp.headers.get("Link", "")
        if 'rel="next"' not in link:
            break
        # Parse next page_info
        for chunk in link.split(","):
            if 'rel="next"' in chunk:
                page_info = chunk.split("page_info=")[1].split(">")[0].split("&")[0]
                break
        else:
            break
        time.sleep(0.4)
    return out


def main():
    metas = {}
    for mf in glob.glob(os.path.join(ARTICLES_DIR, "*.meta.json")):
        m = json.load(open(mf))
        slug = m.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        metas[slug] = m

    print(f"[1/2] Loaded {len(metas)} local meta.json files.")
    print("[2/2] Fetching Shopify articles...")
    articles = list_articles()
    print(f"      {len(articles)} articles on Shopify.\n")

    updated = skipped = failed = 0
    for art in articles:
        slug = art["handle"]
        title = art["title"]
        meta = metas.get(slug, {})
        body = art.get("body_html") or ""
        if not body.strip():
            skipped += 1
            continue
        meta_desc = meta.get("meta_description", "") or art.get("summary_html") or ""
        new_body = inject_medical_schema(
            body, title=title, slug=slug, meta_desc=meta_desc, meta=meta
        )
        if new_body == body:
            skipped += 1
            continue
        if DRY:
            print(f"  DRY {slug[:60]} — would update")
            updated += 1
            continue
        try:
            _req(
                f"{API}/articles/{art['id']}.json",
                data={"article": {"id": art["id"], "body_html": new_body}},
                method="PUT",
            )
            updated += 1
            print(f"  ✓ {slug[:60]}")
            time.sleep(0.5)
        except urllib.error.HTTPError as e:
            failed += 1
            print(f"  ✗ {slug[:60]} — {e}")

    print(f"\nDone. updated={updated} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()

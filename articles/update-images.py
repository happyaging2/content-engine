#!/usr/bin/env python3
"""
Update already-published Shopify articles with images.
Fetches cover + body images from Unsplash (primary) / Pexels (fallback),
fixes product card image placeholders, then PUTs updated HTML to Shopify.

Usage:
    SHOPIFY_TOKEN=shpat_... UNSPLASH_ACCESS_KEY=... python3 update-images.py
    SHOPIFY_TOKEN=shpat_... PEXELS_API_KEY=...      python3 update-images.py  (Pexels only)
"""

import json
import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import glob

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))
UTM = "?utm_source=happy_aging&utm_medium=referral"

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "").strip()

if not SHOPIFY_TOKEN:
    raise SystemExit("ERROR: Set SHOPIFY_TOKEN environment variable.")
if not UNSPLASH_KEY and not PEXELS_KEY:
    raise SystemExit("ERROR: Set UNSPLASH_ACCESS_KEY and/or PEXELS_API_KEY.")


# ── Image search ──────────────────────────────────────────────────────────────

def unsplash_search(query):
    if not UNSPLASH_KEY:
        return None
    try:
        url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({
            "query": query, "orientation": "landscape", "per_page": 5, "content_filter": "high"
        })
        req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if not data.get("results"):
            return None
        p = data["results"][0]
        try:
            dl = urllib.request.Request(
                p["links"]["download_location"],
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"}
            )
            urllib.request.urlopen(dl, timeout=10)
        except Exception:
            pass
        return {
            "src": p["urls"]["regular"],
            "alt": (p.get("alt_description") or query)[:120],
            "credit_name": p["user"]["name"],
            "credit_url": p["user"]["links"]["html"] + UTM,
            "provider": "Unsplash",
            "provider_url": "https://unsplash.com/" + UTM,
        }
    except Exception as e:
        print(f"    unsplash fail '{query[:40]}': {str(e)[:60]}")
        return None


def pexels_search(query):
    if not PEXELS_KEY:
        return None
    try:
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode({
            "query": query, "orientation": "landscape", "per_page": 5
        })
        req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if not data.get("photos"):
            return None
        p = data["photos"][0]
        return {
            "src": p["src"]["large2x"],
            "alt": (p.get("alt") or query)[:120],
            "credit_name": p["photographer"],
            "credit_url": p["photographer_url"],
            "provider": "Pexels",
            "provider_url": "https://www.pexels.com/",
        }
    except Exception as e:
        print(f"    pexels fail '{query[:40]}': {str(e)[:60]}")
        return None


def find_image(query, fallback=None):
    img = unsplash_search(query) or pexels_search(query)
    if not img and fallback and fallback != query:
        img = unsplash_search(fallback) or pexels_search(fallback)
    time.sleep(1)
    return img


def query_from_dalle_prompt(prompt):
    """Extract a short Unsplash search query from a DALL-E image_prompt string.

    Example input:
      'Photograph of a 46-year-old woman eating pomegranate seeds at a kitchen counter...'
    Example output:
      'woman eating pomegranate kitchen healthy'
    """
    if not prompt:
        return None
    # Strip "Photograph of a XX-year-old woman" prefix
    text = re.sub(r"Photograph of a \d+-year-old woman\s*", "", prompt, flags=re.IGNORECASE)
    # Remove camera/technical specs (everything from "shot on" or "8K" onward)
    text = re.split(r",?\s*(shot on|8K|no watermark|editorial|no CGI)", text, flags=re.IGNORECASE)[0]
    # Take first 8 words, drop filler words
    words = text.strip().split()[:10]
    stop = {"a", "an", "the", "at", "in", "on", "with", "and", "or", "of", "from", "by", "her", "his"}
    keywords = [w.strip(".,;:") for w in words if w.lower().strip(".,;:") not in stop][:6]
    return "woman " + " ".join(keywords) if keywords else None


# ── Product card image fix ────────────────────────────────────────────────────

def fetch_product_image_map():
    pmap = {}
    try:
        req = urllib.request.urlopen("https://happyaging.com/products.json?limit=250", timeout=15)
        products = json.loads(req.read())["products"]
        for p in products:
            if p.get("images"):
                pmap[p["handle"]] = p["images"][0]["src"]
        print(f"  Fetched {len(pmap)} product images from Shopify store.")
    except Exception as e:
        print(f"  WARNING: Could not fetch product images: {e}")
    return pmap


def fix_product_card(html, pmap):
    for m in re.finditer(
        r'(product-card-inline.*?happyaging\.com/products/([a-z0-9-]+).*?<img[^>]+src=")([^"]+)(")',
        html, re.DOTALL
    ):
        handle = m.group(2)
        src = m.group(3)
        if "cdn.shopify.com" in src:
            continue
        real = pmap.get(handle)
        if real:
            html = html.replace(src, real)
    return html


# ── Body image injection ──────────────────────────────────────────────────────

def inject_body_images(html, imgs, title):
    if "article-stock-image" in html:
        return html
    h2s = [m.end() for m in re.finditer(r"</h2>", html)]
    if len(h2s) < 2 or not imgs:
        return html
    step = max(1, len(h2s) // (len(imgs) + 1))
    insert_points = h2s[step::step][:len(imgs)]
    for img, pos in zip(reversed(imgs), reversed(insert_points)):
        alt = (img.get("alt") or title)[:140].replace('"', "'")
        figure = (
            f'\n<figure class="article-stock-image" style="margin:24px 0">'
            f'<img src="{img["src"]}" alt="{alt}" '
            f'style="width:100%;border-radius:12px;display:block">'
            f'<figcaption style="font-size:12px;color:#888;margin-top:6px">'
            f'Photo by <a href="{img["credit_url"]}" rel="nofollow noopener">{img["credit_name"]}</a> '
            f'on <a href="{img["provider_url"]}" rel="nofollow noopener">{img["provider"]}</a>'
            f'</figcaption></figure>\n'
        )
        html = html[:pos] + figure + html[pos:]
    return html


# ── Shopify helpers ───────────────────────────────────────────────────────────

def shopify_get_articles():
    """Return dict of handle -> article_id for all published articles."""
    articles = {}
    page_info = None
    base = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    while True:
        params = {"limit": 250, "fields": "id,handle"}
        if page_info:
            params = {"limit": 250, "fields": "id,handle", "page_info": page_info}
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        for a in data.get("articles", []):
            articles[a["handle"]] = a["id"]
        link_header = resp.headers.get("Link", "")
        next_url = None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                next_url = part.strip().split(";")[0].strip("<> ")
        if not next_url:
            break
        pi_match = re.search(r"page_info=([^&]+)", next_url)
        if not pi_match:
            break
        page_info = pi_match.group(1)
    return articles


def shopify_update_article(article_id, body_html, cover_img, title):
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles/{article_id}.json"
    payload = {
        "article": {
            "id": article_id,
            "body_html": body_html,
        }
    }
    if cover_img and cover_img.get("src"):
        payload["article"]["image"] = {
            "src": cover_img["src"],
            "alt": title[:255],
        }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="PUT",
        headers={
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== update-images.py: fetch images + update Shopify articles ===\n")

    print("[1/4] Fetching existing Shopify article handles...")
    existing = shopify_get_articles()
    print(f"  Found {len(existing)} articles on Shopify.\n")

    print("[2/4] Fetching product image map...")
    pmap = fetch_product_image_map()
    print()

    meta_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.meta.json")))
    print(f"[3/4] Resolving images for {len(meta_files)} articles...\n")

    for mf in meta_files:
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title = meta.get("title", slug)
        html_file = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
        if not os.path.exists(html_file):
            print(f"  SKIP {slug} (no -final.html)")
            continue
        if slug not in existing:
            print(f"  SKIP {slug} (not published on Shopify)")
            continue

        changed_meta = False
        fb = (meta.get("primary_keyword") or title or "").split()[:6]
        fallback = " ".join(fb) + " woman over 40 wellness"

        # Cover image
        if not meta.get("resolved_cover"):
            q = (meta.get("image_query")
                 or query_from_dalle_prompt(meta.get("image_prompt"))
                 or fallback)
            img = find_image(q, fallback)
            if img:
                meta["resolved_cover"] = img
                changed_meta = True
                print(f"  COVER {slug} <- {img['provider']}: {img['credit_name']} [{q[:50]}]")
            else:
                print(f"  COVER {slug} <- NOT FOUND (query: {q[:50]})")
        else:
            print(f"  COVER {slug} <- already resolved")

        # Body images
        if not meta.get("resolved_body"):
            queries = meta.get("body_image_queries") or []
            # Fall back to extracting queries from DALL-E body prompts
            if not queries:
                dalle_prompts = meta.get("body_image_prompts") or []
                queries = [query_from_dalle_prompt(p) for p in dalle_prompts if p]
                queries = [q for q in queries if q]
            resolved = []
            for q in queries:
                img = find_image(q, fallback)
                if img:
                    resolved.append(img)
            if resolved:
                meta["resolved_body"] = resolved
                changed_meta = True
                print(f"  BODY  {slug} <- {len(resolved)} images")
        else:
            print(f"  BODY  {slug} <- already resolved ({len(meta['resolved_body'])} images)")

        if changed_meta:
            json.dump(meta, open(mf, "w"), indent=2, ensure_ascii=False)

    print(f"\n[4/4] Updating Shopify articles with images...\n")

    results = []
    for mf in meta_files:
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title = meta.get("title", slug)
        html_file = os.path.join(ARTICLES_DIR, f"{slug}-final.html")

        if not os.path.exists(html_file):
            continue
        if slug not in existing:
            continue

        article_id = existing[slug]
        body = open(html_file).read()

        # Fix product card placeholder images
        body = fix_product_card(body, pmap)

        # Inject body stock images
        body_imgs = meta.get("resolved_body") or []
        body = inject_body_images(body, body_imgs, title)

        # Write back fixed HTML
        open(html_file, "w").write(body)

        cover = meta.get("resolved_cover")
        print(f"  Updating {slug} (id={article_id})...", end=" ", flush=True)
        try:
            shopify_update_article(article_id, body, cover, title)
            print("OK")
            results.append({"slug": slug, "status": "ok"})
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:200]
            print(f"FAILED HTTP {e.code}: {err}")
            results.append({"slug": slug, "status": f"http_{e.code}", "error": err})
        except Exception as e:
            print(f"FAILED: {e}")
            results.append({"slug": slug, "status": "error", "error": str(e)})
        time.sleep(1.5)

    ok = sum(1 for r in results if r["status"] == "ok")
    failed = len(results) - ok
    print(f"\nDone: {ok} updated, {failed} failed.")
    if failed:
        print("Failed slugs:")
        for r in results:
            if r["status"] != "ok":
                print(f"  {r['slug']}: {r.get('error', r['status'])}")


if __name__ == "__main__":
    main()

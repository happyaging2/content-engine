#!/usr/bin/env python3
"""
Update already-published Shopify articles with topic-relevant images.
Fetches cover + body images from Pexels (primary) / Unsplash (fallback),
removes photo credit figcaptions, fixes product card images, PUTs to Shopify.

Usage:
    SHOPIFY_TOKEN=shpat_... PEXELS_API_KEY=... python3 update-images.py
    SHOPIFY_TOKEN=shpat_... UNSPLASH_ACCESS_KEY=... python3 update-images.py
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

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "").strip()

if not SHOPIFY_TOKEN:
    raise SystemExit("ERROR: Set SHOPIFY_TOKEN environment variable.")
if not UNSPLASH_KEY and not PEXELS_KEY:
    raise SystemExit("ERROR: Set UNSPLASH_ACCESS_KEY and/or PEXELS_API_KEY.")


# ── Topic → visual query mapping ──────────────────────────────────────────────
# Maps slug keywords to specific, relevant Unsplash/Pexels search queries.

TOPIC_QUERIES = {
    "nad":              ["woman energy vitality morning healthy", "woman taking supplement kitchen"],
    "nmn":              ["woman energy vitality healthy aging", "woman supplement morning routine"],
    "urolithin":        ["woman eating berries pomegranate healthy", "woman active outdoor healthy aging"],
    "ergothioneine":    ["woman mushrooms cooking healthy kitchen", "woman antioxidant food wellness"],
    "rapamycin":        ["woman longevity healthy aging active", "woman outdoor walk nature healthy"],
    "bacopa":           ["woman reading focus concentration desk", "woman memory brain health"],
    "acetylcholine":    ["woman brain focus mental clarity", "woman reading studying concentration"],
    "choline":          ["woman eggs healthy breakfast nutrition", "woman brain health nutrition"],
    "gut-barrier":      ["woman eating healthy fiber vegetables", "woman gut health nutrition food"],
    "gut-dysbiosis":    ["woman digestive health probiotics", "woman stomach gut wellness"],
    "gut-skin":         ["woman glowing skin healthy gut", "woman skin microbiome beauty"],
    "adenosine":        ["woman sleep drive rest evening", "woman tired sleepy evening routine"],
    "glycine":          ["woman sleeping peaceful bedroom night", "woman skin collagen healthy sleep"],
    "exercise-recovery":["woman post workout stretch recovery", "woman muscle recovery fitness rest"],
    "taurine":          ["woman heart health supplement vitality", "woman healthy aging longevity active"],
    "pcos":             ["woman hormones wellness health balance", "woman healthy lifestyle hormonal health"],
    "perimenopause":    ["woman midlife wellness balance health", "woman menopause natural remedies calm"],
    "mood":             ["woman calm happy wellness nature", "woman mood anxiety natural calm"],
    "omega-3":          ["woman fish oil supplement heart health", "woman omega fatty acids nutrition"],
    "sibo":             ["woman digestive gut health wellness", "woman stomach bloating gut healing"],
    "b12":              ["woman nutrition supplement energy health", "woman vitamin deficiency wellness"],
    "liver-healing":    ["woman liver health detox nutrition", "woman healthy eating liver wellness"],
    "strength-training":["woman lifting weights gym fitness", "woman strength training dumbbell workout"],
    "stress-weight":    ["woman stress relief cortisol wellness", "woman healthy weight stress management"],
    "sleep":            ["woman sleeping peaceful bed night", "woman good sleep bedroom rest"],
    "skin":             ["woman glowing skin beauty natural", "woman skincare radiant face"],
    "collagen":         ["woman collagen skin beauty supplement", "woman glowing skin anti-aging"],
    "brain":            ["woman brain health focus mental clarity", "woman cognitive health reading"],
    "memory":           ["woman memory focus brain health", "woman reading concentration mental"],
    "energy":           ["woman energetic morning vitality health", "woman active energy wellness"],
    "fatigue":          ["woman tired fatigue wellness recovery", "woman energy boost morning healthy"],
    "hormone":          ["woman hormonal balance wellness health", "woman menopause natural hormones"],
    "metabolism":       ["woman healthy metabolism fitness nutrition", "woman exercise metabolic health"],
    "inflammation":     ["woman anti-inflammatory food turmeric", "woman healthy eating reduce inflammation"],
    "immune":           ["woman immune health wellness nutrition", "woman healthy lifestyle immunity"],
    "bone":             ["woman bone health exercise strength", "woman osteoporosis prevention fitness"],
    "heart":            ["woman heart health cardio exercise", "woman cardiovascular wellness fitness"],
    "weight":           ["woman healthy weight management fitness", "woman nutrition weight wellness"],
    "cortisol":         ["woman stress cortisol calm meditation", "woman relaxation stress relief nature"],
    "coq10":            ["woman energy cellular health supplement", "woman vitality heart wellness"],
    "magnesium":        ["woman magnesium sleep calm wellness", "woman supplement mineral healthy"],
    "vitamin-d":        ["woman sunshine vitamin d outdoor", "woman sunlight nature wellness"],
    "probiotics":       ["woman probiotics gut health supplement", "woman yogurt fermented food wellness"],
}


def topic_query_for_slug(slug, title=""):
    """Return a list of 2 queries for a given article slug."""
    slug_lower = slug.lower()
    for key, queries in TOPIC_QUERIES.items():
        if key in slug_lower:
            return queries
    # Generic fallback: extract nouns from title
    skip = {"after", "40", "women", "over", "what", "is", "does", "actually",
            "work", "for", "the", "a", "an", "and", "why", "how", "to", "your",
            "you", "are", "with", "that", "can", "will", "its", "at", "in",
            "on", "of", "by", "from", "or", "be", "do", "vs", "into", "our"}
    words = [w.strip(".,?:!-") for w in title.split()
             if w.lower().strip(".,?:!-") not in skip and len(w) > 3][:4]
    base = "woman " + " ".join(words).lower() + " wellness health"
    return [base, "woman healthy aging wellness supplement"]


# ── Rate limit tracking ───────────────────────────────────────────────────────

_unsplash_req = 0
_unsplash_win = None
UNSPLASH_LIMIT = 45
UNSPLASH_WINDOW = 3600


def _unsplash_rate_check():
    global _unsplash_req, _unsplash_win
    now = time.time()
    if _unsplash_win is None:
        _unsplash_win = now
    elapsed = now - _unsplash_win
    if elapsed >= UNSPLASH_WINDOW:
        _unsplash_req = 0
        _unsplash_win = now
    if _unsplash_req >= UNSPLASH_LIMIT:
        wait = UNSPLASH_WINDOW - elapsed + 5
        print(f"  [unsplash] rate limit reached, waiting {int(wait)}s...")
        time.sleep(wait)
        _unsplash_req = 0
        _unsplash_win = time.time()


# ── Image search ──────────────────────────────────────────────────────────────

def pexels_search(query):
    if not PEXELS_KEY:
        return None
    for attempt in range(3):
        try:
            url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 10, "size": "large"})
            req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            photos = data.get("photos") or []
            if not photos:
                return None
            p = photos[0]
            return {"src": p["src"]["large2x"], "alt": (p.get("alt") or query)[:120]}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 60 * (attempt + 1)
                print(f"  [pexels] 429 rate limit, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    pexels fail '{query[:40]}': HTTP {e.code}")
                return None
        except Exception as e:
            print(f"    pexels fail '{query[:40]}': {str(e)[:60]}")
            return None
    return None


def unsplash_search(query):
    global _unsplash_req
    if not UNSPLASH_KEY:
        return None
    _unsplash_rate_check()
    for attempt in range(3):
        try:
            url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 5, "content_filter": "high"})
            req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            _unsplash_req += 1
            results = data.get("results") or []
            if not results:
                return None
            p = results[0]
            try:
                dl = urllib.request.Request(p["links"]["download_location"],
                    headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
                urllib.request.urlopen(dl, timeout=10)
                _unsplash_req += 1
            except Exception:
                pass
            return {"src": p["urls"]["regular"], "alt": (p.get("alt_description") or query)[:120]}
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                wait = 65 * (attempt + 1)
                print(f"  [unsplash] {e.code} on attempt {attempt+1}, waiting {wait}s...")
                time.sleep(wait)
                _unsplash_req = 0
                _unsplash_win = time.time()
            else:
                print(f"    unsplash fail '{query[:40]}': HTTP {e.code}")
                return None
        except Exception as e:
            print(f"    unsplash fail '{query[:40]}': {str(e)[:60]}")
            return None
    return None


def find_image(query):
    # Pexels first (more generous rate limits), Unsplash as fallback
    img = pexels_search(query) or unsplash_search(query)
    time.sleep(1.5)
    return img


# ── HTML helpers ──────────────────────────────────────────────────────────────

def strip_figcaptions(html):
    """Remove all <figcaption>...</figcaption> blocks."""
    return re.sub(r"<figcaption[^>]*>.*?</figcaption>", "", html, flags=re.DOTALL)


def strip_article_stock_images(html):
    """Remove previously injected article-stock-image figures so we can re-inject cleanly."""
    return re.sub(
        r'\s*<figure class="article-stock-image"[^>]*>.*?</figure>\s*',
        "\n", html, flags=re.DOTALL)


def inject_body_images(html, imgs, title):
    """Insert stock images between H2 sections. No photo credits."""
    if not imgs:
        return html
    # Strip any previously injected figures first
    html = strip_article_stock_images(html)
    h2s = [m.end() for m in re.finditer(r"</h2>", html)]
    if len(h2s) < 2:
        return html
    step = max(1, len(h2s) // (len(imgs) + 1))
    insert_points = h2s[step::step][:len(imgs)]
    for img, pos in zip(reversed(imgs), reversed(insert_points)):
        alt = (img.get("alt") or title)[:140].replace('"', "'")
        figure = (
            f'\n<figure class="article-stock-image" style="margin:24px 0">'
            f'<img src="{img["src"]}" alt="{alt}" '
            f'style="width:100%;border-radius:12px;display:block">'
            f'</figure>\n'
        )
        html = html[:pos] + figure + html[pos:]
    return html


# ── Product card image fix ────────────────────────────────────────────────────

def fetch_product_image_map():
    pmap = {}
    try:
        req = urllib.request.urlopen("https://happyaging.com/products.json?limit=250", timeout=15)
        products = json.loads(req.read())["products"]
        for p in products:
            if p.get("images"):
                pmap[p["handle"]] = p["images"][0]["src"]
        print(f"  Fetched {len(pmap)} product images.")
    except Exception as e:
        print(f"  WARNING: Could not fetch product images: {e}")
    return pmap


def fix_product_card(html, pmap):
    for m in re.finditer(
        r'(product-card-inline.*?happyaging\.com/products/([a-z0-9-]+).*?<img[^>]+src=")([^"]+)(")',
        html, re.DOTALL
    ):
        handle, src = m.group(2), m.group(3)
        if "cdn.shopify.com" in src:
            continue
        real = pmap.get(handle)
        if real:
            html = html.replace(src, real)
    return html


# ── Shopify helpers ───────────────────────────────────────────────────────────

def shopify_get_articles():
    articles = {}
    page_info = None
    base = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    while True:
        params = {"limit": 250, "fields": "id,handle"}
        if page_info:
            params["page_info"] = page_info
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        for a in data.get("articles", []):
            articles[a["handle"]] = a["id"]
        link_header = resp.headers.get("Link", "")
        next_page = None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                next_page = part.strip().split(";")[0].strip("<> ")
        if not next_page:
            break
        pi = re.search(r"page_info=([^&]+)", next_page)
        if not pi:
            break
        page_info = pi.group(1)
    return articles


def shopify_update_article(article_id, body_html, cover_src, title):
    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles/{article_id}.json"
    payload = {"article": {"id": article_id, "body_html": body_html}}
    if cover_src:
        payload["article"]["image"] = {"src": cover_src, "alt": title[:255]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="PUT",
        headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== update-images.py ===\n")

    print("[1/4] Fetching Shopify article handles...")
    existing = shopify_get_articles()
    print(f"  {len(existing)} articles on Shopify.\n")

    print("[2/4] Fetching product image map...")
    pmap = fetch_product_image_map()
    print()

    meta_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.meta.json")))
    published_metas = [
        mf for mf in meta_files
        if (lambda s: s in existing and os.path.exists(
            os.path.join(ARTICLES_DIR, f"{s}-final.html")))(
            json.load(open(mf)).get("slug") or
            os.path.basename(mf).replace(".meta.json", ""))
    ]
    print(f"[3/4] Resolving images for {len(published_metas)} published articles...\n")

    for mf in published_metas:
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title = meta.get("title", slug)
        queries = topic_query_for_slug(slug, title)
        changed = False

        if not meta.get("resolved_cover"):
            img = find_image(queries[0]) or find_image(queries[1])
            if img:
                meta["resolved_cover"] = img
                changed = True
                print(f"  COVER {slug[:55]}")
            else:
                print(f"  COVER {slug[:55]} NOT FOUND")
        else:
            print(f"  COVER {slug[:55]} (cached)")

        if not meta.get("resolved_body"):
            resolved = []
            # Use all available queries: topic queries + extras from body_image_queries if present
            bqs = meta.get("body_image_queries") or []
            all_queries = (queries + bqs)[:4]
            for q in all_queries:
                img = find_image(q)
                if img:
                    resolved.append(img)
            if resolved:
                meta["resolved_body"] = resolved
                changed = True
                print(f"  BODY  {slug[:55]} ({len(resolved)} images)")
        else:
            print(f"  BODY  {slug[:55]} ({len(meta['resolved_body'])} images, cached)")

        if changed:
            json.dump(meta, open(mf, "w"), indent=2, ensure_ascii=False)

    print(f"\n[4/4] Updating Shopify articles...\n")

    ok = failed = 0
    for mf in published_metas:
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title = meta.get("title", slug)
        html_file = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
        article_id = existing[slug]

        body = open(html_file).read()
        body = strip_figcaptions(body)            # remove "Photo by X on Unsplash"
        body = fix_product_card(body, pmap)       # fix product card images
        body_imgs = meta.get("resolved_body") or []
        body = inject_body_images(body, body_imgs, title)
        open(html_file, "w").write(body)

        cover_src = (meta.get("resolved_cover") or {}).get("src")
        print(f"  {slug[:60]}...", end=" ", flush=True)
        try:
            shopify_update_article(article_id, body, cover_src, title)
            print("OK")
            ok += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:150]
            print(f"FAIL {e.code}: {err}")
            failed += 1
        except Exception as e:
            print(f"FAIL: {str(e)[:80]}")
            failed += 1
        time.sleep(1.5)

    print(f"\nDone: {ok} updated, {failed} failed.")


if __name__ == "__main__":
    main()

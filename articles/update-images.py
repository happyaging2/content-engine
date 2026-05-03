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

BLOCKED_TERMS = {
    # Explicit content
    "nude", "naked", "topless", "nudity", "lingerie", "bikini",
    "underwear", "explicit", "adult content", "erotic", "sensual",
    "sexy", "sexual", "pornographic", "nsfw",
    # Exposed body parts / medical imagery
    "belly", "abdomen", "navel", "belly button", "torso", "bare skin",
    "bare stomach", "bare belly", "cesarean", "c-section", "surgical scar",
    "scar", "wound", "surgery", "stretch mark", "skin close", "close-up skin",
    "stomach close", "skin texture",
    # Any product / bottle / packaging — blocks BOTH competitor and generic
    "supplement", "vitamin", "capsule", "pill", "tablet", "dose",
    "bottle", "vial", "jar", "tube", "container", "packaging",
    "product", "serum bottle", "cosmetic bottle", "beauty bottle",
    "holding bottle", "holding vial", "holding product", "holding supplement",
    "holding jar", "holding tube", "with bottle", "with supplement",
    "pill box", "medicine", "pharmacy",
    # Off-brand / low-quality / off-aesthetic
    "tattoo", "tattooed", "tattoos",
    "book cover", "dopamine detox",
    "fast food", "junk food", "cigarette",
    "hospital", "clinic", "medical office",
}

# Competitor / third-party brand names — reject any image whose alt contains these
COMPETITOR_BRANDS = {
    "vigorvault", "vigor vault", "nmn revive", "nmn activ", "lifeextension",
    "life extension", "thorne", "jarrow", "now foods", "garden of life",
    "nature's bounty", "gnc", "optimum nutrition", "ritual", "hims", "hers",
    "elysium", "tru niagen", "tru longevity", "alive by science",
    "wonderfeel", "donotage", "do not age", "renue", "maac10",
    "osh wellness", "osh ",
    "missha",
    "neocell", "youtheory", "vital proteins", "sports research",
    "bronson", "swanson", "solgar", "natrol", "nature made",
    "garden of", "nutricost", "bulk supplements",
}


def is_safe(alt_text):
    text = (alt_text or "").lower()
    if any(t in text for t in BLOCKED_TERMS):
        return False
    if any(b in text for b in COMPETITOR_BRANDS):
        return False
    return True


TOPIC_QUERIES = {
    # Lifestyle / activity / food ONLY — no product, no bottle, no supplement
    "nad":              ["woman glowing skin morning light portrait", "woman energetic yoga sunrise outdoor"],
    "nmn":              ["woman running trail outdoor morning", "woman active healthy aging smiling park"],
    "urolithin":        ["woman eating pomegranate fruit healthy", "woman hiking trail outdoor nature"],
    "ergothioneine":    ["woman cooking mushrooms healthy kitchen", "woman farmers market fresh food"],
    "rapamycin":        ["woman walking park autumn healthy aging", "woman outdoor garden nature longevity"],
    "bacopa":           ["woman reading book morning sunlight calm", "woman studying focus desk natural light"],
    "acetylcholine":    ["woman writing journal morning light focused", "woman reading book calm morning"],
    "choline":          ["woman eating eggs breakfast sunny kitchen", "woman healthy breakfast avocado toast"],
    "gut-barrier":      ["woman colorful salad vegetables healthy eating", "woman cooking fresh vegetables kitchen"],
    "gut-dysbiosis":    ["woman eating yogurt bowl healthy kitchen", "woman farmers market fresh produce"],
    "gut-skin":         ["woman radiant face portrait natural light", "woman smiling clear skin outdoor sunlight"],
    "adenosine":        ["woman sleeping peacefully bedroom evening", "woman relaxing evening calm bedroom"],
    "glycine":          ["woman sleeping peaceful white bedroom", "woman restful sleep morning light"],
    "exercise-recovery":["woman stretching yoga mat morning", "woman post run stretch outdoor park"],
    "taurine":          ["woman running cardio outdoor park", "woman swimming active healthy lifestyle"],
    "pcos":             ["woman meditation yoga nature calm", "woman healthy eating greens lifestyle"],
    "perimenopause":    ["woman midlife portrait smiling confident", "woman yoga meditation calm nature"],
    "mood":             ["woman smiling nature park happy calm", "woman meditation outdoor peaceful morning"],
    "omega-3":          ["woman eating salmon grilled healthy meal", "woman seafood healthy eating lunch"],
    "sibo":             ["woman herbal tea calm kitchen morning", "woman light healthy meal soup bowl"],
    "b12":              ["woman eating leafy greens healthy lunch", "woman energy morning walk outdoor"],
    "liver-healing":    ["woman drinking green juice morning healthy", "woman eating salad greens fresh"],
    "strength-training":["woman lifting dumbbell gym focused", "woman strength training workout fitness"],
    "stress-weight":    ["woman meditation outdoor nature calm", "woman yoga morning park peaceful"],
    "sleep":            ["woman sleeping peaceful white linen bedroom", "woman waking refreshed morning light"],
    "skin":             ["woman radiant face portrait soft light", "woman smiling outdoor natural glow"],
    "collagen":         ["woman glowing complexion portrait outdoor", "woman healthy face smiling sunlight"],
    "brain":            ["woman reading focus desk morning", "woman chess strategy thinking focused"],
    "memory":           ["woman reading book focused natural light", "woman journaling desk morning calm"],
    "energy":           ["woman outdoor morning run energetic", "woman sunrise hike active healthy"],
    "fatigue":          ["woman stretching morning wake up bedroom", "woman outdoor walk refresh nature"],
    "hormone":          ["woman yoga calm outdoor nature morning", "woman midlife active healthy smiling"],
    "metabolism":       ["woman cycling outdoor active healthy", "woman healthy meal prep kitchen"],
    "inflammation":     ["woman eating turmeric food anti-inflammatory", "woman colorful vegetables healthy meal"],
    "immune":           ["woman outdoor nature fresh air smiling", "woman healthy food citrus vegetables"],
    "bone":             ["woman yoga warrior pose outdoor", "woman hiking trail strength active"],
    "heart":            ["woman walking outdoor park cardio healthy", "woman cycling nature cardiovascular"],
    "weight":           ["woman outdoor walk nature healthy lifestyle", "woman cooking healthy meal kitchen"],
    "cortisol":         ["woman meditation nature calm outdoor", "woman deep breathing yoga peaceful"],
    "coq10":            ["woman energetic morning outdoor walk", "woman cycling fitness healthy aging"],
    "magnesium":        ["woman relaxing bath evening calm", "woman sleeping peaceful bedroom night"],
    "vitamin-d":        ["woman outdoor sunshine park morning", "woman sunlight garden smiling nature"],
    "probiotics":       ["woman eating yogurt bowl smiling kitchen", "woman fermented food kimchi healthy"],
    "joint":            ["woman yoga flexibility outdoor morning", "woman gentle walk park healthy aging"],
    "arthritis":        ["woman gentle yoga seated stretching", "woman walking outdoor comfortable active"],
    "ashwagandha":      ["woman meditation calm nature herbs garden", "woman yoga outdoor peaceful morning"],
    "hydrogen":         ["woman drinking water glass morning healthy", "woman hydration healthy lifestyle calm"],
    "ceramide":         ["woman applying moisturizer face morning routine", "woman healthy skin portrait soft light"],
    "collagen-type":    ["woman portrait glowing skin natural", "woman outdoor smiling healthy complexion"],
    "molecular":        ["woman drinking clear water healthy hydration", "woman outdoor morning fresh air"],
    "stress-hormone":   ["woman meditation outdoor morning calm", "woman yoga breathing nature peaceful"],
}


def topic_query_for_slug(slug, title=""):
    """Return a list of 2 queries for a given article slug."""
    slug_lower = slug.lower()
    for key, queries in TOPIC_QUERIES.items():
        if key in slug_lower:
            return queries
    # Generic fallback: lifestyle + title noun, never product-related
    skip = {"after", "40", "women", "over", "what", "is", "does", "actually",
            "work", "for", "the", "a", "an", "and", "why", "how", "to", "your",
            "you", "are", "with", "that", "can", "will", "its", "at", "in",
            "on", "of", "by", "from", "or", "be", "do", "vs", "into", "our",
            "supplement", "vitamin", "pill", "capsule", "product"}
    words = [w.strip(".,?:!-") for w in title.split()
             if w.lower().strip(".,?:!-") not in skip and len(w) > 3][:4]
    base = "woman " + " ".join(words).lower() + " wellness lifestyle"
    return [base, "woman healthy aging outdoor portrait smiling"]


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
            safe = [p for p in photos if is_safe(p.get("alt", ""))]
            if not safe:
                return None
            p = safe[0]
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
            safe = [p for p in results if is_safe(p.get("alt_description", ""))]
            if not safe:
                return None
            p = safe[0]
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
        # Prefer the hand-curated image_query from meta.json (set by content writer)
        # over the TOPIC_QUERIES dict; fall back to topic_query_for_slug for the
        # second query used as a safety net.
        cover_q1 = meta.get("image_query") or queries[0]
        cover_q2 = queries[1] if len(queries) > 1 else queries[0]
        changed = False

        if not meta.get("resolved_cover"):
            img = find_image(cover_q1) or find_image(cover_q2)
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
            # Use all available queries: hand-curated body_image_queries first,
            # then topic_query_for_slug as extras.
            bqs = meta.get("body_image_queries") or []
            all_queries = (bqs + queries)[:4]
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

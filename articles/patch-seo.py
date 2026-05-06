#!/usr/bin/env python3
"""
patch-seo.py — Fix SEO issues on all published Shopify articles:
  1. Inject FAQ JSON-LD schema (for AI/rich-snippet eligibility)
  2. Set summary_html as meta description (≤155 chars)
  3. Re-inject body images matched to each H2 section (section-relevant)

Usage:
    SHOPIFY_TOKEN=shpat_... PEXELS_API_KEY=... python3 articles/patch-seo.py
    Add --schema-only to skip image re-fetch (faster, schema + meta only)
"""

import json, os, re, sys, time, glob
import urllib.request, urllib.parse, urllib.error

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID       = "109440303424"
ARTICLES_DIR  = os.path.dirname(os.path.abspath(__file__))

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "").strip()
UNSPLASH_KEY  = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
SCHEMA_ONLY   = "--schema-only" in sys.argv

if not SHOPIFY_TOKEN:
    raise SystemExit("ERROR: Set SHOPIFY_TOKEN")
if not SCHEMA_ONLY and not PEXELS_KEY and not UNSPLASH_KEY:
    print("WARNING: No image API keys set. Running in --schema-only mode.")
    SCHEMA_ONLY = True

BLOG_URL = "https://happyaging.com/blogs/news"
SITE_URL = "https://happyaging.com"
LOGO_URL = "https://happyaging.com/cdn/shop/files/happy-aging-logo.png"


# ── BlogPosting + Speakable schema ────────────────────────────────────────────

def build_article_schema(title, slug, meta_desc):
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "description": meta_desc,
        "url": f"{BLOG_URL}/{slug}",
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BLOG_URL}/{slug}"},
        "author": {
            "@type": "Organization",
            "name": "Happy Aging Team",
            "url": SITE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name": "Happy Aging",
            "url": SITE_URL,
            "logo": {"@type": "ImageObject", "url": LOGO_URL},
        },
        "speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": ["article p:first-of-type", ".faq h3"],
        },
    }


def inject_article_schema(html, title, slug, meta_desc):
    """Inject BlogPosting + Speakable schema once, before </body> or at end."""
    # Remove old article schema if re-running
    html = re.sub(
        r'\s*<script type="application/ld\+json">\s*\{[^}]*"BlogPosting".*?</script>\s*',
        '\n', html, flags=re.DOTALL)
    schema = build_article_schema(title, slug, meta_desc)
    block = ('\n<script type="application/ld+json">\n'
             + json.dumps(schema, ensure_ascii=False, indent=2)
             + '\n</script>\n')
    if '</body>' in html:
        return html.replace('</body>', block + '</body>', 1)
    return html + block


# ── FAQ Schema ────────────────────────────────────────────────────────────────

def extract_faq_pairs(html):
    """Extract Q&A pairs from the Frequently Asked Questions section."""
    faq_match = re.search(
        r'<h2[^>]*>Frequently Asked Questions</h2>(.*?)(?:<h2[^>]*>References|$)',
        html, re.DOTALL | re.IGNORECASE)
    if not faq_match:
        return []
    faq_section = faq_match.group(1)
    pairs = []
    for m in re.finditer(r'<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>', faq_section, re.DOTALL):
        question = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        answer   = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        answer   = re.sub(r'\s+', ' ', answer)
        if question and answer and len(question) > 10:
            pairs.append((question, answer))
    return pairs


def build_faq_schema(pairs):
    entities = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}
        }
        for q, a in pairs
    ]
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    return (
        '\n<script type="application/ld+json">\n'
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + '\n</script>\n'
    )


def inject_faq_schema(html, pairs):
    if not pairs:
        return html
    # Remove existing FAQ schema if re-running
    html = re.sub(
        r'\s*<script type="application/ld\+json">\s*\{[^}]*"FAQPage".*?</script>\s*',
        '\n', html, flags=re.DOTALL)
    schema_block = build_faq_schema(pairs)
    # Insert before the FAQ h2
    html = re.sub(
        r'(<h2[^>]*>Frequently Asked Questions</h2>)',
        schema_block + r'\1',
        html, flags=re.IGNORECASE)
    return html


# ── Meta description ──────────────────────────────────────────────────────────

def extract_meta_description(html, max_chars=155):
    """Extract first paragraph text, strip tags, truncate to max_chars."""
    m = re.search(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    if not m:
        return ""
    text = re.sub(r'<[^>]+>', '', m.group(1))
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(' ', 1)[0]
    return truncated.rstrip('.,;:') + '...'


# ── Brand safety filters ──────────────────────────────────────────────────────

# Only block images whose description clearly shows the VISUAL SUBJECT is
# inappropriate. Use multi-word phrases, not single words — single words like
# "vitamin", "jar", "product" appear in innocent lifestyle photo descriptions
# (e.g. "woman cooking with a jar of spices") and would block everything.
BLOCKED_TERMS = {
    # Explicit / nudity
    "nude", "naked", "topless", "nudity", "lingerie", "bikini", "underwear",
    "explicit", "adult content", "erotic", "sensual", "sexy", "sexual",
    "pornographic", "nsfw",
    # Medical / clinical imagery
    "surgical scar", "c-section", "cesarean", "stretch mark",
    "injection", "syringe", "iv drip", "blood draw",
    "operating room", "hospital bed", "medical office", "clinic room",
    "bare belly", "bare stomach", "bare skin",
    # Actual product shots (multi-word so we don't block innocent uses)
    "supplement bottle", "vitamin bottle", "pill bottle", "medicine bottle",
    "cosmetic bottle", "serum bottle", "beauty bottle",
    "holding bottle", "holding supplement", "holding pill", "holding vial",
    "pill box", "blister pack",
    # Off-brand aesthetics
    "tattoo", "tattooed",
    "book cover",
    "fast food", "junk food", "cigarette", "smoking",
    # Explicit wrong persona
    " man,", " man.", "men's", "elderly man", "old man", "grandfather",
    " boy ", " boys ", "child", "children",
    "baby", "infant", "toddler",
}

COMPETITOR_BRANDS = {
    "vigorvault", "vigor vault", "nmn revive", "nmn activ", "lifeextension",
    "life extension", "thorne", "jarrow", "now foods", "garden of life",
    "nature's bounty", "gnc", "optimum nutrition", "ritual",
    "elysium", "tru niagen", "alive by science", "wonderfeel", "donotage",
    "do not age", "renue", "maac10", "osh wellness",
    "missha", "neocell", "youtheory", "vital proteins", "sports research",
    "swanson", "solgar", "natrol", "nature made",
}

# Supplement/medical topic keywords → safe lifestyle visual context
TOPIC_VISUAL_CONTEXT = {
    "ampk": "exercise morning",
    "autophagy": "meditating sunrise",
    "sirtuin": "hiking nature",
    "nad": "reading morning",
    "nattokinase": "jogging park",
    "collagen": "healthy portrait",
    "retinol": "skincare routine",
    "vitamin": "eating vegetables kitchen",
    "omega": "salmon meal",
    "magnesium": "relaxing evening",
    "gut": "healthy meal kitchen",
    "microbiome": "cooking vegetables",
    "probiotic": "yogurt breakfast",
    "butyrate": "farmers market",
    "glucomannan": "healthy meal",
    "protein": "gym workout",
    "muscle": "strength training",
    "sleep": "bedroom morning",
    "menopausal": "hiking confident",
    "menopause": "hiking nature",
    "hormones": "yoga outdoor",
    "cortisol": "meditation garden",
    "dhea": "jogging park",
    "iodine": "cooking seafood",
    "thyroid": "walking outdoor",
    "bone": "hiking outdoor",
    "heart": "jogging outdoor",
    "brain": "reading focused",
    "skin": "glowing portrait",
    "weight": "healthy eating",
    "inflammation": "yoga meditation",
    "antioxidant": "eating berries",
}

# Safe fallback queries used when topic-specific search returns nothing.
SAFE_FALLBACK_QUERIES = [
    "woman healthy lifestyle outdoor",
    "woman wellness morning",
    "woman eating healthy meal",
    "woman walking park",
    "woman yoga outdoor",
    "woman smiling nature",
    "woman active healthy",
]


def _is_safe(text):
    """Return True only if the image text passes all brand safety checks."""
    t = (text or "").lower()
    if any(k in t for k in BLOCKED_TERMS):
        return False
    if any(b in t for b in COMPETITOR_BRANDS):
        return False
    return True


def _safe_photo(photo_text_fields):
    """Check all available text fields of a photo result."""
    combined = " ".join(f or "" for f in photo_text_fields).lower()
    return _is_safe(combined)


_unsplash_req = 0
_unsplash_win = None

def _rate_check_unsplash():
    global _unsplash_req, _unsplash_win
    now = time.time()
    if _unsplash_win is None:
        _unsplash_win = now
    if (now - _unsplash_win) >= 3600:
        _unsplash_req = 0; _unsplash_win = now
    if _unsplash_req >= 45:
        wait = 3605 - (now - _unsplash_win)
        print(f"  [unsplash] rate limit, waiting {int(wait)}s...")
        time.sleep(wait)
        _unsplash_req = 0; _unsplash_win = time.time()


def pexels_search(query):
    if not PEXELS_KEY:
        return None
    for attempt in range(3):
        try:
            url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 30})
            req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            all_photos = data.get("photos") or []
            safe = []
            rejected_reasons = []
            for p in all_photos:
                alt = p.get("alt") or ""
                if _safe_photo([alt, p.get("photographer")]):
                    safe.append(p)
                else:
                    t = (alt + " " + (p.get("photographer") or "")).lower()
                    hit = next((k for k in BLOCKED_TERMS if k in t), None) or \
                          next((b for b in COMPETITOR_BRANDS if b in t), None)
                    rejected_reasons.append(f"'{alt[:50]}' [{hit}]")
            if not safe and rejected_reasons:
                print(f"        [all blocked] " + " | ".join(rejected_reasons[:3]))
            if not safe:
                return None
            p = safe[0]
            return {"src": p["src"]["large2x"], "alt": (p.get("alt") or query)[:120]}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(60 * (attempt + 1))
            else:
                return None
        except Exception:
            return None
    return None


def unsplash_search(query):
    global _unsplash_req
    if not UNSPLASH_KEY:
        return None
    _rate_check_unsplash()
    for attempt in range(3):
        try:
            url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 15,
                 "content_filter": "high"})
            req = urllib.request.Request(url,
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            _unsplash_req += 1
            results = [p for p in (data.get("results") or [])
                       if _safe_photo([
                           p.get("alt_description"),
                           p.get("description"),
                           p["user"]["name"] if p.get("user") else "",
                       ])]
            if not results:
                return None
            p = results[0]
            return {"src": p["urls"]["regular"], "alt": (p.get("alt_description") or query)[:120]}
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(65 * (attempt + 1)); _unsplash_req = 0
            else:
                return None
        except Exception:
            return None
    return None


def find_image(query, fallbacks=None):
    """Search Pexels then Unsplash; try fallback queries if primary returns nothing."""
    img = pexels_search(query) or unsplash_search(query)
    if img:
        return img
    for fb in (fallbacks or []):
        img = pexels_search(fb) or unsplash_search(fb)
        if img:
            return img
    return None


def h2_to_query(h2_text, article_title=""):
    """Convert H2 heading text to a brand-safe Pexels/Unsplash query.

    Always produces a lifestyle/activity query, never a supplement/clinical one.
    Uses TOPIC_VISUAL_CONTEXT to map known supplement topics to safe visuals.
    """
    h2_lower = h2_text.lower()

    # Check topic map first — steers medical topics to lifestyle visuals
    for keyword, context in TOPIC_VISUAL_CONTEXT.items():
        if keyword in h2_lower:
            return f"woman {context}"

    # Generic extraction: remove stop words, keep descriptive nouns/verbs
    skip = {"what", "why", "how", "the", "a", "an", "and", "or", "of", "to",
            "is", "are", "for", "after", "with", "your", "that", "its", "in",
            "on", "at", "by", "does", "do", "can", "will", "about", "from",
            "this", "these", "40", "over", "women", "woman", "you", "when",
            "should", "need", "take", "use", "using", "does", "into", "vs",
            "which", "between", "difference", "signs", "symptoms", "complete",
            "guide", "protocol", "review", "connection", "link", "role"}
    words = [w.strip(".,?:!-()") for w in h2_text.split()
             if w.lower().strip(".,?:!-()") not in skip
             and len(w.strip(".,?:!-()")) > 2][:4]

    if not words:
        # Fall back to title-derived words
        words = [w.strip(".,?:!-()") for w in article_title.split()
                 if w.lower().strip(".,?:!-()") not in skip][:3]

    # Always append a lifestyle anchor to avoid product/clinical results
    query = "woman " + " ".join(words).lower() + " outdoor lifestyle"
    return query


def inject_section_images(html, article_title, body_image_queries=None):
    """Re-inject body images, one per H2 section, each matched to that section's topic.

    Prefers pre-validated body_image_queries from meta.json over H2-derived queries.
    Applies comprehensive brand safety filtering on every result.
    """
    # Remove previously injected article-stock-image figures
    html = re.sub(
        r'\s*<figure class="article-stock-image"[^>]*>.*?</figure>\s*',
        '\n', html, flags=re.DOTALL)
    # Remove unfilled [BODY_IMAGE_N] placeholder <img> tags (old format)
    html = re.sub(r'<img[^>]+src="\[BODY_IMAGE_\d+\]"[^>]*/?>', '', html)

    # Find all H2 positions (skip FAQ and References)
    skip_h2 = {"frequently asked questions", "references", "faq"}
    h2_matches = [(m.end(), re.sub(r'<[^>]+>', '', m.group(1)).strip())
                  for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
                  if re.sub(r'<[^>]+>', '', m.group(1)).strip().lower() not in skip_h2]

    if not h2_matches:
        return html

    # Skip first H2 (too close to top); target up to 3 images
    targets = h2_matches[1:4]

    offset = 0
    for i, (pos, h2_text) in enumerate(targets):
        # Prefer pre-validated query from meta.json; fall back to H2 derivation
        if body_image_queries and i < len(body_image_queries):
            primary_query = body_image_queries[i]
            derived_query = h2_to_query(h2_text, article_title)
            fallbacks = [derived_query] + SAFE_FALLBACK_QUERIES[:2]
        else:
            primary_query = h2_to_query(h2_text, article_title)
            fallbacks = SAFE_FALLBACK_QUERIES[:2]

        print(f"    [{i+1}] '{h2_text[:40]}' → query: '{primary_query[:50]}'")
        img = find_image(primary_query, fallbacks)
        if not img:
            print(f"        no safe image found — skipping section")
            continue

        alt = img.get("alt", article_title)[:140].replace('"', "'")
        figure = (
            f'\n<figure class="article-stock-image" style="margin:24px 0">'
            f'<img src="{img["src"]}" alt="{alt}" '
            f'style="width:100%;border-radius:12px;display:block">'
            f'</figure>\n'
        )
        insert_at = pos + offset
        html = html[:insert_at] + figure + html[insert_at:]
        offset += len(figure)

    return html


# ── Product price helpers ─────────────────────────────────────────────────────

def fetch_product_prices():
    """Fetch real prices from the Shopify storefront for all products.

    Returns {handle: "XX.XX"} using the lowest variant price, which is
    typically the subscription price on stores using Recharge.
    """
    prices = {}
    page = 1
    while True:
        try:
            url = f"https://happyaging.com/products.json?limit=250&page={page}"
            data = json.loads(urllib.request.urlopen(url, timeout=15).read())
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                handle = p["handle"]
                variants = p.get("variants", [])
                if variants:
                    min_price = min(float(v["price"]) for v in variants)
                    # Format: "49" not "49.00" when whole number
                    prices[handle] = (
                        str(int(min_price)) if min_price == int(min_price)
                        else f"{min_price:.2f}"
                    )
            page += 1
            time.sleep(0.3)
        except Exception:
            break
    return prices


def fix_product_card_prices(body, prices):
    """Replace $XX/month in product cards with real fetched prices."""
    def _replace(m):
        card = m.group(0)
        hm = re.search(r'happyaging\.com/products/([a-z0-9-]+)', card)
        if hm:
            price = prices.get(hm.group(1))
            if price:
                card = re.sub(r'\$[\d.]+/month', f'${price}/month', card)
        return card
    return re.sub(
        r'<div class="product-card-inline">.*?</div>\s*</div>',
        _replace, body, flags=re.DOTALL)


# ── Shopify helpers ───────────────────────────────────────────────────────────

def shopify_get_articles():
    """Fetch all articles: returns {handle: {id, title}}."""
    articles = {}
    page_info = None
    base = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    while True:
        params = {"limit": 250, "fields": "id,handle,title"}
        if page_info:
            params["page_info"] = page_info
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url,
            headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        for a in data.get("articles", []):
            articles[a["handle"]] = {"id": a["id"], "title": a.get("title", "")}
        link = resp.headers.get("Link", "")
        next_url = next((p.strip().split(";")[0].strip("<> ")
                         for p in link.split(",") if 'rel="next"' in p), None)
        if not next_url:
            break
        pi = re.search(r"page_info=([^&]+)", next_url)
        if not pi:
            break
        page_info = pi.group(1)
    return articles


def shopify_fetch_article(article_id):
    """Fetch body_html + existing cover image src for a single article."""
    url = (f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}"
           f"/articles/{article_id}.json?fields=id,body_html,image")
    req = urllib.request.Request(url,
        headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN})
    with urllib.request.urlopen(req, timeout=30) as r:
        art = json.loads(r.read()).get("article", {})
    body = art.get("body_html", "")
    existing_cover = (art.get("image") or {}).get("src")
    return body, existing_cover


def shopify_update(article_id, body_html, summary_html, cover_src=None, cover_alt=None):
    url = (f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}"
           f"/articles/{article_id}.json")
    article = {
        "id": article_id,
        "body_html": body_html,
        "summary_html": summary_html,
    }
    if cover_src:
        article["image"] = {"src": cover_src, "alt": (cover_alt or "")[:120]}
    payload = {"article": article}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PUT",
        headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    mode = "schema + meta only" if SCHEMA_ONLY else "schema + meta + section images + cover"
    print(f"=== patch-seo.py [{mode}] ===\n")

    print("[1/4] Fetching Shopify article list...")
    existing = shopify_get_articles()
    print(f"  {len(existing)} articles on Shopify.")

    print("[2/4] Fetching real product prices from store...")
    prices = fetch_product_prices()
    if prices:
        print(f"  {len(prices)} products found: " +
              ", ".join(f"{h}=${p}" for h, p in sorted(prices.items())))
    else:
        print("  WARNING: could not fetch product prices — prices will not be updated.")
    print()

    # Build slug → meta.json lookup from local files
    local_meta = {}
    local_html = {}
    for mf in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.meta.json"))):
        m = json.load(open(mf))
        slug = m.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        local_meta[slug] = m
        html_f = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
        if os.path.exists(html_f):
            local_html[slug] = html_f

    print(f"[3/4] Processing all {len(existing)} Shopify articles...\n")

    ok = failed = schema_added = meta_set = img_updated = cover_updated = 0

    for slug, info in existing.items():
        art_id = info["id"]
        title  = info["title"]
        meta   = local_meta.get(slug, {})

        # Load body: prefer local file, fall back to Shopify fetch
        # Also fetch existing cover so we don't waste Pexels quota on articles
        # that already have a cover image.
        existing_cover = None
        if slug in local_html:
            body = open(local_html[slug]).read()
            source = "local"
            resolved = meta.get("resolved_cover")
            if resolved and resolved.get("src"):
                existing_cover = resolved["src"]
        else:
            try:
                body, existing_cover = shopify_fetch_article(art_id)
                source = "shopify"
                time.sleep(0.5)
            except Exception as e:
                print(f"  SKIP {slug[:55]} — fetch failed: {str(e)[:60]}")
                failed += 1
                continue

        if not body.strip():
            print(f"  SKIP {slug[:55]} — empty body")
            continue

        # 1. Product card prices
        if prices:
            body = fix_product_card_prices(body, prices)

        # 2. Meta description (needed by article schema below)
        meta_desc = extract_meta_description(body)

        # 3. FAQ Schema
        pairs = extract_faq_pairs(body)
        if pairs:
            body = inject_faq_schema(body, pairs)
            schema_added += 1

        # 4. BlogPosting + Speakable schema
        body = inject_article_schema(body, title, slug, meta_desc)

        # 5. Section images + cover
        cover_src = cover_alt = None
        if not SCHEMA_ONLY:
            print(f"  {slug[:55]} [{source}]")
            body_image_queries = meta.get("body_image_queries") or []
            body = inject_section_images(body, title, body_image_queries)
            img_updated += 1

            # Cover image: reuse existing if present (saves Pexels quota).
            # Only call Pexels for articles that have NO cover at all.
            if existing_cover:
                cover_src = existing_cover
                cover_alt = title
            else:
                q = meta.get("image_query") or h2_to_query(title, title)
                img = find_image(q, SAFE_FALLBACK_QUERIES[:3])
                if img:
                    cover_src = img["src"]
                    cover_alt = title
                    cover_updated += 1
        else:
            print(f"  {slug[:55]} (schema+meta) [{source}]")

        meta_set += 1

        # Write back local file if it exists
        if slug in local_html:
            open(local_html[slug], "w").write(body)

        # Update Shopify
        try:
            shopify_update(art_id, body, meta_desc, cover_src, cover_alt)
            ok += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:120]
            print(f"    FAIL {e.code}: {err}")
            failed += 1
        except Exception as e:
            print(f"    FAIL: {str(e)[:80]}")
            failed += 1

        time.sleep(1.2)

    print(f"\n[4/4] Done.")
    print(f"  FAQ schema injected:     {schema_added}")
    print(f"  Meta descriptions set:   {meta_set}")
    print(f"  Section images updated:  {img_updated}")
    print(f"  Cover images updated:    {cover_updated}")
    print(f"  Shopify updates:         {ok} OK, {failed} failed")


if __name__ == "__main__":
    main()

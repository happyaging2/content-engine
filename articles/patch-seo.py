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

# Local lib for MedicalWebPage / Article / HowTo JSON-LD with reviewer Person.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_medical_schema import inject_medical_schema  # noqa: E402

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID       = "109440303424"
ARTICLES_DIR  = os.path.dirname(os.path.abspath(__file__))

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "").strip()
UNSPLASH_KEY  = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
PIXABAY_KEY   = os.environ.get("PIXABAY_API_KEY", "").strip()
SCHEMA_ONLY   = "--schema-only" in sys.argv
FORCE_COVERS  = "--force-covers" in sys.argv   # replace covers even if one already exists

if not SHOPIFY_TOKEN:
    raise SystemExit("ERROR: Set SHOPIFY_TOKEN")
if not SCHEMA_ONLY and not PEXELS_KEY and not UNSPLASH_KEY and not PIXABAY_KEY:
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
    "ampk": "exercise morning energetic",
    "autophagy": "meditating peaceful sunrise",
    "sirtuin": "hiking nature trail",
    "nad": "reading morning coffee",
    "nmn": "morning routine energetic",
    "nmn": "morning routine energetic",
    "nattokinase": "jogging coastal park",
    "collagen": "glowing skin portrait",
    "retinol": "skincare morning ritual",
    "vitamin": "eating colorful vegetables",
    "omega": "salmon healthy meal",
    "magnesium": "relaxing bath evening",
    "gut": "healthy salad bowl",
    "microbiome": "preparing vegetables colorful",
    "probiotic": "yogurt bowl breakfast",
    "butyrate": "farmers market vegetables",
    "glucomannan": "balanced meal satisfied",
    "protein": "gym workout active",
    "muscle": "strength training confident",
    "sleep": "peaceful bedroom sunrise",
    "menopausal": "hiking confident nature",
    "menopause": "hiking nature serene",
    "hormones": "yoga outdoor calm",
    "cortisol": "meditation garden breathing",
    "dhea": "active outdoor lifestyle",
    "iodine": "cooking seafood healthy",
    "thyroid": "walking energetic outdoor",
    "bone": "hiking outdoor strong",
    "heart": "jogging outdoor healthy",
    "brain": "reading focused calm",
    "skin": "glowing portrait natural",
    "weight": "healthy eating balanced",
    "inflammation": "yoga stretching serene",
    "antioxidant": "eating berries colorful",
    "astaxanthin": "glowing skin outdoor portrait",
    "quercetin": "eating colorful fruits",
    "resveratrol": "walking vineyard healthy",
    "coq10": "active lifestyle energetic",
    "berberine": "healthy meal balanced",
    "pterostilbene": "eating blueberries fresh",
    "spermidine": "eating wheat germ healthy",
    "fisetin": "eating strawberries fresh",
    "lion": "focused writing outdoor cafe",
    "ashwagandha": "yoga meditation calm",
    "phosphatidylserine": "reading focused morning",
    "lutein": "eating leafy greens",
    "zeaxanthin": "eating colorful vegetables",
    "zinc": "cooking colorful vegetables",
    "iron": "energetic morning run",
    "calcium": "yoga stretching outdoor",
    "energy": "active woman morning energetic",
    "fatigue": "resting peaceful nature",
    "joint": "yoga gentle stretching",
    "hair": "natural portrait confident smile",
    "nail": "healthy hands natural",
    "mood": "smiling woman nature happy",
    "anxiety": "meditation calm garden breathing",
    "focus": "reading focused cafe morning",
    "memory": "reading books focused calm",
    "libido": "couple walking beach sunset",
    "fertility": "healthy woman nature serene",
    "adrenal": "calm breathing yoga morning",
    "insulin": "healthy meal vegetables",
    "blood sugar": "healthy meal balanced",
    "longevity": "active woman hiking nature",
    "aging": "confident woman outdoor portrait",
    "mitochondria": "morning run energetic",
    "detox": "green smoothie healthy kitchen",
    "liver": "healthy salad greens",
    "kidney": "drinking water healthy",
    "immune": "eating citrus fruit healthy",
    "allergy": "walking outdoor spring",
    "stress": "meditation yoga breathing calm",
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
    headers = {
        "Authorization": PEXELS_KEY,
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for attempt in range(3):
        try:
            url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 30})
            req = urllib.request.Request(url, headers=headers)
            raw = urllib.request.urlopen(req, timeout=15).read()
            data = json.loads(raw)
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
            print(f"    [pexels HTTP {e.code}] {e.read().decode()[:120]}")
            if e.code == 429:
                time.sleep(60 * (attempt + 1))
            else:
                return None
        except Exception as e:
            print(f"    [pexels error] {type(e).__name__}: {str(e)[:100]}")
            return None
    return None


def pexels_search_many(query, max_results=60):
    """Return a list of up to max_results safe photos — used to build the image pool.

    Uses per_page=80 (Pexels max) to get a large, varied pool in a single API call.
    """
    if not PEXELS_KEY:
        return []
    headers = {
        "Authorization": PEXELS_KEY,
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": query, "orientation": "landscape", "per_page": 80})
        req = urllib.request.Request(url, headers=headers)
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return [
            {"src": p["src"]["large2x"], "alt": (p.get("alt") or query)[:120]}
            for p in (data.get("photos") or [])
            if _safe_photo([p.get("alt") or "", p.get("photographer") or ""])
        ][:max_results]
    except Exception:
        return []


def pixabay_search_many(query, max_results=30):
    """Return a list of up to max_results safe photos from Pixabay (free, no attribution)."""
    if not PIXABAY_KEY:
        return []
    try:
        url = "https://pixabay.com/api/?" + urllib.parse.urlencode({
            "key": PIXABAY_KEY,
            "q": query,
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": 50,
            "safesearch": "true",
            "editors_choice": "false",
        })
        data = json.loads(urllib.request.urlopen(url, timeout=15).read())
        return [
            {"src": h.get("largeImageURL", h.get("webformatURL", "")),
             "alt": (h.get("tags", query).split(",")[0].strip() or query)[:120]}
            for h in (data.get("hits") or [])
            if h.get("largeImageURL") or h.get("webformatURL")
            if _safe_photo([h.get("tags", ""), h.get("user", "")])
        ][:max_results]
    except Exception:
        return []


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


def inject_section_images(html, article_title, slug="", body_image_queries=None,
                          image_pool=None, image_cache=None):
    """Re-inject body images, one per H2 section, varied per article via slug hash.

    image_pool: {query: [img, img, ...]} — pool of safe photos per query.
                Each article picks a different photo using hash(slug + section_idx).
    image_cache: legacy {query: single_img} — still checked as fallback.
    Skips articles that already have valid section images.
    """
    # Strip ALL [BODY_IMAGE_N] placeholders first — ALWAYS, even if article already has figures
    html = re.sub(r'\[BODY_IMAGE_\d+\]', '', html)
    html = re.sub(r'<img[^>]+src="\[BODY_IMAGE_\d+\]"[^>]*/?>', '', html)
    html = re.sub(r'<figure[^>]*>\s*<img[^>]+src="\[BODY_IMAGE_\d+\]"[^>]*/?>\s*</figure>', '', html)

    # Skip injecting NEW figures if article already has valid ones
    if re.search(r'<figure class="article-stock-image"[^>]*>.*?<img[^>]+src="https?://', html,
                 re.DOTALL):
        return html

    # Find all H2 positions (skip FAQ and References)
    skip_h2 = {"frequently asked questions", "references", "faq"}
    h2_matches = [(m.end(), re.sub(r'<[^>]+>', '', m.group(1)).strip())
                  for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
                  if re.sub(r'<[^>]+>', '', m.group(1)).strip().lower() not in skip_h2]

    if not h2_matches:
        return html

    # Skip first H2 (too close to top); target up to 3 images
    targets = h2_matches[1:4]
    pool = image_pool or {}
    stop = {"woman", "the", "and", "for", "with", "your"}

    offset = 0
    for i, (pos, h2_text) in enumerate(targets):
        if body_image_queries and i < len(body_image_queries):
            primary_query = body_image_queries[i]
            fallbacks = [h2_to_query(h2_text, article_title)] + SAFE_FALLBACK_QUERIES[:2]
        else:
            primary_query = h2_to_query(h2_text, article_title)
            fallbacks = SAFE_FALLBACK_QUERIES[:2]

        # Pick from pool (varied per article + section via hash)
        photo_pool = pool.get(primary_query)
        if not photo_pool:
            for fb in fallbacks:
                photo_pool = pool.get(fb)
                if photo_pool:
                    break
        if not photo_pool:
            # Topic keyword scan
            title_lower = article_title.lower()
            for cq, cpool in pool.items():
                words = [w for w in cq.split() if w not in stop and len(w) > 3]
                if any(w in title_lower for w in words):
                    photo_pool = cpool; break
        if not photo_pool:
            # Guaranteed fallback: safe fallback queries always pre-fetched
            for fb in SAFE_FALLBACK_QUERIES:
                photo_pool = pool.get(fb)
                if photo_pool: break

        img = None
        if photo_pool:
            # Hash of slug + section index → unique photo per article per section
            idx = abs(hash(slug + str(i))) % len(photo_pool)
            img = photo_pool[idx]
        else:
            # Last resort: legacy cache or live API
            img = (image_cache or {}).get(primary_query)
            if not img:
                img = find_image(primary_query, fallbacks)
        if not img:
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


# ── Product helpers ───────────────────────────────────────────────────────────

_PRODUCT_STOPWORDS = {
    "happy", "aging", "supplement", "formula", "complex", "blend", "advanced",
    "ultra", "daily", "plus", "pro", "extra", "strength", "boost", "pure",
    "natural", "organic", "the", "for", "women", "woman", "men", "support",
    "with", "and", "our", "new",
}


def _extract_product_keywords(title):
    """Return matchable keyword phrases from a product title (longest first)."""
    cleaned = re.sub(r'\b\d+\s*(?:mg|mcg|g|iu|ml|oz|caps?|tablets?|count)\b',
                     '', title, flags=re.I)
    cleaned = re.sub(r'[^\w\s-]', ' ', cleaned)
    words = [w.strip('-') for w in cleaned.split()
             if w.lower().strip('-') not in _PRODUCT_STOPWORDS
             and len(w.strip('-')) > 2]
    if not words:
        return []
    kws = []
    if len(words) >= 2:
        kws.append(" ".join(words[:2]))
    for w in sorted(words, key=len, reverse=True):
        if len(w) >= 4:
            kws.append(w)
    return list(dict.fromkeys(kws))


def fetch_products():
    """Fetch all store products; return (prices_dict, linking_list).

    prices_dict: {handle: "XX"} (lowest variant price)
    linking_list: [{handle, title, keywords}] for contextual article links
    """
    prices = {}
    linking = []
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
                    prices[handle] = (
                        str(int(min_price)) if min_price == int(min_price)
                        else f"{min_price:.2f}"
                    )
                kws = _extract_product_keywords(p.get("title", ""))
                if kws:
                    linking.append({
                        "handle": handle,
                        "title": p.get("title", ""),
                        "keywords": kws,
                        "img_url": (p["images"][0]["src"] if p.get("images") else ""),
                    })
            page += 1
            time.sleep(0.3)
        except Exception:
            break
    return prices, linking


def _inject_link_in_para(para_html, kw, url):
    """Inject one `<a>` for kw into para_html; respects existing link nesting."""
    kw_re = re.compile(r'\b' + re.escape(kw) + r'\b', re.I)
    result = []
    i = 0
    in_link = False
    done = False
    while i < len(para_html):
        if para_html[i] == '<':
            j = para_html.find('>', i)
            if j < 0:
                result.append(para_html[i:]); break
            tag = para_html[i:j + 1]
            if re.match(r'<a\b', tag, re.I):
                in_link = True
            elif re.match(r'</a', tag, re.I):
                in_link = False
            result.append(tag)
            i = j + 1
        else:
            j = para_html.find('<', i)
            if j < 0:
                j = len(para_html)
            text = para_html[i:j]
            if not done and not in_link:
                m = kw_re.search(text)
                if m:
                    s, e = m.start(), m.end()
                    text = (text[:s]
                            + f'<a href="{url}" style="color:#8B7355;font-weight:600">'
                            + text[s:e] + '</a>'
                            + text[e:])
                    done = True
            result.append(text)
            i = j
    return "".join(result), done


def inject_product_links(html, products, max_links=2):
    """Inject up to max_links contextual product links into article paragraphs.

    - Skips first 2 paragraphs (intro/hook)
    - Skips text already inside an existing <a> tag
    - Idempotent: won't double-link the same product URL
    - Targets first natural occurrence of each product keyword
    """
    if not products:
        return html
    injected = 0
    for prod in products:
        if injected >= max_links:
            break
        prod_url = f"https://happyaging.com/products/{prod['handle']}"
        found = False
        for kw in prod["keywords"]:
            if found or injected >= max_links:
                break
            if len(kw) < 3:
                continue
            # Re-parse after each injection so offsets stay valid
            paras = list(re.finditer(r'<p\b[^>]*>.*?</p>', html, re.DOTALL))
            for pm in paras[2:]:
                para = pm.group(0)
                if prod_url in para:   # already linked this product
                    found = True; break
                # Quick text-only check (avoids tag noise)
                text = re.sub(r'<[^>]+>', '', para)
                if not re.search(r'\b' + re.escape(kw) + r'\b', text, re.I):
                    continue
                new_para, did_inject = _inject_link_in_para(para, kw, prod_url)
                if did_inject:
                    html = html[:pm.start()] + new_para + html[pm.end():]
                    injected += 1
                    found = True
                    break
    return html


def inject_product_cta(html, products, prices, article_title):
    """Inject a prominent product CTA block before the FAQ section.

    Picks the most relevant product by keyword overlap with article_title,
    then falls back to body text matching. Idempotent via CSS class marker.
    Inserts before <h2>Frequently Asked Questions</h2> or before last H2.
    """
    if 'class="article-product-cta"' in html or not products:
        return html

    title_lower = article_title.lower()

    # Score by keyword overlap with article title (most specific signal)
    best_prod, best_score = None, 0
    for prod in products:
        score = sum(1 for kw in prod["keywords"]
                    if re.search(r'\b' + re.escape(kw) + r'\b', title_lower, re.I))
        if score > best_score:
            best_score, best_prod = score, prod

    # Fallback: first product keyword match in body text
    if not best_prod or best_score == 0:
        body_text = re.sub(r'<[^>]+>', '', html).lower()
        for prod in products:
            for kw in prod["keywords"]:
                if len(kw) >= 4 and re.search(r'\b' + re.escape(kw) + r'\b', body_text, re.I):
                    best_prod = prod
                    break
            if best_prod:
                break

    if not best_prod:
        return html

    handle    = best_prod["handle"]
    prod_url  = f"https://happyaging.com/products/{handle}"
    price     = prices.get(handle, "")
    img_url   = best_prod.get("img_url", "")

    # Strip dosage numbers for a clean display name
    short_name = re.sub(
        r'\b\d+\s*(?:mg|mcg|g|iu|ml|caps?|tablets?|count)\b', '',
        best_prod["title"], flags=re.I).strip()

    price_line = f" — from ${price}/month" if price else ""

    # Contextual intro: ties article topic directly to product benefit
    # Uses the best matching product keyword so the connection feels editorial, not generic.
    _skip = {"why","how","what","when","is","are","the","a","an","for","and","or",
             "of","to","in","on","at","after","40","over","women","woman","your",
             "you","do","does","can","will","with","its","this","that","these"}
    topic_words = [w.strip("?,.:;!'\"") for w in article_title.split()
                   if w.lower().strip("?,.:;!'\"") not in _skip
                   and len(w.strip("?,.:;!'\"")) > 3]
    topic = " ".join(topic_words[:3]).lower() if topic_words else "healthy aging"

    # Find the product keyword that best matches the article title
    matching_kw = next(
        (kw for kw in best_prod["keywords"]
         if re.search(r'\b' + re.escape(kw) + r'\b', title_lower, re.I)
         and len(kw) >= 4),
        topic
    )
    intro = (f"Many women over 40 reading about {matching_kw} find that adding "
             f"{short_name} to their daily routine makes a real difference.")

    img_block = (
        f'<img src="{img_url}" alt="{short_name}" '
        'style="width:100px;height:100px;object-fit:contain;'
        'border-radius:8px;background:#fff;flex-shrink:0">\n'
        if img_url else ""
    )

    cta = (
        '\n<div class="article-product-cta" '
        'style="background:#FDF8F3;border:2px solid #E8D5B7;border-radius:16px;'
        'padding:24px 28px;margin:48px 0">\n'
        '<p style="font-size:11px;text-transform:uppercase;letter-spacing:0.12em;'
        'color:#8B7355;font-weight:700;margin:0 0 16px">Recommended by Happy Aging</p>\n'
        '<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">\n'
        + img_block +
        '<div style="flex:1;min-width:180px">\n'
        f'<h3 style="font-size:19px;color:#2D2D2D;font-weight:700;margin:0 0 6px">'
        f'{short_name}</h3>\n'
        f'<p style="color:#5A5A5A;font-size:14px;margin:0 0 14px;line-height:1.55">'
        f'{intro}</p>\n'
        f'<a href="{prod_url}" '
        'style="display:inline-block;background:#8B7355;color:#fff;padding:11px 28px;'
        'border-radius:8px;text-decoration:none;font-weight:700;font-size:14px">'
        f'Try {short_name}{price_line} →</a>\n'
        '</div>\n</div>\n</div>\n'
    )

    # Insert before FAQ H2 (preferred position)
    new_html = re.sub(
        r'(<h2[^>]*>\s*(?:Frequently Asked Questions|FAQ)\s*</h2>)',
        cta + r'\1', html, count=1, flags=re.I)
    if new_html != html:
        return new_html

    # Fallback: before the last H2 in the article
    h2_matches = list(re.finditer(r'<h2[^>]*>', html))
    if len(h2_matches) >= 2:
        last_h2_pos = h2_matches[-1].start()
        return html[:last_h2_pos] + cta + html[last_h2_pos:]

    return html + cta


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
    if FORCE_COVERS and not SCHEMA_ONLY:
        mode += " (FORCE-COVERS: replacing all existing covers)"
    print(f"=== patch-seo.py [{mode}] ===\n")

    # Quick connectivity test — 1 Pexels call, print raw result
    if PEXELS_KEY and not SCHEMA_ONLY:
        print("[0/4] Testing Pexels API key...")
        try:
            headers = {
                "Authorization": PEXELS_KEY,
                "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/124.0.0.0 Safari/537.36"),
                "Accept": "application/json",
            }
            url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
                {"query": "woman walking park", "per_page": 3})
            req = urllib.request.Request(url, headers=headers)
            raw = urllib.request.urlopen(req, timeout=15).read()
            data = json.loads(raw)
            photos = data.get("photos") or []
            if photos:
                p = photos[0]
                alt = p.get("alt", "")
                print(f"  OK — {len(photos)} photos. First: '{alt[:80]}'")
                print(f"       src: {p['src']['large2x'][:80]}")
            else:
                print(f"  WARNING — API responded but returned 0 photos.")
                print(f"  Raw response: {raw[:300]}")
        except Exception as e:
            print(f"  ERROR — {type(e).__name__}: {e}")
        print()

    print("[1/4] Fetching Shopify article list...")
    existing = shopify_get_articles()
    print(f"  {len(existing)} articles on Shopify.")

    print("[2/4] Fetching products (prices + linking)...")
    prices, products_for_linking = fetch_products()
    if prices:
        print(f"  {len(prices)} products — prices: " +
              ", ".join(f"{h}=${p}" for h, p in sorted(prices.items())))
    else:
        print("  WARNING: could not fetch product prices — prices will not be updated.")
    if products_for_linking:
        print(f"  {len(products_for_linking)} products available for contextual linking.")
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

    # Pre-fetch image pool: topic queries + per-article cover queries.
    # Pexels: up to 60 photos per query (per_page=80, filtered).
    # Pixabay: up to 30 photos per query (free, no attribution).
    # Each article picks by hash(slug) so covers and body images are varied.
    image_pool  = {}   # {query: [img, img, ...]}
    image_cache = {}   # {query: img}  — first photo per query (legacy fallback)
    if not SCHEMA_ONLY and (PEXELS_KEY or UNSPLASH_KEY or PIXABAY_KEY):
        print("[3/4] Pre-fetching image pool (Pexels 60/query + Pixabay 30/query)...")

        # Collect unique title-derived cover queries for ALL articles so each article
        # has its own pool bucket rather than falling to shared SAFE_FALLBACK_QUERIES.
        title_cover_queries = {}   # {slug: query}
        for slug, info in existing.items():
            t = info["title"]
            meta = local_meta.get(slug, {})
            q = meta.get("image_query") or h2_to_query(t, t)
            title_cover_queries[slug] = q

        unique_queries = list(dict.fromkeys(
            ["woman " + v for v in TOPIC_VISUAL_CONTEXT.values()]
            + SAFE_FALLBACK_QUERIES
            + list(title_cover_queries.values())
        ))

        for q in unique_queries:
            photos: list = []
            # Pexels (primary): up to 60 photos per query
            if PEXELS_KEY:
                photos = pexels_search_many(q, max_results=60)
            # Pixabay (supplement): adds more variety, deduplicated by src
            if PIXABAY_KEY:
                pb_photos = pixabay_search_many(q, max_results=30)
                existing_srcs = {p["src"] for p in photos}
                photos += [p for p in pb_photos if p["src"] not in existing_srcs]
            # Unsplash fallback only if both above empty
            if not photos and UNSPLASH_KEY:
                fb = unsplash_search(q)
                if fb:
                    photos = [fb]
            if photos:
                image_pool[q]  = photos
                image_cache[q] = photos[0]
                print(f"  ✓ {q[:55]}  ({len(photos)} photos)")
            time.sleep(0.5)
        total_photos = sum(len(v) for v in image_pool.values())
        print(f"  Pool: {len(image_pool)} queries, {total_photos} unique photos.\n")
    else:
        print(f"[3/4] Skipping image pool (schema-only mode or no API keys).\n")
        title_cover_queries = {}

    print(f"[4/4] Processing all {len(existing)} Shopify articles...\n")

    ok = failed = schema_added = meta_set = img_updated = cover_updated = links_added = ctas_added = 0

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

        # 2. Contextual product links (1-2 per article, subtle inline links)
        if products_for_linking:
            body_before = body
            body = inject_product_links(body, products_for_linking)
            if body != body_before:
                links_added += 1

        # 2b. Product CTA block (prominent, before FAQ section)
        if products_for_linking:
            body_before = body
            body = inject_product_cta(body, products_for_linking, prices, title)
            if body != body_before:
                ctas_added += 1

        # 3. Meta description (needed by article schema below)
        meta_desc = extract_meta_description(body)

        # 4. FAQ Schema
        pairs = extract_faq_pairs(body)
        if pairs:
            body = inject_faq_schema(body, pairs)
            schema_added += 1

        # 5. BlogPosting + Speakable schema (legacy; kept for backward compat)
        body = inject_article_schema(body, title, slug, meta_desc)

        # 5b. MedicalWebPage / Article + Person reviewer + HowTo (GEO E-E-A-T)
        body = inject_medical_schema(
            body, title=title, slug=slug, meta_desc=meta_desc, meta=meta
        )

        # 6. Section images + cover
        cover_src = cover_alt = None
        if not SCHEMA_ONLY:
            print(f"  {slug[:55]} [{source}]")
            body_image_queries = meta.get("body_image_queries") or []
            body = inject_section_images(
                body, title, slug=slug,
                body_image_queries=body_image_queries,
                image_pool=image_pool, image_cache=image_cache)
            img_updated += 1

            # Cover image: use per-article title-derived query for maximum variety.
            # --force-covers replaces covers even if one already exists (fixes repeated covers).
            cover_src = cover_alt = None
            if not existing_cover or FORCE_COVERS:
                # Per-article query: pre-computed from article title (or meta image_query)
                q = meta.get("image_query") or title_cover_queries.get(slug) or h2_to_query(title, title)
                title_lower = title.lower()
                stop = {"woman", "the", "and", "for", "with", "your"}

                # 1. Article-specific pool hit (best — unique per article topic)
                pool = image_pool.get(q)

                # 2. Topic-keyword scan against pool (broader match)
                if not pool:
                    for cq, cpool in image_pool.items():
                        words = [w for w in cq.split() if w not in stop and len(w) > 3]
                        if any(w in title_lower for w in words):
                            pool = cpool; break

                # 3. Guaranteed fallback: SAFE_FALLBACK_QUERIES are always pre-fetched
                if not pool:
                    for fb in SAFE_FALLBACK_QUERIES:
                        pool = image_pool.get(fb)
                        if pool: break

                if pool:
                    # hash(slug) → unique photo per article, stable across re-runs
                    # Pool now has 60-90 photos so collision rate is very low
                    idx = abs(hash(slug)) % len(pool)
                    img = pool[idx]
                else:
                    # 4. Last resort: live API only if pool is completely empty
                    img = find_image(q, SAFE_FALLBACK_QUERIES[:2])

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

    print(f"\n[Done]")
    print(f"  FAQ schema injected:     {schema_added}")
    print(f"  Meta descriptions set:   {meta_set}")
    print(f"  Product links injected:  {links_added} articles")
    print(f"  Product CTA blocks:      {ctas_added} articles")
    print(f"  Section images updated:  {img_updated}")
    print(f"  Cover images updated:    {cover_updated}")
    print(f"  Shopify updates:         {ok} OK, {failed} failed")


if __name__ == "__main__":
    main()

#!/bin/bash
# =============================================================
# JARVIS QA + Publish Script
# Run LOCALLY every day after 7am BRT (agent finishes at ~6:20am)
# Usage: cd /tmp/content-engine && bash scripts/qa-and-publish.sh
# =============================================================

set -e

BATCH_DATE="${1:-$(date +%Y-%m-%d)}"
SHOPIFY_TOKEN="${SHOPIFY_TOKEN}"
BLOG_ID="109440303424"
API_URL="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/${BLOG_ID}/articles.json"
ARTICLES_DIR="articles"
LOG_FILE="articles/qa-${BATCH_DATE}.log"

# Export BATCH_DATE so every python heredoc below can scope its work to today's
# slugs (read from articles/batch-<date>-report.md). Without scoping, every
# Step iterates the full corpus (500+ files) — wastes API budget and re-injects
# CTAs into already-published articles.
export BATCH_DATE

echo "=== JARVIS QA + Publish: Batch ${BATCH_DATE} ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$LOG_FILE"

# Step 0: Pull latest (rebase to avoid race with concurrent agent-pipeline push)
echo "[0/6] Pulling latest from git..."
git pull --rebase origin main --quiet 2>/dev/null || git pull origin main --quiet || true

# Step 0a: PMID validation — verify citations resolve on PubMed
echo "[0a] Validating PMIDs in batch ${BATCH_DATE} articles..."
python3 << 'PYEOF'
import re, glob, os, urllib.request, urllib.error, time

batch_date = os.environ.get("BATCH_DATE", "")
pattern = f"articles/*-final.html" if not batch_date else f"articles/*-final.html"

# Collect PMIDs from all -final.html files for today's batch slugs
report = f"articles/batch-{batch_date}-report.md" if batch_date else None
slugs = set()
if report and os.path.exists(report):
    for line in open(report):
        m = re.search(r'\|\s*\d+\s*\|.*?\|\s*([a-z0-9-]+)\s*\|', line)
        if m:
            slugs.add(m.group(1).strip())

files = [f"articles/{s}-final.html" for s in slugs if os.path.exists(f"articles/{s}-final.html")]
if not files:
    files = sorted(glob.glob("articles/*-final.html"))

removed_total = 0
for f in files:
    body = open(f).read()
    pmids = set(re.findall(r'PMID[:\s]+(\d{7,8})', body))
    changed = False
    for pmid in pmids:
        try:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            req = urllib.request.Request(url, method="HEAD",
                headers={"User-Agent": "Mozilla/5.0"})
            urllib.request.urlopen(req, timeout=8)
            time.sleep(0.3)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                body = re.sub(
                    r'<li[^>]*>[^<]*(?:<[^>]*>)*[^<]*PMID[:\s]+' + pmid + r'.*?</li>\s*',
                    '', body, flags=re.DOTALL)
                print(f"  REMOVED fake PMID {pmid} from {os.path.basename(f)}")
                removed_total += 1
                changed = True
        except Exception:
            pass
    if changed:
        open(f, "w").write(body)

print(f"  PMID check done. Removed {removed_total} unresolvable citations.")
PYEOF

# Step 1: Fetch realistic stock photos (Unsplash primary, Pexels fallback)
echo "[1/6] Fetching stock photos (Unsplash + Pexels)..."
python3 << 'PYEOF'
import json, urllib.request, urllib.parse, glob, os, time

unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
pexels_key = os.environ.get("PEXELS_API_KEY", "")

pixabay_key = os.environ.get("PIXABAY_API_KEY", "")

if not unsplash_key and not pexels_key and not pixabay_key:
    print("  WARN: no image API key set — skipping image fetch (will fall back "
          "to local covers/no images at publish time)")
    raise SystemExit(0)

# Scope work to today's batch — meta.json files whose date_published equals
# BATCH_DATE. Fallback (no BATCH_DATE set or empty result): only metas missing
# resolved_cover. Avoids re-fetching images for 500+ legacy articles every run.
batch_date = os.environ.get("BATCH_DATE", "")

def _is_today(meta):
    if not batch_date:
        return True
    return (meta.get("date_published") or "").startswith(batch_date)

UTM = "?utm_source=happy_aging&utm_medium=referral"

# Images containing any of these terms in alt/description are rejected
BLOCKED_TERMS = {
    "nude", "naked", "topless", "nudity", "lingerie", "bikini",
    "underwear", "explicit", "adult content", "erotic", "sensual",
    "sexy", "sexual", "pornographic", "nsfw",
    "belly", "abdomen", "navel", "torso", "bare skin", "bare stomach",
    "cesarean", "c-section", "surgical scar", "scar", "wound", "surgery",
    "stretch mark", "skin close", "close-up skin", "skin texture",
    "supplement", "vitamin", "capsule", "pill", "tablet",
    "bottle", "vial", "jar", "tube", "container", "packaging",
    "product", "serum bottle", "cosmetic bottle", "beauty bottle",
    "holding bottle", "holding vial", "holding supplement",
    "tattoo", "tattooed", "tattoos",
    "book cover", "dopamine detox",
    "hospital", "clinic", "medicine",
}

COMPETITOR_BRANDS = {
    "vigorvault", "vigor vault", "nmn revive", "nmn activ", "lifeextension",
    "life extension", "thorne", "jarrow", "now foods", "garden of life",
    "nature's bounty", "gnc", "optimum nutrition", "ritual",
    "elysium", "tru niagen", "alive by science", "wonderfeel", "donotage",
    "do not age", "renue", "maac10",
    "osh wellness", "osh ", "missha",
    "neocell", "youtheory", "vital proteins", "sports research",
    "swanson", "solgar", "natrol", "nature made",
}

def is_safe(alt_text):
    text = (alt_text or "").lower()
    if any(t in text for t in BLOCKED_TERMS):
        return False
    if any(b in text for b in COMPETITOR_BRANDS):
        return False
    return True

def unsplash_search(query):
    if not unsplash_key: return None
    try:
        url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({
            "query": query, "orientation": "landscape", "per_page": 5, "content_filter": "high"})
        req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {unsplash_key}"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if not data.get("results"): return None
        safe = [p for p in data["results"]
                if is_safe((p.get("alt_description") or "") + " " + (p.get("description") or ""))]
        if not safe: return None
        p = safe[0]
        try:
            dl = urllib.request.Request(p["links"]["download_location"],
                headers={"Authorization": f"Client-ID {unsplash_key}"})
            urllib.request.urlopen(dl, timeout=10)
        except Exception: pass
        return {
            "src": p["urls"]["regular"],
            "alt": (p.get("alt_description") or query)[:120],
            "credit_name": p["user"]["name"],
            "credit_url": p["user"]["links"]["html"] + UTM,
            "provider": "Unsplash",
            "provider_url": "https://unsplash.com/" + UTM,
        }
    except Exception as e:
        print(f"    unsplash fail '{query[:30]}': {str(e)[:50]}"); return None

def pexels_search(query):
    if not pexels_key: return None
    try:
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode({
            "query": query, "orientation": "landscape", "per_page": 10})
        headers = {
            "Authorization": pexels_key,
            "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
            "Accept": "application/json",
        }
        req = urllib.request.Request(url, headers=headers)
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if not data.get("photos"): return None
        safe = [p for p in data["photos"] if is_safe(p.get("alt") or "")]
        if not safe: return None
        p = safe[0]
        return {
            "src": p["src"]["large2x"],
            "alt": (p.get("alt") or query)[:120],
            "credit_name": p["photographer"],
            "credit_url": p["photographer_url"],
            "provider": "Pexels",
            "provider_url": "https://www.pexels.com/",
        }
    except Exception as e:
        print(f"    pexels fail '{query[:30]}': {str(e)[:50]}"); return None

def pixabay_search(query):
    if not pixabay_key: return None
    try:
        url = "https://pixabay.com/api/?" + urllib.parse.urlencode({
            "key": pixabay_key, "q": query, "image_type": "photo",
            "orientation": "horizontal", "per_page": 20, "safesearch": "true"})
        data = json.loads(urllib.request.urlopen(url, timeout=15).read())
        hits = [h for h in (data.get("hits") or [])
                if is_safe((h.get("tags") or "") + " " + (h.get("user") or ""))
                and (h.get("largeImageURL") or h.get("webformatURL"))]
        if not hits: return None
        h = hits[0]
        return {"src": h.get("largeImageURL") or h["webformatURL"],
                "alt": (h.get("tags","").split(",")[0].strip() or query)[:120],
                "credit_name": h.get("user","Pixabay"),
                "credit_url": "https://pixabay.com/",
                "provider": "Pixabay", "provider_url": "https://pixabay.com/"}
    except Exception as e:
        print(f"    pixabay fail '{query[:30]}': {str(e)[:50]}"); return None

def find_image(query, fallback):
    img = pexels_search(query) or pixabay_search(query) or unsplash_search(query)
    if not img and fallback and fallback != query:
        img = pexels_search(fallback) or pixabay_search(fallback) or unsplash_search(fallback)
    return img

def fallback_query(meta):
    pk = meta.get("primary_keyword") or meta.get("title") or ""
    bad = {"supplement","vitamin","pill","capsule","product","bottle","detox"}
    words = [w for w in pk.split()[:6] if w.lower() not in bad]
    return (" ".join(words) + " woman wellness outdoor lifestyle").strip()

metas = sorted(glob.glob("articles/*.meta.json"))
updated = 0
for mf in metas:
    meta = json.load(open(mf))
    if not _is_today(meta):
        continue
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json", ""))
    fb = fallback_query(meta)
    changed = False

    if not meta.get("resolved_cover"):
        q = meta.get("image_query") or fb
        img = find_image(q, fb)
        if img:
            meta["resolved_cover"] = img; changed = True
            print(f"  COVER {slug} <- {img['provider']}")
        else:
            print(f"  SKIP cover {slug}")
        time.sleep(1)

    if not meta.get("resolved_body"):
        queries = meta.get("body_image_queries") or []
        resolved = []
        for q in queries:
            img = find_image(q, fb)
            if img: resolved.append(img)
            time.sleep(1)
        if resolved:
            meta["resolved_body"] = resolved; changed = True
            print(f"  BODY  {slug} <- {len(resolved)} images")

    if changed:
        json.dump(meta, open(mf, "w"), indent=2, ensure_ascii=False)
        updated += 1

print(f"  Resolved images for {updated} articles")
PYEOF

# Step 2: Fix product card images + prices
echo "[2/6] Fixing product card images and prices..."
python3 << 'PYEOF'
import json, urllib.request, re, glob, os

img_map = {}
price_map = {}
try:
    page = 1
    while True:
        data = json.loads(urllib.request.urlopen(
            f"https://happyaging.com/products.json?limit=250&page={page}").read())
        products = data.get("products", [])
        if not products:
            break
        for p in products:
            h = p["handle"]
            if p.get("images"):
                img_map[h] = p["images"][0]["src"]
            variants = p.get("variants", [])
            if variants:
                min_price = min(float(v["price"]) for v in variants)
                price_map[h] = str(int(min_price)) if min_price == int(min_price) else f"{min_price:.2f}"
        page += 1
except Exception as e:
    print(f"  WARNING: Could not fetch product data: {e}")

print(f"  {len(price_map)} products found")

def fix_card(card):
    hm = re.search(r'happyaging\.com/products/([a-z0-9-]+)', card)
    if not hm:
        return card
    handle = hm.group(1)
    # Fix image
    img_m = re.search(r'<img[^>]+src="([^"]+)"', card)
    if img_m and "cdn.shopify.com/s/files/1/0869/3704/3264/" not in img_m.group(1):
        real = img_map.get(handle)
        if real:
            card = card.replace(img_m.group(1), real)
    # Fix price
    price = price_map.get(handle)
    if price:
        card = re.sub(r'\$[\d.]+/month', f'${price}/month', card)
    return card

fixed = 0
for f in sorted(glob.glob("articles/*-final.html")):
    body = open(f).read()
    new_body = re.sub(
        r'<div class="product-card-inline">.*?</div>\s*</div>',
        fix_card, body, flags=re.DOTALL)
    if new_body != body:
        open(f, "w").write(new_body)
        fixed += 1
print(f"  Fixed product cards in {fixed} articles")
PYEOF

# Step 3: Validate DOIs
echo "[3/6] Validating DOIs..."
python3 << 'PYEOF'
import re, glob, json, os, urllib.request, urllib.error

batch_date = os.environ.get("BATCH_DATE", "")

def _today_html_files():
    if not batch_date:
        return sorted(glob.glob("articles/*-final.html"))
    out = []
    for mf in sorted(glob.glob("articles/*.meta.json")):
        try:
            m = json.load(open(mf))
        except Exception:
            continue
        if not (m.get("date_published") or "").startswith(batch_date):
            continue
        slug = m.get("slug", os.path.basename(mf).replace(".meta.json", ""))
        p = f"articles/{slug}-final.html"
        if os.path.exists(p):
            out.append(p)
    return out

removed = 0
for f in _today_html_files():
    body = open(f).read()
    dois = set(re.findall(r"(10\.\d{4,9}/[^\s<\"&;]+)", body))
    changed = False
    for doi in dois:
        doi_clean = doi.rstrip(".")
        try:
            req = urllib.request.Request(f"https://doi.org/{doi_clean}", method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0")
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Try to remove the entire <li> containing this DOI
                pattern = re.compile(r"<li[^>]*>(?:[^<]|<(?!/li>))*?" + re.escape(doi_clean) + r".*?</li>\s*", re.DOTALL)
                body, n = pattern.subn("", body)
                if n > 0:
                    changed = True; removed += 1
                else:
                    # DOI not in a <li> — log and skip; do NOT replace inline
                    print(f"  WARNING: DOI {doi_clean} not in <li> in {os.path.basename(f)} — skipping")
        except: pass
    if changed: open(f, "w").write(body)
print(f"  Removed {removed} fake DOIs")
PYEOF

# Step 4: Insert section-relevant body images and inject FAQ schema + meta description
echo "[4/6] Inserting section images, FAQ schema, and meta description..."
python3 << 'PYEOF'
import json, glob, os, re, sys, time, urllib.request, urllib.parse, urllib.error

# Batch scoping: only act on today's articles. Without this, the loop iterates
# every meta.json in the repo (500+) re-injecting CTAs and re-rendering schema
# on already-published articles every single run.
batch_date = os.environ.get("BATCH_DATE", "")

def _is_today(meta):
    if not batch_date:
        return True
    return (meta.get("date_published") or "").startswith(batch_date)

pexels_key   = os.environ.get("PEXELS_API_KEY", "")
unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
pixabay_key  = os.environ.get("PIXABAY_API_KEY", "")

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
    # Actual product shots (multi-word — don't block innocent uses of "jar" etc.)
    "supplement bottle", "vitamin bottle", "pill bottle", "medicine bottle",
    "cosmetic bottle", "serum bottle", "beauty bottle",
    "holding bottle", "holding supplement", "holding pill", "holding vial",
    "pill box", "blister pack",
    # Off-brand aesthetics
    "tattoo", "tattooed",
    "book cover",
    "fast food", "junk food", "cigarette", "smoking",
    # Wrong persona
    " man,", " man.", "men's", "elderly man", "old man", "grandfather",
    " boy ", " boys ", "child", "children",
    "baby", "infant", "toddler",
}

COMPETITOR_BRANDS = {
    "vigorvault", "vigor vault", "nmn revive", "nmn activ", "lifeextension",
    "life extension", "thorne", "jarrow", "now foods", "garden of life",
    "nature's bounty", "gnc", "optimum nutrition", "ritual", "hims", "hers",
    "elysium", "tru niagen", "tru longevity", "alive by science",
    "wonderfeel", "donotage", "do not age", "renue", "maac10",
    "osh wellness", "osh ", "missha",
    "neocell", "youtheory", "vital proteins", "sports research",
    "bronson", "swanson", "solgar", "natrol", "nature made",
    "garden of", "nutricost", "bulk supplements",
}

TOPIC_VISUAL_CONTEXT = {
    "ampk": "outdoor exercise morning",
    "autophagy": "meditating peaceful sunrise",
    "nattokinase": "jogging coastal path",
    "collagen": "glowing skin healthy portrait",
    "gut": "eating healthy meal kitchen",
    "microbiome": "preparing vegetables colorful",
    "probiotic": "eating yogurt bowl kitchen",
    "glucomannan": "healthy meal vegetables satisfied",
    "sleep": "peaceful bedroom morning",
    "magnesium": "relaxing calm evening",
    "omega": "healthy meal salmon vegetables",
    "protein": "gym workout active",
    "muscle": "strength training confident",
    "menopause": "hiking nature confident",
    "hormone": "yoga outdoor calm",
    "thyroid": "walking outdoor energetic",
    "iodine": "cooking healthy meal",
    "vitamin": "eating fruit outdoor",
    "zinc": "cooking colorful vegetables",
    "iron": "energetic morning run",
    "calcium": "yoga stretching outdoor",
    "dhea": "active lifestyle outdoor",
    "testosterone": "strength training weights",
    "estrogen": "walking garden serene",
    "cortisol": "meditation breathing calm",
    "inflammation": "healthy salad bowl",
    "antioxidant": "eating berries colorful",
    "resveratrol": "eating grapes vineyard",
    "butyrate": "cooking fiber vegetables",
    "phosphatidylserine": "reading focused morning",
    "lion's mane": "focused writing outdoor",
    "ashwagandha": "yoga meditation calm",
    "berberine": "healthy meal balanced",
}

SAFE_FALLBACK_QUERIES = [
    "woman 40s healthy lifestyle outdoor",
    "woman wellness nature morning",
    "woman healthy eating kitchen",
    "woman yoga outdoor serene",
    "woman walking park smiling",
]

def _safe(text):
    t = (text or "").lower()
    return (not any(k in t for k in BLOCKED_TERMS)
            and not any(b in t for b in COMPETITOR_BRANDS))

def pexels_search(query):
    if not pexels_key: return None
    try:
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": query, "orientation": "landscape", "per_page": 30})
        headers = {
            "Authorization": pexels_key,
            "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
            "Accept": "application/json",
        }
        req = urllib.request.Request(url, headers=headers)
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        safe = [p for p in (data.get("photos") or []) if _safe(p.get("alt") or "")]
        if not safe: return None
        return {"src": safe[0]["src"]["large2x"], "alt": (safe[0].get("alt") or query)[:120]}
    except Exception: return None

def unsplash_search(query):
    if not unsplash_key: return None
    try:
        url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
            {"query": query, "orientation": "landscape", "per_page": 15, "content_filter": "high"})
        req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {unsplash_key}"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        safe = [p for p in (data.get("results") or [])
                if _safe((p.get("alt_description") or "") + " " + (p.get("description") or ""))]
        if not safe: return None
        p = safe[0]
        return {"src": p["urls"]["regular"], "alt": (p.get("alt_description") or query)[:120]}
    except Exception: return None

def pixabay_search_step4(query):
    if not pixabay_key: return None
    try:
        url = "https://pixabay.com/api/?" + urllib.parse.urlencode({
            "key": pixabay_key, "q": query, "image_type": "photo",
            "orientation": "horizontal", "per_page": 20, "safesearch": "true"})
        data = json.loads(urllib.request.urlopen(url, timeout=15).read())
        hits = [h for h in (data.get("hits") or [])
                if _safe((h.get("tags") or "") + " " + (h.get("user") or ""))
                and (h.get("largeImageURL") or h.get("webformatURL"))]
        if not hits: return None
        h = hits[0]
        return {"src": h.get("largeImageURL") or h["webformatURL"],
                "alt": (h.get("tags","").split(",")[0].strip() or query)[:120]}
    except Exception: return None

def find_image(query, fallbacks=None):
    img = pexels_search(query) or pixabay_search_step4(query) or unsplash_search(query)
    if not img and fallbacks:
        for fb in fallbacks:
            img = pexels_search(fb) or pixabay_search_step4(fb) or unsplash_search(fb)
            if img: break
    time.sleep(1.2)
    return img

def h2_to_query(h2_text, article_title=""):
    combined = (h2_text + " " + article_title).lower()
    for keyword, visual in TOPIC_VISUAL_CONTEXT.items():
        if keyword in combined:
            return "woman " + visual
    skip = {"what","why","how","the","a","an","and","or","of","to","is","are",
            "for","after","with","your","that","in","on","at","by","does","do",
            "can","will","about","from","this","40","over","women","woman",
            "supplement","vitamin","capsule","pill","tablet","dose","bottle"}
    words = [w.strip(".,?:!-()") for w in h2_text.split()
             if w.lower().strip(".,?:!-()") not in skip
             and len(w.strip(".,?:!-()")) > 2][:4]
    if not words:
        words = [w.strip(".,?:!-()") for w in article_title.split()
                 if w.lower().strip(".,?:!-()") not in skip][:3]
    return "woman " + " ".join(words).lower() + " outdoor lifestyle"

def fetch_products_for_linking():
    """Return (prices_dict, linking_list) from the public store."""
    _STOP = {"happy","aging","supplement","formula","complex","blend","advanced",
             "ultra","daily","plus","pro","extra","strength","boost","pure",
             "natural","organic","the","for","women","woman","men","support","with","and"}
    prices, linking = {}, []
    for page in range(1, 5):
        try:
            data = json.loads(urllib.request.urlopen(
                f"https://happyaging.com/products.json?limit=250&page={page}", timeout=15).read())
            prods = data.get("products", [])
            if not prods: break
            for p in prods:
                h = p["handle"]
                variants = p.get("variants", [])
                if variants:
                    mp = min(float(v["price"]) for v in variants)
                    prices[h] = str(int(mp)) if mp == int(mp) else f"{mp:.2f}"
                cleaned = re.sub(r'\b\d+\s*(?:mg|mcg|g|iu|ml|caps?|tablets?|count)\b',
                                 '', p.get("title",""), flags=re.IGNORECASE)
                words = [w.strip('-') for w in cleaned.split()
                         if w.lower().strip('-') not in _STOP and len(w.strip('-')) > 2]
                kws = list(dict.fromkeys(
                    ([" ".join(words[:2])] if len(words) >= 2 else []) +
                    [w for w in words if len(w) >= 4]))
                if kws:
                    linking.append({
                        "handle": h, "title": p.get("title",""), "keywords": kws,
                        "img_url": (p["images"][0]["src"] if p.get("images") else ""),
                    })
            time.sleep(0.2)
        except Exception:
            break
    return prices, linking


def _inject_link_in_para(para_html, kw, url):
    kw_re = re.compile(r'\b' + re.escape(kw) + r'\b', re.I)
    result, i, in_link, done = [], 0, False, False
    while i < len(para_html):
        if para_html[i] == '<':
            j = para_html.find('>', i)
            if j < 0: result.append(para_html[i:]); break
            tag = para_html[i:j+1]
            if re.match(r'<a\b', tag, re.I): in_link = True
            elif re.match(r'</a', tag, re.I): in_link = False
            result.append(tag); i = j+1
        else:
            j = para_html.find('<', i)
            if j < 0: j = len(para_html)
            text = para_html[i:j]
            if not done and not in_link:
                m = kw_re.search(text)
                if m:
                    s, e = m.start(), m.end()
                    text = (text[:s] +
                            f'<a href="{url}" style="color:#8B7355;font-weight:600">'
                            + text[s:e] + '</a>' + text[e:])
                    done = True
            result.append(text); i = j
    return "".join(result), done


def inject_product_links(html, products, max_links=2):
    if not products: return html
    injected = 0
    for prod in products:
        if injected >= max_links: break
        prod_url = f"https://happyaging.com/products/{prod['handle']}"
        found = False
        for kw in prod["keywords"]:
            if found or injected >= max_links: break
            if len(kw) < 3: continue
            paras = list(re.finditer(r'<p\b[^>]*>.*?</p>', html, re.DOTALL))
            for pm in paras[2:]:
                para = pm.group(0)
                if prod_url in para: found = True; break
                if not re.search(r'\b' + re.escape(kw) + r'\b',
                                 re.sub(r'<[^>]+>', '', para), re.I): continue
                new_para, did_inject = _inject_link_in_para(para, kw, prod_url)
                if did_inject:
                    html = html[:pm.start()] + new_para + html[pm.end():]
                    injected += 1; found = True; break
    return html


def inject_product_cta(html, products, prices, article_title):
    if 'class="article-product-cta"' in html or not products: return html
    title_lower = article_title.lower()
    best_prod, best_score = None, 0
    for prod in products:
        score = sum(1 for kw in prod["keywords"]
                    if re.search(r'\b' + re.escape(kw) + r'\b', title_lower, re.I))
        if score > best_score: best_score, best_prod = score, prod
    if not best_prod or best_score == 0:
        body_text = re.sub(r'<[^>]+>', '', html).lower()
        for prod in products:
            for kw in prod["keywords"]:
                if len(kw) >= 4 and re.search(r'\b' + re.escape(kw) + r'\b', body_text, re.I):
                    best_prod = prod; break
            if best_prod: break
    if not best_prod: return html
    handle    = best_prod["handle"]
    prod_url  = f"https://happyaging.com/products/{handle}"
    price     = prices.get(handle, "")
    img_url   = best_prod.get("img_url", "")
    short_name = re.sub(r'\b\d+\s*(?:mg|mcg|g|iu|ml|caps?|tablets?|count)\b',
                        '', best_prod["title"], flags=re.I).strip()
    price_line = f" — from ${price}/month" if price else ""
    _skip = {"why","how","what","when","is","are","the","a","an","for","and","or",
             "of","to","in","on","at","after","40","over","women","woman","your",
             "you","do","does","can","will","with","its","this","that","these"}
    topic_words = [w.strip("?,.:;!'\"") for w in article_title.split()
                   if w.lower().strip("?,.:;!'\"") not in _skip
                   and len(w.strip("?,.:;!'\"")) > 3]
    topic = " ".join(topic_words[:3]).lower() if topic_words else "healthy aging"
    matching_kw = next(
        (kw for kw in best_prod["keywords"]
         if re.search(r'\b' + re.escape(kw) + r'\b', title_lower, re.I)
         and len(kw) >= 4),
        topic
    )
    intro = (f"Many women over 40 reading about {matching_kw} find that adding "
             f"{short_name} to their daily routine makes a real difference.")
    img_block = (f'<img src="{img_url}" alt="{short_name}" '
                 'style="width:100px;height:100px;object-fit:contain;'
                 'border-radius:8px;background:#fff;flex-shrink:0">\n'
                 if img_url else "")
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
        f'<a href="{prod_url}" style="display:inline-block;background:#8B7355;color:#fff;'
        'padding:11px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px">'
        f'Try {short_name}{price_line} →</a>\n'
        '</div>\n</div>\n</div>\n'
    )
    new_html = re.sub(r'(<h2[^>]*>\s*(?:Frequently Asked Questions|FAQ)\s*</h2>)',
                      cta + r'\1', html, count=1, flags=re.I)
    if new_html != html: return new_html
    h2s = list(re.finditer(r'<h2[^>]*>', html))
    if len(h2s) >= 2:
        p = h2s[-1].start()
        return html[:p] + cta + html[p:]
    return html + cta


def extract_faq_pairs(html):
    faq = re.search(
        r'<h2[^>]*>Frequently Asked Questions</h2>(.*?)(?:<h2[^>]*>References|$)',
        html, re.DOTALL | re.IGNORECASE)
    if not faq: return []
    pairs = []
    for m in re.finditer(r'<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>', faq.group(1), re.DOTALL):
        q = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        a = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(2))).strip()
        if q and a and len(q) > 10:
            pairs.append((q, a))
    return pairs

def build_faq_schema(pairs):
    schema = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}}
                             for q, a in pairs]}
    return ('\n<script type="application/ld+json">\n'
            + json.dumps(schema, ensure_ascii=False, indent=2) + '\n</script>\n')

def meta_description(html, max_chars=155):
    m = re.search(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    if not m: return ""
    text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip()
    if len(text) <= max_chars: return text
    return text[:max_chars].rsplit(' ', 1)[0].rstrip('.,;:') + '...'

print("  Fetching products for linking + CTA...")
prices, products_for_linking = fetch_products_for_linking()
print(f"  {len(products_for_linking)} products loaded for contextual linking.")

inserted = schema_added = links_added = ctas_added = 0
for mf in sorted(glob.glob("articles/*.meta.json")):
    meta = json.load(open(mf))
    if not _is_today(meta):
        continue
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json", ""))
    title = meta.get("title", slug)
    html_file = f"articles/{slug}-final.html"
    if not os.path.exists(html_file): continue

    body = open(html_file).read()

    # Remove legacy figcaptions, old stock images, and [BODY_IMAGE_N] placeholders (all formats)
    body = re.sub(r'<figcaption[^>]*>.*?</figcaption>', '', body, flags=re.DOTALL)
    body = re.sub(r'\s*<figure class="article-stock-image"[^>]*>.*?</figure>\s*',
                  '\n', body, flags=re.DOTALL)
    body = re.sub(r'\[BODY_IMAGE_\d+\]', '', body)
    body = re.sub(r'<img[^>]+src="\[BODY_IMAGE_\d+\]"[^>]*/?>', '', body)
    body = re.sub(r'<figure[^>]*>\s*<img[^>]+src="\[BODY_IMAGE_\d+\]"[^>]*/?>\s*</figure>', '', body)

    # Insert section-relevant images
    skip_h2s = {"frequently asked questions", "references", "faq"}
    h2_matches = [(m.end(), re.sub(r'<[^>]+>', '', m.group(1)).strip())
                  for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', body, re.DOTALL)
                  if re.sub(r'<[^>]+>', '', m.group(1)).strip().lower() not in skip_h2s]

    targets = h2_matches[1:4]  # skip first H2, max 3 images
    body_image_queries = meta.get("body_image_queries") or []
    offset = 0
    for i, (pos, h2_text) in enumerate(targets):
        if body_image_queries and i < len(body_image_queries):
            primary_query = body_image_queries[i]
            derived = h2_to_query(h2_text, title)
            fallbacks = [derived] + SAFE_FALLBACK_QUERIES[:2]
        else:
            primary_query = h2_to_query(h2_text, title)
            fallbacks = SAFE_FALLBACK_QUERIES[:2]
        img = find_image(primary_query, fallbacks)
        if not img: continue
        alt = img.get("alt", title)[:140].replace('"', "'")
        figure = (f'\n<figure class="article-stock-image" style="margin:24px 0">'
                  f'<img src="{img["src"]}" alt="{alt}" '
                  f'style="width:100%;border-radius:12px;display:block">'
                  f'</figure>\n')
        insert_at = pos + offset
        body = body[:insert_at] + figure + body[insert_at:]
        offset += len(figure)
    inserted += 1

    # Contextual product links (1-2 subtle inline links)
    if products_for_linking:
        before = body
        body = inject_product_links(body, products_for_linking)
        if body != before: links_added += 1

    # Product CTA block (prominent, before FAQ section)
    if products_for_linking:
        before = body
        body = inject_product_cta(body, products_for_linking, prices, title)
        if body != before: ctas_added += 1

    # FAQ Schema
    pairs = extract_faq_pairs(body)
    if pairs:
        body = re.sub(
            r'\s*<script type="application/ld\+json">\s*\{[^}]*"FAQPage".*?</script>\s*',
            '\n', body, flags=re.DOTALL)
        schema_block = build_faq_schema(pairs)
        body = re.sub(r'(<h2[^>]*>Frequently Asked Questions</h2>)',
                      schema_block + r'\1', body, flags=re.IGNORECASE)
        schema_added += 1

    # MedicalWebPage / Article schema with reviewer Person + HowTo (GEO E-E-A-T)
    sys.path.insert(0, os.path.abspath("articles"))
    try:
        from lib_medical_schema import inject_medical_schema
        body = inject_medical_schema(
            body, title=title, slug=slug,
            meta_desc=meta.get("meta_description") or meta_description(body),
            meta=meta,
        )
    except Exception as e:
        print(f"  WARN: medical schema injection failed for {slug}: {e}")

    # Meta description saved to meta.json for use at publish time
    meta["meta_description"] = meta_description(body)
    json.dump(meta, open(mf, "w"), indent=2, ensure_ascii=False)

    open(html_file, "w").write(body)

print(f"  Section images injected:  {inserted} articles")
print(f"  Product links injected:   {links_added} articles")
print(f"  Product CTA blocks added: {ctas_added} articles")
print(f"  FAQ schema added:         {schema_added} articles")
PYEOF

# Step 5: Publish to Shopify (articles + covers)
echo "[5/6] Publishing to Shopify..."
python3 << PYEOF
import json, urllib.request, glob, os, re, time, base64

shopify_token = "${SHOPIFY_TOKEN}"
api = "${API_URL}"
covers_dir = "articles/covers"
batch_date = os.environ.get("BATCH_DATE", "")

# Get existing articles, indexed by BOTH title and handle (slug). Title-only
# dedup breaks when Phase 4 rewrites titles between runs — slug stays stable.
def _fetch_existing():
    by_title, by_handle = {}, {}
    page_url = f"{api}?limit=250&fields=id,title,handle"
    while page_url:
        req = urllib.request.Request(page_url, headers={"X-Shopify-Access-Token": shopify_token})
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        for a in data.get("articles", []):
            by_title[a["title"].lower().strip()] = a["id"]
            if a.get("handle"):
                by_handle[a["handle"].lower().strip()] = a["id"]
        # Shopify pagination via Link header
        link = resp.headers.get("Link", "")
        m = re.search(r'<([^>]+)>;\s*rel="next"', link or "")
        page_url = m.group(1) if m else None
    return by_title, by_handle

existing_titles, existing_handles = _fetch_existing()

metas = sorted(glob.glob("articles/*.meta.json"))
published = 0

for mf in metas:
    meta = json.load(open(mf))
    # Only publish today's batch — never re-publish legacy metas.
    if batch_date and not (meta.get("date_published") or "").startswith(batch_date):
        continue
    title = meta.get("title","").strip()
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json",""))
    # Slug-based dedup is the source of truth (stable across title rewrites).
    if slug.lower() in existing_handles: continue
    if title.lower() in existing_titles: continue

    html_file = f"articles/{slug}-final.html"
    if not os.path.exists(html_file): continue

    body = open(html_file).read()
    tags = meta.get("tags","")
    if isinstance(tags, list): tags = ", ".join(tags)

    summary = meta.get("meta_description", "")[:155]
    # Publish as DRAFT by default — user reviews + publishes manually in Shopify.
    # Override with PUBLISH_DRAFT=false (e.g. for one-off auto-publish runs).
    publish_draft = os.environ.get("PUBLISH_DRAFT", "true").lower() != "false"
    is_published = not publish_draft
    payload = {"article": {"title": title, "body_html": body, "summary_html": summary,
               "author": "Happy Aging Team", "tags": tags, "published": is_published,
               "template_suffix": "timeline"}}

    # Cover image: prefer resolved stock URL; fall back to legacy local file
    cover = meta.get("resolved_cover")
    if cover and cover.get("src"):
        payload["article"]["image"] = {"src": cover["src"], "alt": title}
    else:
        cover_file = f"{covers_dir}/{slug}-cover.jpg"
        if os.path.exists(cover_file):
            with open(cover_file, "rb") as f:
                payload["article"]["image"] = {"attachment": base64.b64encode(f.read()).decode(), "alt": title}

    data = json.dumps(payload).encode()
    req = urllib.request.Request(api, data=data, method="POST",
        headers={"X-Shopify-Access-Token": shopify_token, "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        aid = result["article"]["id"]
        published += 1
        existing_titles[title.lower()] = aid
        if result["article"].get("handle"):
            existing_handles[result["article"]["handle"].lower()] = aid
        print(f"  OK {title[:50]} (id:{aid})")
    except Exception as e:
        print(f"  ERR {slug}: {str(e)[:80]}")
    time.sleep(1)

print(f"  Published {published} new articles")
PYEOF

# Step 6: Verify
echo "[6/6] Verifying..."
python3 << PYEOF
import urllib.request, json
req = urllib.request.Request("${API_URL}?limit=1&fields=id", headers={"X-Shopify-Access-Token": "${SHOPIFY_TOKEN}"})
# Just count
req2 = urllib.request.Request("https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/${BLOG_ID}/articles/count.json", headers={"X-Shopify-Access-Token": "${SHOPIFY_TOKEN}"})
count = json.loads(urllib.request.urlopen(req2).read())["count"]
print(f"  Total articles on Shopify: {count}")
PYEOF

echo ""
echo "=== QA + Publish complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG_FILE"

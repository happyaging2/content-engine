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

echo "=== JARVIS QA + Publish: Batch ${BATCH_DATE} ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$LOG_FILE"

# Step 0: Pull latest
echo "[0/6] Pulling latest from git..."
git pull origin main --quiet

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

if not unsplash_key and not pexels_key:
    print("  ERR: set UNSPLASH_ACCESS_KEY and/or PEXELS_API_KEY"); raise SystemExit(1)

UTM = "?utm_source=happy_aging&utm_medium=referral"

# Images containing any of these terms in alt/description are rejected
BLOCKED_TERMS = {
    "nude", "naked", "topless", "nudity", "lingerie", "bikini",
    "underwear", "explicit", "adult content", "erotic", "sensual",
    "sexy", "sexual", "pornographic", "nsfw",
}

def is_safe(img):
    text = ((img.get("alt_description") or "") + " " + (img.get("description") or "")).lower()
    return not any(t in text for t in BLOCKED_TERMS)

def unsplash_search(query):
    if not unsplash_key: return None
    try:
        url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({
            "query": query, "orientation": "landscape", "per_page": 5, "content_filter": "high"})
        req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {unsplash_key}"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if not data.get("results"): return None
        # Pick first result that passes safety check
        safe = [p for p in data["results"] if is_safe(p)]
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
        req = urllib.request.Request(url, headers={"Authorization": pexels_key})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if not data.get("photos"): return None
        # Pick first result whose alt passes safety check
        safe = [p for p in data["photos"]
                if not any(t in (p.get("alt") or "").lower() for t in BLOCKED_TERMS)]
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

def find_image(query, fallback):
    img = unsplash_search(query) or pexels_search(query)
    if not img and fallback and fallback != query:
        img = unsplash_search(fallback) or pexels_search(fallback)
    return img

def fallback_query(meta):
    pk = meta.get("primary_keyword") or meta.get("title") or ""
    return (" ".join(pk.split()[:6]) + " woman wellness").strip()

metas = sorted(glob.glob("articles/*.meta.json"))
updated = 0
for mf in metas:
    meta = json.load(open(mf))
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

# Step 2: Fix product card images
echo "[2/6] Fixing product card images..."
python3 << 'PYEOF'
import json, urllib.request, re, glob, os

pmap = {}
try:
    products = json.loads(urllib.request.urlopen("https://happyaging.com/products.json?limit=250").read())["products"]
    for p in products:
        if p.get("images"):
            pmap[p["handle"]] = p["images"][0]["src"]
except:
    print("  WARNING: Could not fetch product images")

fixed = 0
for f in sorted(glob.glob("articles/*-final.html")):
    body = open(f).read()
    changed = False
    for m in re.finditer(r'product-card-inline.*?happyaging\.com/products/([a-z0-9-]+).*?<img[^>]+src="([^"]+)"', body, re.DOTALL):
        handle, src = m.group(1), m.group(2)
        if "cdn.shopify.com/s/files/1/0869/3704/3264/" in src: continue
        real = pmap.get(handle)
        if real:
            body = body.replace(src, real)
            changed = True
    if changed:
        open(f, "w").write(body)
        fixed += 1
print(f"  Fixed {fixed} product card images")
PYEOF

# Step 3: Validate DOIs
echo "[3/6] Validating DOIs..."
python3 << 'PYEOF'
import re, glob, urllib.request

removed = 0
for f in sorted(glob.glob("articles/*-final.html")):
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
                pattern = re.compile(r"<li[^>]*>[^<]*(?:<[^>]*>)*[^<]*" + re.escape(doi_clean) + r"[^<]*(?:<[^>]*>)*[^<]*</li>\s*", re.DOTALL)
                body, n = pattern.subn("", body)
                if n == 0: body = body.replace(doi_clean, "[reference removed]")
                changed = True; removed += 1
        except: pass
    if changed: open(f, "w").write(body)
print(f"  Removed {removed} fake DOIs")
PYEOF

# Step 4: Insert stock body images into HTML from meta.resolved_body
echo "[4/6] Inserting stock body images into articles..."
python3 << 'PYEOF'
import json, glob, os, re

inserted = 0
for mf in sorted(glob.glob("articles/*.meta.json")):
    meta = json.load(open(mf))
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json", ""))
    html_file = f"articles/{slug}-final.html"
    if not os.path.exists(html_file): continue

    imgs = meta.get("resolved_body") or []
    if not imgs: continue

    body = open(html_file).read()

    # Scrub legacy DALL-E placeholders from prior runs
    body = re.sub(
        r'\s*<!-- DALLE_BODY_IMG:[^>]*-->\s*<img[^>]*PENDING_DALLE_UPLOAD[^>]*>\s*',
        "\n", body)

    if "article-stock-image" in body:
        open(html_file, "w").write(body)
        continue

    h2s = [m.end() for m in re.finditer(r"</h2>", body)]
    if len(h2s) < 2: continue

    step = max(1, len(h2s) // (len(imgs) + 1))
    insert_points = h2s[step::step][:len(imgs)]

    for img, pos in zip(reversed(imgs), reversed(insert_points)):
        alt = (img.get("alt") or meta.get("title", ""))[:140].replace('"', "'")
        figure = (
            f'\n<figure class="article-stock-image" style="margin:24px 0">'
            f'<img src="{img["src"]}" alt="{alt}" style="width:100%;border-radius:12px;display:block">'
            f'<figcaption style="font-size:12px;color:#888;margin-top:6px">'
            f'Photo by <a href="{img["credit_url"]}" rel="nofollow noopener">{img["credit_name"]}</a> '
            f'on <a href="{img["provider_url"]}" rel="nofollow noopener">{img["provider"]}</a>'
            f'</figcaption></figure>\n'
        )
        body = body[:pos] + figure + body[pos:]

    open(html_file, "w").write(body)
    inserted += 1

print(f"  Inserted stock body images into {inserted} articles")
PYEOF

# Step 5: Publish to Shopify (articles + covers)
echo "[5/6] Publishing to Shopify..."
python3 << PYEOF
import json, urllib.request, glob, os, re, time, base64

shopify_token = "${SHOPIFY_TOKEN}"
api = "${API_URL}"
covers_dir = "articles/covers"

# Get existing titles
req = urllib.request.Request(f"{api}?limit=250&fields=id,title", headers={"X-Shopify-Access-Token": shopify_token})
existing = {}
for a in json.loads(urllib.request.urlopen(req).read())["articles"]:
    existing[a["title"].lower().strip()] = a["id"]

metas = sorted(glob.glob("articles/*.meta.json"))
published = 0

for mf in metas:
    meta = json.load(open(mf))
    title = meta.get("title","").strip()
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json",""))
    if title.lower() in existing: continue

    html_file = f"articles/{slug}-final.html"
    if not os.path.exists(html_file): continue

    body = open(html_file).read()
    tags = meta.get("tags","")
    if isinstance(tags, list): tags = ", ".join(tags)

    payload = {"article": {"title": title, "body_html": body, "author": "Happy Aging Team", "tags": tags, "published": True, "template_suffix": "timeline"}}

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
        existing[title.lower()] = aid
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

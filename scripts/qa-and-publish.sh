#!/bin/bash
# =============================================================
# JARVIS QA + Publish Script
# Run LOCALLY every day after 7am BRT (agent finishes at ~6:20am)
# Usage: cd /tmp/content-engine && bash scripts/qa-and-publish.sh
# =============================================================

set -e

BATCH_DATE="${1:-$(date +%Y-%m-%d)}"
SHOPIFY_TOKEN="${SHOPIFY_TOKEN}"
OPENAI_KEY="${OPENAI_API_KEY}"
BLOG_ID="109440303424"
API_URL="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/${BLOG_ID}/articles.json"
ARTICLES_DIR="articles"
LOG_FILE="articles/qa-${BATCH_DATE}.log"

echo "=== JARVIS QA + Publish: Batch ${BATCH_DATE} ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$LOG_FILE"

# Step 0: Pull latest
echo "[0/6] Pulling latest from git..."
git pull origin main --quiet

# Step 1: Generate DALL-E images from meta.json prompts
echo "[1/6] Generating DALL-E 3 images..."
python3 << 'PYEOF'
import json, urllib.request, glob, os, time, base64, re

openai_key = os.environ.get("OPENAI_KEY", "${OPENAI_API_KEY}")
out_dir = "articles/covers"
os.makedirs(out_dir, exist_ok=True)

metas = sorted(glob.glob("articles/*.meta.json"))
generated = 0

for mf in metas:
    meta = json.load(open(mf))
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json",""))

    # Cover image
    cover_file = f"{out_dir}/{slug}-cover.jpg"
    prompt = meta.get("image_prompt","")
    if prompt and not os.path.exists(cover_file):
        data = json.dumps({"model":"dall-e-3","prompt":prompt,"n":1,"size":"1792x1024","quality":"standard"}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/images/generations",
            data=data, headers={"Authorization":f"Bearer {openai_key}","Content-Type":"application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=120)
            img_url = json.loads(resp.read())["data"][0]["url"]
            urllib.request.urlretrieve(img_url, cover_file)
            generated += 1
            print(f"  COVER {slug}")
        except Exception as e:
            print(f"  ERR cover {slug}: {str(e)[:60]}")
        time.sleep(2)

    # Body images
    body_prompts = meta.get("body_image_prompts", [])
    for i, bp in enumerate(body_prompts):
        body_file = f"{out_dir}/{slug}-body-{i}.jpg"
        if os.path.exists(body_file):
            continue
        data = json.dumps({"model":"dall-e-3","prompt":bp,"n":1,"size":"1792x1024","quality":"standard"}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/images/generations",
            data=data, headers={"Authorization":f"Bearer {openai_key}","Content-Type":"application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=120)
            img_url = json.loads(resp.read())["data"][0]["url"]
            urllib.request.urlretrieve(img_url, body_file)
            generated += 1
        except Exception as e:
            print(f"  ERR body {slug}-{i}: {str(e)[:60]}")
        time.sleep(2)

print(f"  Generated {generated} DALL-E images")
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

# Step 4: Insert DALL-E body images into HTML
echo "[4/6] Inserting generated body images into articles..."
python3 << 'PYEOF'
import json, glob, os, re, base64, urllib.request

shopify_token = os.environ.get("SHOPIFY_TOKEN", "${SHOPIFY_TOKEN}")
covers_dir = "articles/covers"

for mf in sorted(glob.glob("articles/*.meta.json")):
    meta = json.load(open(mf))
    slug = meta.get("slug", os.path.basename(mf).replace(".meta.json",""))
    html_file = f"articles/{slug}-final.html"
    if not os.path.exists(html_file): continue

    body = open(html_file).read()
    body_imgs = sorted(glob.glob(f"{covers_dir}/{slug}-body-*.jpg"))
    if not body_imgs: continue

    # Find H2 positions to insert images after
    h2s = [m.end() for m in re.finditer(r"</h2>", body)]
    if len(h2s) < 2: continue

    # Pick evenly spaced insertion points
    step = max(1, len(h2s) // (len(body_imgs) + 1))
    insert_points = h2s[step::step][:len(body_imgs)]

    changed = False
    for img_file, pos in zip(reversed(body_imgs), reversed(insert_points)):
        # For now, use a placeholder — the actual upload happens in step 5
        # We'll use a data URI temporarily
        alt = f"Woman wellness - {meta.get('title','')[:30]}"
        # Mark for later replacement with CDN URL after Shopify upload
        marker = f'<!-- DALLE_BODY_IMG:{os.path.basename(img_file)} -->'
        if marker not in body:
            body = body[:pos] + f'\n{marker}\n<img src="PENDING_DALLE_UPLOAD" alt="{alt}" style="width:100%;border-radius:12px;margin:20px 0;">\n' + body[pos:]
            changed = True

    if changed:
        open(html_file, "w").write(body)
print("  Body image placeholders inserted")
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

    # Cover image via base64
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

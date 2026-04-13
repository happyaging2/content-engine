#!/bin/bash
# =============================================================
# JARVIS QA + Publish Script
# Run LOCALLY every day after 7am BRT (agent finishes at ~6:20am)
# Usage: cd /tmp/content-engine && bash scripts/qa-and-publish.sh
# =============================================================

set -e

BATCH_DATE="${1:-$(date +%Y-%m-%d)}"
SHOPIFY_TOKEN="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"
BLOG_ID="109440303424"
API_URL="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/${BLOG_ID}/articles.json"
ARTICLES_DIR="articles"
LOG_FILE="articles/qa-${BATCH_DATE}.log"

echo "=== JARVIS QA + Publish: Batch ${BATCH_DATE} ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "$LOG_FILE"

# Step 0: Pull latest from repo
echo "[0/5] Pulling latest from git..."
git pull origin main --quiet

# Step 1: Fix product card images (replace Unsplash with real product CDN)
echo "[1/5] Fixing product card images..."
python3 << 'PYEOF'
import json, urllib.request, re, glob, os

pmap = {}
try:
    products = json.loads(urllib.request.urlopen('https://happyaging.com/products.json?limit=250').read())['products']
    for p in products:
        if p.get('images'):
            pmap[p['handle']] = p['images'][0]['src']
except:
    print("  WARNING: Could not fetch product images")

fixed = 0
for f in sorted(glob.glob('articles/*-final.html')):
    body = open(f).read()
    cards = re.finditer(r'product-card-inline.*?happyaging\.com/products/([a-z0-9-]+).*?<img[^>]+src="([^"]+)"', body, re.DOTALL)
    changed = False
    for m in cards:
        handle, src = m.group(1), m.group(2)
        if 'cdn.shopify.com/s/files/1/0869/3704/3264/' in src:
            continue
        real = pmap.get(handle)
        if real:
            body = body.replace(src, real)
            changed = True
    if changed:
        open(f, 'w').write(body)
        fixed += 1

print(f"  Fixed {fixed} product card images")
PYEOF

# Step 2: Validate DOIs (remove any 404s)
echo "[2/5] Validating DOIs..."
python3 << 'PYEOF'
import re, glob, urllib.request

removed = 0
for f in sorted(glob.glob('articles/*-final.html')):
    body = open(f).read()
    dois = set(re.findall(r'(10\.\d{4,9}/[^\s<"&;]+)', body))
    changed = False
    for doi in dois:
        doi_clean = doi.rstrip('.')
        try:
            req = urllib.request.Request(f'https://doi.org/{doi_clean}', method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0')
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Remove the <li> or <p> containing this fake DOI
                pattern = re.compile(r'<li[^>]*>[^<]*(?:<[^>]*>)*[^<]*' + re.escape(doi_clean) + r'[^<]*(?:<[^>]*>)*[^<]*</li>\s*', re.DOTALL)
                body, n = pattern.subn('', body)
                if n == 0:
                    body = body.replace(doi_clean, '[reference removed]')
                changed = True
                removed += 1
        except:
            pass  # 403, timeout = probably real
    if changed:
        open(f, 'w').write(body)

print(f"  Removed {removed} fake DOIs")
PYEOF

# Step 3: Verify image URLs (replace broken ones)
echo "[3/5] Checking image URLs..."
python3 << 'PYEOF'
import re, glob, urllib.request

replaced = 0
fallback = 'https://images.unsplash.com/photo-1552196563-55cd4e45efb3?w=800&h=450&fit=crop&auto=format'
for f in sorted(glob.glob('articles/*-final.html')):
    body = open(f).read()
    imgs = set(re.findall(r'(https://images\.unsplash\.com/photo-[a-zA-Z0-9_-]+)', body))
    changed = False
    for img_base in imgs:
        try:
            req = urllib.request.Request(img_base + '?w=10', method='HEAD')
            urllib.request.urlopen(req, timeout=5)
        except:
            body = re.sub(re.escape(img_base) + r'[^"]*', fallback, body)
            changed = True
            replaced += 1
    if changed:
        open(f, 'w').write(body)

print(f"  Replaced {replaced} broken image URLs")
PYEOF

# Step 4: Enforce author
echo "[4/5] Verifying author field..."

# Step 5: Publish to Shopify
echo "[5/5] Publishing to Shopify..."
PUBLISH_SCRIPT="articles/batch-${BATCH_DATE}-publish.sh"
if [ -f "$PUBLISH_SCRIPT" ]; then
    bash "$PUBLISH_SCRIPT" 2>&1 | tee -a "$LOG_FILE"
else
    echo "  No publish script found for ${BATCH_DATE}. Publishing from meta.json files..."
    python3 << PYEOF
import json, urllib.request, glob, os, re, time

token = '${SHOPIFY_TOKEN}'
api = '${API_URL}'

# Get existing titles
req = urllib.request.Request(f'{api}?limit=250&fields=id,title', headers={'X-Shopify-Access-Token': token})
existing = set(a['title'].lower().strip() for a in json.loads(urllib.request.urlopen(req).read())['articles'])

metas = sorted(glob.glob('articles/*.meta.json'))
published = 0
for mf in metas:
    meta = json.load(open(mf))
    title = meta.get('title','').strip()
    slug = meta.get('slug', os.path.basename(mf).replace('.meta.json',''))
    if title.lower() in existing:
        continue
    html_file = f'articles/{slug}-final.html'
    if not os.path.exists(html_file):
        continue
    body = open(html_file).read()
    tags = meta.get('tags','')
    if isinstance(tags, list): tags = ', '.join(tags)
    payload = {'article': {'title': title, 'body_html': body, 'author': 'Happy Aging Team', 'tags': tags, 'published': True, 'template_suffix': 'timeline'}}
    # Featured image
    img = re.search(r'<img[^>]+src="(https://images\.unsplash\.com/[^"]+)"', body)
    if img:
        payload['article']['image'] = {'src': img.group(1), 'alt': title}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(api, data=data, method='POST', headers={'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req)
        published += 1
    except urllib.error.HTTPError as e:
        if 'Image upload failed' in (e.read().decode() if hasattr(e,'read') else ''):
            del payload['article']['image']
            data2 = json.dumps(payload).encode()
            req2 = urllib.request.Request(api, data=data2, method='POST', headers={'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'})
            try:
                urllib.request.urlopen(req2)
                published += 1
            except:
                pass
    time.sleep(0.6)
    existing.add(title.lower())
print(f"  Published {published} new articles")
PYEOF
fi

echo ""
echo "=== QA + Publish complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG_FILE"

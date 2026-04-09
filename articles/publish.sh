#!/usr/bin/env bash
# Happy Aging — Batch Publisher
# Run from any machine with network access to shop-happy-aging.myshopify.com
# Usage: SHOPIFY_TOKEN=shpat_xxx bash publish.sh

set -euo pipefail

ARTICLES_DIR="$(cd "$(dirname "$0")" && pwd)"
TOKEN="${SHOPIFY_TOKEN:-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}"
BLOG_ID="109440303424"
STORE="shop-happy-aging.myshopify.com"
URL="https://${STORE}/admin/api/2024-01/blogs/${BLOG_ID}/articles.json"
LOG="${ARTICLES_DIR}/published.log"

SLUGS=(
  why-you-feel-tired-after-40
  nad-plus-energy-women
  signs-mitochondria-need-support
  sleep-problems-after-40
  magnesium-sleep-women-over-40
  wake-up-3am-cortisol-after-40
  perimenopause-fatigue-causes-solutions
  hormonal-belly-fat-after-40
  estrogen-decline-symptoms-after-40
  slow-metabolism-after-40
  blood-sugar-belly-fat-menopause
  weight-gain-perimenopause
  skin-dryness-after-40
  collagen-loss-after-40
  bloating-after-40-women
  gut-health-women-over-40
  brain-fog-after-40
  memory-problems-after-40-women
  immune-system-after-40-women
  chronic-inflammation-after-40
)

echo "[]" > "$LOG"
PUBLISHED=0
ERRORS=0

for i in "${!SLUGS[@]}"; do
  SLUG="${SLUGS[$i]}"
  NUM=$((i + 1))
  META="${ARTICLES_DIR}/${SLUG}.meta.json"
  HTML="${ARTICLES_DIR}/${SLUG}-final.html"

  if [[ ! -f "$META" || ! -f "$HTML" ]]; then
    echo "[${NUM}/20] SKIP (missing files): $SLUG"
    continue
  fi

  TITLE=$(python3 -c "import json,sys; d=json.load(open('$META')); print(d['title'])")
  TAGS=$(python3 -c "import json,sys; d=json.load(open('$META')); print(d['tags'])")
  BODY=$(cat "$HTML")

  PAYLOAD=$(python3 -c "
import json, sys
body = open('$HTML').read()
meta = json.load(open('$META'))
payload = {
  'article': {
    'title': meta['title'],
    'body_html': body,
    'author': 'Dr. Daniel Yadegar, MD',
    'tags': meta['tags'],
    'published': True,
    'template_suffix': 'timeline'
  }
}
print(json.dumps(payload))
")

  RESPONSE=$(curl -s -X POST "$URL" \
    -H "X-Shopify-Access-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

  ARTICLE_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['article']['id'])" 2>/dev/null || echo "")

  if [[ -n "$ARTICLE_ID" ]]; then
    HANDLE=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['article']['handle'])" 2>/dev/null)
    echo "[${NUM}/20] ✅ PUBLISHED: $TITLE"
    echo "         ID: $ARTICLE_ID | handle: $HANDLE"
    python3 -c "
import json
log = json.load(open('$LOG'))
log.append({'slug': '$SLUG', 'shopify_id': $ARTICLE_ID, 'handle': '$HANDLE', 'title': $(echo "$TITLE" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))"), 'status': 'published'})
json.dump(log, open('$LOG','w'), indent=2)
"
    PUBLISHED=$((PUBLISHED + 1))
  else
    echo "[${NUM}/20] ❌ ERROR: $SLUG"
    echo "         $RESPONSE" | head -3
    ERRORS=$((ERRORS + 1))
  fi

  if [[ $NUM -lt 20 ]]; then sleep 2; fi
done

echo ""
echo "=== BATCH COMPLETE: ${PUBLISHED}/20 published, ${ERRORS} errors ==="
echo "Log: $LOG"

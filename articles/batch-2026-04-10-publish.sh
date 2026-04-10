#!/usr/bin/env bash
# Happy Aging — Batch Publisher 2026-04-10
# Run from any machine with network access to shop-happy-aging.myshopify.com
# Usage: bash articles/batch-2026-04-10-publish.sh

set -euo pipefail

ARTICLES_DIR="$(cd "$(dirname "$0")" && pwd)"
TOKEN="${SHOPIFY_TOKEN:-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}"
BLOG_ID="109440303424"
STORE="shop-happy-aging.myshopify.com"
URL="https://${STORE}/admin/api/2024-01/blogs/${BLOG_ID}/articles.json"
LOG="${ARTICLES_DIR}/published.log"
BATCH_LOG="${ARTICLES_DIR}/batch-2026-04-10-published.json"

SLUGS=(
  what-is-nad-plus-energy-aging
  energy-after-40-without-caffeine
  hidden-energy-drains-after-40
  best-bedtime-routine-women-over-40
  menopause-insomnia-what-helps
  deep-sleep-after-40-restore
  perimenopause-symptoms-checklist
  cortisol-hormonal-symptoms-after-40
  balance-hormones-naturally-after-40
  what-is-nmn-women-over-40
  intermittent-fasting-women-over-40
  muscle-loss-after-40-women
  marine-collagen-after-40
  glutathione-skin-glow-after-40
  gut-hormone-connection-women-over-40
  probiotics-women-over-40
  coq10-brain-health-after-40
  focus-after-40-women
  brain-nutrition-after-40
  curcumin-inflammation-after-40
)

echo "[]" > "$BATCH_LOG"
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

  PAYLOAD=$(python3 - <<PYEOF
import json
body = open('$HTML').read()
meta = json.load(open('$META'))
payload = {
  'article': {
    'title': meta['title'],
    'body_html': body,
    'author': 'Happy Aging Team',
    'tags': meta.get('tags', ''),
    'published': True,
    'template_suffix': 'timeline'
  }
}
print(json.dumps(payload))
PYEOF
)

  echo "[${NUM}/20] Publishing: $(python3 -c "import json; print(json.load(open('$META'))['title'])")"

  RESPONSE=$(curl -s -X POST "$URL" \
    -H "X-Shopify-Access-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

  ARTICLE_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['article']['id'])" 2>/dev/null || echo "")

  if [[ -n "$ARTICLE_ID" ]]; then
    HANDLE=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['article']['handle'])" 2>/dev/null)
    TITLE=$(python3 -c "import json; print(json.load(open('$META'))['title'])")
    echo "  ✅ PUBLISHED — ID: $ARTICLE_ID | handle: $HANDLE"
    # Append to log
    python3 - <<PYEOF2
import json
log = json.load(open('$BATCH_LOG'))
log.append({
  'slug': '$SLUG',
  'shopify_id': $ARTICLE_ID,
  'handle': '$HANDLE',
  'title': json.load(open('$META'))['title'],
  'status': 'published',
  'batch': '2026-04-10'
})
json.dump(log, open('$BATCH_LOG', 'w'), indent=2)
PYEOF2
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) PUBLISHED slug=$SLUG id=$ARTICLE_ID handle=$HANDLE" >> "$LOG"
    PUBLISHED=$((PUBLISHED + 1))
  else
    ERROR_MSG=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('errors', d)))" 2>/dev/null || echo "$RESPONSE")
    echo "  ❌ ERROR: $ERROR_MSG"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) FAILED slug=$SLUG error=$ERROR_MSG" >> "$LOG"
    ERRORS=$((ERRORS + 1))
  fi

  # Rate limit: 2s between publishes
  if [[ $NUM -lt ${#SLUGS[@]} ]]; then sleep 2; fi
done

echo ""
echo "==================================="
echo "BATCH 2026-04-10 COMPLETE"
echo "${PUBLISHED}/20 published successfully"
echo "${ERRORS} errors"
echo "Log: $BATCH_LOG"
echo "==================================="

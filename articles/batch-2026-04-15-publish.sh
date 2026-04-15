#!/bin/bash
# Batch 2026-04-15 Shopify Publish Script
# Run from an environment with unrestricted network access
# Usage: bash batch-2026-04-15-publish.sh

TOKEN="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"
STORE="shop-happy-aging.myshopify.com"
BLOG_ID="109440303424"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${SCRIPT_DIR}/published-2026-04-15.log"

ARTICLES=(
  "signs-you-are-low-in-b12-after-40"
  "nr-vs-nmn-difference-women-over-40"
  "does-liposomal-coq10-work-energy-focus-after-40"
  "magnesium-vs-ashwagandha-sleep-stress-after-40"
  "liposomal-magnesium-vs-regular-magnesium"
  "evening-routine-women-over-40-sleep-stress"
  "signs-you-need-more-vitamin-d-after-40"
  "signs-your-inflammation-is-dropping-after-40"
  "best-time-to-take-curcumin-morning-or-night"
  "menopause-weight-management-complete-guide"
  "hormonal-fatigue-vs-adrenal-fatigue-after-40"
  "signs-hormones-coming-back-into-balance-after-40"
  "collagen-vs-biotin-hair-nails-after-40"
  "best-time-to-take-glutathione-skin-benefits"
  "signs-your-gut-is-healing-after-40"
  "fiber-after-40-women-why-you-need-more"
  "signs-you-need-more-omega-3-after-40"
  "can-nootropics-help-brain-fog-after-40"
  "how-to-build-supplement-stack-women-over-40"
  "best-anti-aging-supplements-women-over-40"
)

echo "Publishing batch-2026-04-15 (${#ARTICLES[@]} articles)..."
echo "Started: $(date)" | tee -a "$LOG"

SUCCESS=0
FAILED=0

for SLUG in "${ARTICLES[@]}"; do
  META="${SCRIPT_DIR}/${SLUG}.meta.json"
  HTML="${SCRIPT_DIR}/${SLUG}-final.html"

  if [ ! -f "$META" ] || [ ! -f "$HTML" ]; then
    echo "SKIP $SLUG — missing file"
    continue
  fi

  TITLE=$(python3 -c "import json; d=json.load(open('$META')); print(d.get('title',''))")
  TAGS=$(python3 -c "import json; d=json.load(open('$META')); print(d.get('tags',''))")

  RESPONSE=$(python3 -c "
import json, urllib.request, urllib.error
body = open('$HTML').read()
payload = json.dumps({
  'article': {
    'title': '''$TITLE''',
    'body_html': body,
    'author': 'Happy Aging Team',
    'tags': '''$TAGS''',
    'published': True,
    'template_suffix': 'timeline'
  }
}).encode('utf-8')
req = urllib.request.Request(
  'https://${STORE}/admin/api/2024-01/blogs/${BLOG_ID}/articles.json',
  data=payload,
  headers={
    'X-Shopify-Access-Token': '${TOKEN}',
    'Content-Type': 'application/json'
  },
  method='POST'
)
try:
  with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read())
    art_id = data.get('article', {}).get('id', 'unknown')
    print(f'PUBLISHED {art_id}')
except urllib.error.HTTPError as e:
  print(f'ERROR {e.code}: {e.read().decode()}')
except Exception as ex:
  print(f'EXCEPTION: {ex}')
")

  if echo "$RESPONSE" | grep -q "^PUBLISHED"; then
    ART_ID=$(echo "$RESPONSE" | awk '{print $2}')
    echo "OK  $SLUG | article_id: $ART_ID"
    echo "$SLUG | article_id:$ART_ID | $(date)" >> "$LOG"
    SUCCESS=$((SUCCESS+1))
  else
    echo "FAIL $SLUG | $RESPONSE"
    FAILED=$((FAILED+1))
  fi

  sleep 2
done

echo ""
echo "Done: $SUCCESS published, $FAILED failed"
echo "Completed: $(date)" | tee -a "$LOG"

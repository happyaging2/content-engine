#!/bin/bash
# JARVIS Batch 2026-04-13 Publish Script
# Run from: /home/user/content-engine
# Requires: SHOPIFY_TOKEN env var OR uses hardcoded token below
# Usage: bash articles/batch-2026-04-13-publish.sh

SHOPIFY_TOKEN="${SHOPIFY_TOKEN:-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}"
BLOG_ID="109440303424"
API_URL="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/${BLOG_ID}/articles.json"
AUTHOR="Happy Aging Team"
LOG_FILE="articles/published-2026-04-13.log"
ARTICLES_DIR="articles"

echo "# Batch 2026-04-13 Publish Log" > "$LOG_FILE"
echo "# Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

publish_article() {
  local SLUG="$1"
  local TITLE="$2"
  local TAGS="$3"
  local FEATURED_URL="$4"
  local FEATURED_ALT="$5"

  local BODY
  BODY=$(cat "${ARTICLES_DIR}/${SLUG}-final.html")

  local PAYLOAD
  PAYLOAD=$(python3 -c "
import json, sys
body = open('${ARTICLES_DIR}/${SLUG}-final.html').read()
payload = {
  'article': {
    'title': '''${TITLE}''',
    'author': '${AUTHOR}',
    'tags': '''${TAGS}''',
    'published': True,
    'template_suffix': 'timeline',
    'image': {'src': '${FEATURED_URL}', 'alt': '''${FEATURED_ALT}'''},
    'body_html': body
  }
}
print(json.dumps(payload))
")

  local RESPONSE
  RESPONSE=$(curl -s --max-time 30 -X POST "$API_URL" \
    -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" 2>&1)

  local ARTICLE_ID
  ARTICLE_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('article',{}).get('id',''))" 2>/dev/null)

  if [ -n "$ARTICLE_ID" ] && [ "$ARTICLE_ID" != "None" ]; then
    echo "PUBLISHED slug=${SLUG} id=${ARTICLE_ID}" | tee -a "$LOG_FILE"
  else
    local ERR
    ERR=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('errors',''))" 2>/dev/null || echo "$RESPONSE")
    echo "ERROR slug=${SLUG} err=${ERR}" | tee -a "$LOG_FILE"
  fi

  sleep 2
}

echo "Publishing 20 articles from batch 2026-04-13..."
echo ""

publish_article \
  "can-you-take-nad-and-nmn-together" \
  "Can You Take NAD+ and NMN Together? What the Research Shows" \
  "NAD+, NMN, energy, supplements, stacking, women over 40, longevity" \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=630&fit=crop" \
  "Woman with energy and vitality after 40 taking NAD+ and NMN supplements"

publish_article \
  "how-often-should-you-take-nad-supplements" \
  "How Often Should You Take NAD+ Supplements? A Dosing Guide for Women Over 40" \
  "NAD+, supplements, dosing, energy, women over 40, daily routine" \
  "https://images.unsplash.com/photo-1556909114-a1b7b3f8ce84?w=1200&h=630&fit=crop" \
  "Woman energized and healthy representing NAD+ supplement frequency guide"

publish_article \
  "signs-you-need-more-coq10-after-40" \
  "7 Signs You Need More CoQ10 After 40 (And What to Do About It)" \
  "CoQ10, energy, fatigue, supplements, women over 40, mitochondria, brain fog" \
  "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=1200&h=630&fit=crop" \
  "Woman experiencing fatigue that may signal low CoQ10 levels after 40"

publish_article \
  "how-long-does-magnesium-take-to-work-for-sleep" \
  "How Long Does Magnesium Take to Work for Sleep? A Realistic Timeline" \
  "magnesium, sleep, supplements, timeline, women over 40, insomnia, calm" \
  "https://images.unsplash.com/photo-1508214027789-b37a15a74ea4?w=1200&h=630&fit=crop" \
  "Woman sleeping peacefully after magnesium supplementation"

publish_article \
  "signs-low-magnesium-after-40" \
  "8 Signs You Are Low in Magnesium After 40 (And Why It Gets Worse With Age)" \
  "magnesium deficiency, sleep, anxiety, muscle cramps, women over 40, hormones" \
  "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=630&fit=crop" \
  "Woman showing signs of fatigue and stress that may indicate low magnesium"

publish_article \
  "can-you-take-magnesium-every-night" \
  "Can You Take Magnesium Every Night? What You Need to Know" \
  "magnesium, sleep, nightly supplements, safety, women over 40, dosing, calm" \
  "https://images.unsplash.com/photo-1571019614046-1b2af9e8ef84?w=1200&h=630&fit=crop" \
  "Woman in calm evening routine representing nightly magnesium supplementation"

publish_article \
  "what-is-dhea-women-over-40" \
  "What Is DHEA and Should Women Over 40 Take It?" \
  "DHEA, hormones, women over 40, perimenopause, longevity, NAD+, adrenal" \
  "https://images.unsplash.com/photo-1556909114-a1b7b3f8ce84?w=1200&h=630&fit=crop" \
  "Woman over 40 in healthy lifestyle representing hormonal balance and DHEA"

publish_article \
  "best-supplements-for-perimenopause" \
  "Best Supplements for Perimenopause: What Works and What Does Not" \
  "perimenopause, supplements, hormones, menopause, women over 40, NAD+, magnesium" \
  "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=1200&h=630&fit=crop" \
  "Woman navigating perimenopause with supplement support"

publish_article \
  "stacking-supplements-for-hormones-after-40" \
  "Can You Take Multiple Supplements for Hormones at Once? A Safe Stacking Guide" \
  "supplement stacking, hormones, NMN, women over 40, perimenopause, morning routine" \
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1200&h=630&fit=crop" \
  "Variety of supplements for hormone support stacking guide for women over 40"

publish_article \
  "does-coq10-help-with-weight-loss-after-40" \
  "Does CoQ10 Help with Weight Loss After 40? What the Research Actually Shows" \
  "CoQ10, weight loss, metabolism, energy, women over 40, mitochondria, exercise" \
  "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=1200&h=630&fit=crop" \
  "Woman exercising for metabolism and weight management after 40"

publish_article \
  "how-often-should-you-take-nmn" \
  "How Often Should You Take NMN? A Frequency Guide for Best Results" \
  "NMN, supplements, dosing, frequency, women over 40, metabolism, energy, NAD+" \
  "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1200&h=630&fit=crop" \
  "Woman with morning supplement routine representing NMN frequency guide"

publish_article \
  "how-often-should-you-take-collagen-supplements" \
  "How Often Should You Take Collagen Supplements? What Science Recommends" \
  "collagen, supplements, skin, frequency, women over 40, daily routine, marine collagen" \
  "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=1200&h=630&fit=crop" \
  "Woman with healthy glowing skin representing daily collagen supplementation"

publish_article \
  "collagen-and-vitamin-c-together" \
  "Can You Take Collagen and Vitamin C Together? The Science of This Power Pair" \
  "collagen, vitamin C, supplements, stacking, skin, women over 40, glow, marine collagen" \
  "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=1200&h=630&fit=crop" \
  "Fresh fruits and wellness representing collagen and vitamin C synergy"

publish_article \
  "can-you-take-quercetin-every-day" \
  "Can You Take Quercetin Every Day? Safety, Dosing, and What You Need to Know" \
  "quercetin, immunity, allergies, daily supplements, safety, women over 40, inflammation" \
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1200&h=630&fit=crop" \
  "Woman healthy and active representing daily quercetin supplementation safety"

publish_article \
  "how-often-should-you-take-probiotics-after-40" \
  "How Often Should You Take Probiotics After 40? Daily or As Needed?" \
  "probiotics, gut health, microbiome, women over 40, perimenopause, daily supplements" \
  "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=630&fit=crop" \
  "Woman eating healthy food for gut health and microbiome support after 40"

publish_article \
  "coq10-and-nad-stack-for-energy-focus" \
  "Can You Stack CoQ10 and NAD+ for More Energy and Brain Focus?" \
  "CoQ10, NAD+, stacking, brain, energy, focus, mitochondria, women over 40" \
  "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=1200&h=630&fit=crop" \
  "Woman with sharp mental focus and energy representing CoQ10 and NAD+ stack"

publish_article \
  "signs-your-brain-is-aging-faster-after-40" \
  "7 Signs Your Brain Is Aging Faster Than It Should After 40" \
  "brain aging, cognitive decline, women over 40, brain fog, memory, neuro, focus" \
  "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&h=630&fit=crop" \
  "Woman experiencing cognitive changes and brain aging signs after 40"

publish_article \
  "how-often-should-you-take-coq10" \
  "How Often Should You Take CoQ10? A Daily Dosing Guide for Women Over 40" \
  "CoQ10, supplements, dosing, frequency, women over 40, energy, mitochondria, daily" \
  "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=1200&h=630&fit=crop" \
  "Woman energized representing daily CoQ10 supplementation guide"

publish_article \
  "can-you-take-curcumin-every-day" \
  "Can You Take Curcumin Every Day? A Safety and Dosing Guide" \
  "curcumin, turmeric, inflammation, daily supplements, safety, women over 40, immunity" \
  "https://images.unsplash.com/photo-1543362906-acfb19b5b57b?w=1200&h=630&fit=crop" \
  "Woman healthy and vibrant representing daily curcumin supplementation safety"

publish_article \
  "curcumin-and-quercetin-together" \
  "Can You Take Curcumin and Quercetin Together? The Anti-Inflammatory Stack" \
  "curcumin, quercetin, inflammation, supplement stacking, immunity, women over 40, NF-kB" \
  "https://images.unsplash.com/photo-1507003235124-6cb74b9e4abe?w=1200&h=630&fit=crop" \
  "Woman with anti-inflammatory lifestyle representing curcumin and quercetin stack"

echo ""
echo "Batch 2026-04-13 publishing complete."
echo "Log saved to: $LOG_FILE"

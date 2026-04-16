#!/bin/bash
# Batch 2026-04-16 Publish Script
# Run from an unrestricted network environment
# Usage: SHOPIFY_TOKEN=shpat_xxx bash articles/batch-2026-04-16-publish.sh

SHOPIFY_TOKEN="${SHOPIFY_TOKEN:-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}"
BASE_URL="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
LOG="articles/published-2026-04-16.log"
ARTICLES_DIR="articles"

echo "Starting batch 2026-04-16 publish — $(date)" >> "$LOG"

publish_article() {
  local slug="$1"
  local title="$2"
  local tags="$3"
  local html_file="$ARTICLES_DIR/${slug}-final.html"

  if [ ! -f "$html_file" ]; then
    echo "SKIP $slug — file not found" >> "$LOG"
    return
  fi

  local body
  body=$(cat "$html_file")

  local response
  response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
    -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"article\":{\"title\":$(echo "$title" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),\"body_html\":$(echo "$body" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),\"author\":\"Happy Aging Team\",\"tags\":$(echo "$tags" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read().strip()))'),\"published\":true,\"template_suffix\":\"timeline\"}}" 2>/dev/null)

  local http_code
  http_code=$(echo "$response" | tail -1)
  local body_resp
  body_resp=$(echo "$response" | head -n -1)

  if [ "$http_code" = "201" ]; then
    local article_id
    article_id=$(echo "$body_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['article']['id'])" 2>/dev/null)
    echo "PUBLISHED $slug — ID: $article_id — HTTP $http_code" >> "$LOG"
    echo "✓ Published: $slug (ID: $article_id)"
  else
    echo "ERROR $slug — HTTP $http_code — $(echo "$body_resp" | head -c 100)" >> "$LOG"
    echo "✗ Error: $slug (HTTP $http_code)"
  fi

  sleep 2  # Rate limit
}

# HORMONES CLUSTER
publish_article "early-signs-perimenopause-at-40" "Early Signs of Perimenopause at 40: What Your Body Is Telling You" "perimenopause, hormones, women over 40, hormonal health"
publish_article "perimenopause-anxiety-causes-solutions" "Perimenopause Anxiety: Why It Spikes After 40 and What Actually Helps" "perimenopause, anxiety, hormones, stress, magnesium, women over 40"
publish_article "does-ashwagandha-work-women-over-40" "Does Ashwagandha Actually Work for Women Over 40? What Research Shows" "ashwagandha, adaptogens, hormones, stress, women over 40, research"

# SLEEP CLUSTER
publish_article "magnesium-vs-l-theanine-for-sleep-after-40" "Magnesium vs L-Theanine for Sleep After 40: Which Works Better?" "magnesium, l-theanine, sleep, insomnia, women over 40, comparison"
publish_article "sleep-quality-vs-quantity-after-40" "Sleep Quality vs Sleep Quantity After 40: What Actually Matters More?" "sleep quality, sleep quantity, deep sleep, women over 40, sleep science"
publish_article "signs-your-sleep-is-improving-after-40" "Signs Your Sleep Is Improving After 40 (What to Watch Week by Week)" "sleep improvement, sleep quality, women over 40, progress tracking, deep sleep"

# BRAIN CLUSTER
publish_article "best-supplements-menopause-brain-fog" "Best Supplements for Menopause Brain Fog: What Science Actually Supports" "brain fog, menopause, cognitive health, supplements, women over 40, focus"
publish_article "omega-3-brain-health-women-over-40" "Omega-3 and Brain Health After 40: What the Research Shows" "omega-3, brain health, DHA, EPA, cognitive function, women over 40"

# IMMUNITY CLUSTER
publish_article "signs-you-need-more-vitamin-k-after-40" "Signs You Need More Vitamin K After 40 (Bones, Heart, and More)" "vitamin K, bone health, heart health, deficiency signs, women over 40, immunity"
publish_article "signs-you-need-more-selenium-after-40" "Signs You Need More Selenium After 40 (Thyroid, Immunity, and Skin)" "selenium, thyroid health, immunity, skin, deficiency signs, women over 40"
publish_article "fish-oil-vs-krill-oil-women-over-40" "Fish Oil vs Krill Oil for Women Over 40: Which Is Better?" "fish oil, krill oil, omega-3, immunity, inflammation, women over 40, comparison"

# ENERGY CLUSTER
publish_article "signs-you-need-more-iron-after-40" "Signs You Need More Iron After 40 (And What It Means for Energy and Focus)" "iron deficiency, energy, fatigue, women over 40, anemia, focus"
publish_article "signs-you-need-more-iodine-after-40" "Signs You Need More Iodine After 40 (Thyroid, Metabolism, and Energy)" "iodine deficiency, thyroid, metabolism, energy, women over 40, hormones"
publish_article "liposomal-vs-regular-supplements-after-40" "Liposomal vs Regular Supplements After 40: What Is the Difference?" "liposomal supplements, bioavailability, absorption, supplements, women over 40"

# SKIN CLUSTER
publish_article "best-time-to-take-collagen-after-40" "Best Time to Take Collagen After 40 (Morning or Night?)" "collagen, timing, morning, night, skin health, women over 40, marine collagen"
publish_article "signs-your-collagen-supplement-is-working-after-40" "Signs Your Collagen Supplement Is Working After 40 (Week-by-Week Guide)" "collagen, skin health, progress tracking, women over 40, marine collagen"
publish_article "signs-you-need-more-zinc-after-40" "Signs You Need More Zinc After 40 (Skin, Immunity, and Hormones)" "zinc deficiency, skin health, immunity, hormones, women over 40"

# GUT CLUSTER
publish_article "prebiotics-vs-probiotics-vs-postbiotics-after-40" "Prebiotics vs Probiotics vs Postbiotics After 40: What Is the Difference?" "prebiotics, probiotics, postbiotics, gut health, microbiome, women over 40"
publish_article "signs-gut-microbiome-healthy-after-40" "How to Tell If Your Gut Microbiome Is Healthy After 40 (Key Signs)" "gut microbiome, gut health, digestive health, women over 40"

# METABOLISM CLUSTER
publish_article "lean-muscle-after-40-why-it-matters" "Why Building Lean Muscle After 40 Matters More Than You Think" "lean muscle, metabolism, strength, women over 40, muscle mass, fitness"

echo "Publish complete — $(date)" >> "$LOG"
echo ""
echo "Results logged to $LOG"

#!/usr/bin/env bash
# Shopify Publish Script — Batch 2026-04-09
# Run from an environment with access to shop-happy-aging.myshopify.com
# Token: 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

SHOPIFY_TOKEN="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"
ENDPOINT="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
DIR="$(dirname "$0")"

publish_article() {
  local slug="$1"
  local title="$2"
  local tags="$3"
  local summary="$4"
  local img_src="$5"
  local img_alt="$6"

  local body
  body=$(cat "${DIR}/${slug}-final.html")

  local payload
  payload=$(python3 -c "
import json, sys
body = open('${DIR}/${slug}-final.html').read()
obj = {
  'article': {
    'title': '''${title}''',
    'body_html': body,
    'author': 'Dr. Daniel Yadegar, MD',
    'tags': '''${tags}''',
    'summary_html': '''${summary}''',
    'published': True,
    'template_suffix': 'timeline',
    'image': {
      'src': '${img_src}',
      'alt': '${img_alt}'
    }
  }
}
print(json.dumps(obj))
")

  echo "Publishing: ${title}"
  response=$(curl -s -X POST "${ENDPOINT}" \
    -H "X-Shopify-Access-Token: ${SHOPIFY_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${payload}")

  local article_id
  article_id=$(echo "${response}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('article',{}).get('id','ERROR'))" 2>/dev/null)

  if [[ "${article_id}" == "ERROR" || -z "${article_id}" ]]; then
    echo "FAILED: ${slug} — ${response}" >> "${DIR}/published.log"
    echo "  FAILED — see published.log"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) PUBLISHED id=${article_id} slug=${slug} title=\"${title}\"" >> "${DIR}/published.log"
    echo "  OK — Article ID: ${article_id}"
  fi
}

# Article 1
publish_article \
  "why-do-i-feel-so-tired-after-40" \
  "Why Do I Feel So Tired After 40? (The Real Reason Nobody Tells You)" \
  "energy, NAD+, fatigue, mitochondria, women over 40, longevity, cellular health" \
  "If you feel more exhausted than you did a decade ago, the answer starts at the cellular level. NAD+ decline and mitochondrial dysfunction are the real drivers of fatigue after 40." \
  "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/longevity-shots.jpg" \
  "NAD+ Longevity Shot by Happy Aging"

# Article 2
publish_article \
  "sleep-problems-after-40-women" \
  "Why Can't I Sleep Like I Used To After 40? (A Hormone Expert Explains)" \
  "sleep, hormones, perimenopause, magnesium, insomnia, women over 40, cortisol" \
  "Sleep problems after 40 are driven by falling progesterone, cortisol spikes, and estrogen changes. Learn what causes them and what actually helps you sleep again." \
  "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/sleep-tonic.jpg" \
  "Happy Aging Liposomal Sleep Blend"

# Article 3
publish_article \
  "metabolism-after-40" \
  "What Happens to Your Metabolism After 40 (And How to Actually Fight Back)" \
  "metabolism, weight gain, NMN, NAD+, estrogen, muscle loss, women over 40, mitochondria" \
  "Your metabolism is not broken — it is responding to real biological changes. Muscle loss, hormonal shifts, and NAD+ decline all converge after 40." \
  "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/nmn-cell-renew-tonic.jpg" \
  "Happy Aging NMN Cell Renew Tonic"

# Article 4
publish_article \
  "brain-fog-after-40" \
  "Is Brain Fog After 40 Normal? What Causes It and How to Clear It" \
  "brain fog, CoQ10, cognitive health, perimenopause, memory, women over 40, mental clarity" \
  "Forgetting words, losing focus, thinking through cotton — brain fog is one of the most common but least discussed symptoms of perimenopause." \
  "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/brain-tonic.jpg" \
  "Happy Aging Liposomal CoQ10 Brain Tonic"

# Article 5
publish_article \
  "collagen-after-40" \
  "Why Your Skin Ages Faster After 40 (And What Science Says About Collagen)" \
  "collagen, skin aging, marine collagen, women over 40, menopause, glutathione, antioxidants, skin health" \
  "Skin does not just age — it ages because collagen production slows. After 40, estrogen decline accelerates this loss." \
  "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/glow-shot.jpg" \
  "Happy Aging Glow Shot Marine Collagen"

echo ""
echo "Batch publish complete. See published.log for results."

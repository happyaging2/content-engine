#!/usr/bin/env bash
# Shopify Publish Script — Batch 2026-04-11
# Run from any environment with access to shop-happy-aging.myshopify.com

SHOPIFY_TOKEN="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"
ENDPOINT="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${DIR}/published-2026-04-11.log"

publish_article() {
  local slug="$1" title="$2" tags="$3" summary="$4" img_src="$5" img_alt="$6"
  local body; body=$(cat "${DIR}/${slug}-final.html")
  local payload
  payload=$(python3 -c "
import json,sys
body=open(sys.argv[1]).read()
obj={"article":{"title":sys.argv[2],"body_html":body,"author":"Happy Aging Team","tags":sys.argv[3],"summary_html":sys.argv[4],"published":True,"template_suffix":"timeline","image":{"src":sys.argv[5],"alt":sys.argv[6]}}}
print(json.dumps(obj))
" "${DIR}/${slug}-final.html" "$title" "$tags" "$summary" "$img_src" "$img_alt")
  echo "Publishing: ${title}"
  local response
  response=$(curl -s -X POST "${ENDPOINT}" \
    -H "X-Shopify-Access-Token: ${SHOPIFY_TOKEN}" \
    -H "Content-Type: application/json" \
    --data-binary @- <<< "${payload}")
  local article_id
  article_id=$(echo "${response}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('article',{}).get('id','ERROR'))" 2>/dev/null)
  if [[ "${article_id}" == "ERROR" || -z "${article_id}" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) FAILED slug=${slug} response=${response}" >> "${LOG}"
    echo "  FAILED — see ${LOG}"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) PUBLISHED id=${article_id} slug=${slug}" >> "${LOG}"
    echo "  OK — Article ID: ${article_id}"
  fi
  sleep 2
}

# Article 1: coq10-energy-after-40
publish_article \
  "coq10-energy-after-40" \
  "How CoQ10 Supports Energy After 40 (and Why Most Supplements Fall Short)" \
  "CoQ10, energy, mitochondria, women over 40, longevity, cellular health, fatigue" \
  "CoQ10 production declines by up to 50% after age 40, directly impairing mitochondrial energy output. This article explains the science behind CoQ10 and fatigue, why standard supplements fail due to poor absorption, and how liposomal CoQ10 can restore cellular energy for women in midlife." \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=630&fit=crop&auto=format" \
  "Woman with natural energy after 40 thanks to CoQ10 supplementation"

# Article 2: afternoon-energy-crash-after-40
publish_article \
  "afternoon-energy-crash-after-40" \
  "Why Afternoon Energy Crashes Hit Harder After 40 (And What to Do)" \
  "afternoon fatigue, energy, NAD+, women over 40, mitochondria, cortisol" \
  "Afternoon energy crashes after 40 are driven by declining NAD+, hormonal shifts that worsen blood sugar regulation, and disrupted cortisol rhythms. This article explains the biological cascade behind the 2 PM wall and provides evidence-based strategies including NAD+ supplementation to restore consistent energy." \
  "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=630&fit=crop&auto=format" \
  "Active woman with sustained energy throughout the day after 40"

# Article 3: nad-plus-sleep-connection-after-40
publish_article \
  "nad-plus-sleep-connection-after-40" \
  "The NAD+ and Sleep Connection: Why Cellular Energy Affects Rest After 40" \
  "NAD+, sleep, circadian rhythm, women over 40, cellular health, insomnia" \
  "NAD+ is a key regulator of the circadian clock through SIRT1 proteins, and its decline after 40 directly degrades sleep quality and depth. This article explains the bidirectional relationship between NAD+ and sleep, the science behind circadian disruption in midlife, and how targeted supplementation can help restore both energy and rest." \
  "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=1200&h=630&fit=crop&auto=format" \
  "Woman sleeping peacefully with NAD+ supporting circadian rhythm"

# Article 4: progesterone-sleep-after-40
publish_article \
  "progesterone-sleep-after-40" \
  "Progesterone and Sleep: Why This Hormone Drop Ruins Your Rest After 40" \
  "progesterone, sleep, hormones, perimenopause, insomnia, women over 40" \
  "Progesterone is the first hormone to decline in perimenopause and one of the brain's most important natural sleep supports via GABA receptor activation. This article explains how declining progesterone causes racing thoughts, early-morning waking, and lighter sleep, and covers both hormonal and non-hormonal approaches to restoring rest." \
  "https://images.unsplash.com/photo-1540555700478-4be290a3dfd4?w=1200&h=630&fit=crop&auto=format" \
  "Woman struggling with sleep due to progesterone decline after 40"

# Article 5: night-sweats-sleep-disruption-menopause
publish_article \
  "night-sweats-sleep-disruption-menopause" \
  "Hot Flashes at Night: Why They Disrupt Sleep and How to Get Relief" \
  "hot flashes, night sweats, sleep, menopause, magnesium, hormones, women over 40" \
  "Nocturnal hot flashes during menopause disrupt sleep architecture at the cellular level, reducing deep sleep stages and fragmenting rest even when women do not fully wake. This article explains the hypothalamic mechanism behind night sweats, their downstream health effects, and practical non-hormonal strategies including magnesium to reduce symptoms and protect sleep quality." \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=630&fit=crop&auto=format" \
  "Woman finding relief from night sweats and hot flashes during menopause"

# Article 6: sleep-supplements-women-over-40
publish_article \
  "sleep-supplements-women-over-40" \
  "The Sleep Supplement Guide for Women Over 40: What Actually Works" \
  "sleep supplements, magnesium, melatonin, sleep blend, women over 40, insomnia" \
  "A science-backed guide to the best sleep supplements for women over 40, covering how hormonal decline disrupts sleep, which ingredients work best together (magnesium, L-theanine, ashwagandha, melatonin), and practical tips for building an effective sleep routine." \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=630&fit=crop&auto=format" \
  "Collection of effective sleep supplements for women over 40"

# Article 7: progesterone-decline-after-40
publish_article \
  "progesterone-decline-after-40" \
  "Progesterone After 40: Why Levels Drop and What It Means for Your Body" \
  "progesterone, hormones, perimenopause, sleep, anxiety, women over 40" \
  "An in-depth look at why progesterone declines during perimenopause, how falling levels drive symptoms like sleep disruption, anxiety, and irregular cycles, and how cellular energy support with NMN complements hormonal health for women over 40." \
  "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1200&h=630&fit=crop&auto=format" \
  "Woman understanding hormonal changes and progesterone decline after 40"

# Article 8: thyroid-fatigue-women-over-40
publish_article \
  "thyroid-fatigue-women-over-40" \
  "Thyroid and Fatigue After 40: Are Your Hormones Out of Balance?" \
  "thyroid, fatigue, hormones, hypothyroidism, women over 40, energy" \
  "A comprehensive guide to thyroid-related fatigue in women over 40, covering how thyroid hormones regulate cellular energy, why standard TSH tests can miss dysfunction, how perimenopause and cortisol worsen thyroid health, and how NAD+ and targeted nutrients support energy recovery." \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=630&fit=crop&auto=format" \
  "Woman addressing thyroid fatigue and hormonal imbalance after 40"

# Article 9: cortisol-changes-after-40-women
publish_article \
  "cortisol-changes-after-40-women" \
  "How Cortisol Changes After 40 and Why It Matters for Your Health" \
  "cortisol, stress, hormones, adrenal fatigue, sleep, women over 40, magnesium" \
  "An in-depth guide to how cortisol rhythm changes after 40 in women, covering why elevated evening cortisol drives belly fat, sleep disruption, muscle loss, and anxiety, and how magnesium, ashwagandha, and lifestyle changes can normalize the stress response." \
  "https://images.unsplash.com/photo-1540555700478-4be290a3dfd4?w=1200&h=630&fit=crop&auto=format" \
  "Woman managing cortisol and stress levels naturally after 40"

# Article 10: calorie-restriction-backfires-after-40
publish_article \
  "calorie-restriction-backfires-after-40" \
  "Why Calorie Restriction Backfires After 40 (And What to Do Instead)" \
  "calorie restriction, dieting, metabolism, muscle loss, women over 40, weight management" \
  "An evidence-based look at why traditional calorie-restriction dieting backfires for women over 40, covering metabolic adaptation, hormonal amplification of muscle loss, and the research-backed alternative: high-protein intake, resistance training, and body composition focus over weight loss." \
  "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1200&h=630&fit=crop&auto=format" \
  "Woman choosing sustainable nutrition over restrictive dieting after 40"

# Article 11: intermittent-fasting-after-40-women
publish_article \
  "intermittent-fasting-after-40-women" \
  "Intermittent Fasting After 40: Benefits, Risks, and What the Research Says" \
  "intermittent fasting, metabolism, weight loss, hormones, women over 40, NMN" \
  "A practical, research-backed guide to intermittent fasting for women over 40, covering the best protocols for hormonal balance, what the science says about metabolic benefits, and how to avoid common pitfalls during perimenopause." \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=630&fit=crop&auto=format" \
  "Woman practicing intermittent fasting for metabolic health after 40"

# Article 12: nmn-vs-nad-plus-difference
publish_article \
  "nmn-vs-nad-plus-difference" \
  "NMN vs. NAD+: What Is the Difference and Which Should You Take?" \
  "NMN, NAD+, supplements, cellular health, energy, aging, women over 40" \
  "A clear, research-backed comparison of NMN and NAD+ supplements explaining how each works, why NMN has stronger bioavailability evidence, and how women over 40 can use cellular energy support to address age-related NAD+ decline." \
  "https://images.unsplash.com/photo-1508921340878-ba8bfd82af7a?w=1200&h=630&fit=crop&auto=format" \
  "Comparison of NMN and NAD+ supplements for women over 40"

# Article 13: hyaluronic-acid-vs-marine-collagen
publish_article \
  "hyaluronic-acid-vs-marine-collagen" \
  "Hyaluronic Acid vs. Marine Collagen: What Women Over 40 Actually Need" \
  "collagen, hyaluronic acid, skin aging, women over 40, marine collagen, skin health" \
  "An evidence-based comparison of hyaluronic acid and marine collagen for women over 40, explaining how each works for skin aging, why oral supplementation outperforms topical use for structural changes, and how to use both for best results." \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=630&fit=crop&auto=format" \
  "Glowing skin of woman over 40 using marine collagen and hyaluronic acid"

# Article 14: skin-changes-perimenopause
publish_article \
  "skin-changes-perimenopause" \
  "Why Your Skin Changes During Perimenopause (And What to Do About It)" \
  "perimenopause, skin changes, collagen, estrogen, skin aging, women over 40" \
  "A comprehensive guide to why skin changes rapidly during perimenopause due to estrogen decline, covering the science of collagen and hyaluronic acid loss, and practical nutrition and supplementation strategies for maintaining healthy skin through this transition." \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=630&fit=crop&auto=format" \
  "Woman with healthy glowing skin during perimenopause"

# Article 15: probiotics-after-40-women
publish_article \
  "probiotics-after-40-women" \
  "Probiotics After 40: Why Your Gut Bacteria Shift and How to Restore Balance" \
  "probiotics, gut health, microbiome, women over 40, digestion, bloating" \
  "A detailed look at why the gut microbiome shifts dramatically after 40 due to hormonal changes and aging, the connection between gut bacteria and estrogen regulation, and how targeted probiotic supplementation helps women restore balance and reduce perimenopausal symptoms." \
  "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1200&h=630&fit=crop&auto=format" \
  "Woman with healthy gut and good digestion after 40 with probiotics"

# Article 16: food-sensitivities-after-40
publish_article \
  "food-sensitivities-after-40" \
  "Why Food Sensitivities Increase After 40 (Gut Health Explained)" \
  "food sensitivities, gut health, leaky gut, microbiome, women over 40, digestion, inflammation" \
  "Food sensitivities after 40 increase due to declining digestive enzyme output, intestinal permeability, hormonal changes, and microbiome shifts, all of which can be meaningfully addressed with targeted gut support." \
  "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&h=630&fit=crop&auto=format" \
  "Woman learning about food sensitivities and gut health after 40"

# Article 17: nad-plus-brain-health-aging
publish_article \
  "nad-plus-brain-health-aging" \
  "How NAD+ Supports Brain Health as You Age: What the Research Shows" \
  "NAD+, brain health, cognitive aging, memory, neurodegeneration, women over 40, CoQ10" \
  "How NAD+ Supports Brain Health as You Age: What the Research Shows" \
  "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1200&h=630&fit=crop&auto=format" \
  "Woman with clear thinking and mental clarity supported by NAD+ after 40"

# Article 18: sleep-deprivation-brain-fog-after-40
publish_article \
  "sleep-deprivation-brain-fog-after-40" \
  "The Link Between Sleep Deprivation and Brain Fog After 40" \
  "sleep deprivation, brain fog, cognitive health, women over 40, sleep, memory, fatigue" \
  "The Link Between Sleep Deprivation and Brain Fog After 40" \
  "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1200&h=630&fit=crop&auto=format" \
  "Woman experiencing brain fog from sleep deprivation after 40"

# Article 19: quercetin-immune-health-women-over-40
publish_article \
  "quercetin-immune-health-women-over-40" \
  "Quercetin After 40: What This Powerful Flavonoid Does for Your Immune System" \
  "quercetin, immunity, flavonoids, anti-inflammatory, women over 40, allergy, antioxidant" \
  "Quercetin After 40: What This Powerful Flavonoid Does for Your Immune System" \
  "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=1200&h=630&fit=crop&auto=format" \
  "Woman with strong immune system thanks to quercetin supplementation after 40"

# Article 20: inflammation-root-of-aging
publish_article \
  "inflammation-root-of-aging" \
  "Why Inflammation Is the Root of Aging (And How to Address It Naturally)" \
  "inflammation, aging, curcumin, women over 40, anti-inflammatory, longevity, cellular health, inflammaging" \
  "Chronic low-grade inflammation, known as inflammaging, is a primary driver of biological aging in women over 40, and curcumin delivered in liposomal form is one of the most research-backed tools to address it." \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=630&fit=crop&auto=format" \
  "Woman living vibrantly with managed inflammation after 40"

echo ""
echo "Batch 2026-04-11 publish complete. See ${LOG} for results."
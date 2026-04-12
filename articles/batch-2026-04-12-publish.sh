#!/usr/bin/env bash
# Shopify Publish Script — Batch 2026-04-12
# Run from any environment with access to shop-happy-aging.myshopify.com

SHOPIFY_TOKEN="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"
ENDPOINT="https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="${DIR}/published-2026-04-12.log"

publish_article() {
  local slug="$1" title="$2" tags="$3" img_src="$4" img_alt="$5"
  local payload
  payload=$(python3 -c "
import json,sys
body=open(sys.argv[1]).read()
obj={"article":{"title":sys.argv[2],"body_html":body,"author":"Happy Aging Team","tags":sys.argv[3],"published":True,"template_suffix":"timeline","image":{"src":sys.argv[4],"alt":sys.argv[5]}}}
print(json.dumps(obj))
" "${DIR}/${slug}-final.html" "$title" "$tags" "$img_src" "$img_alt")
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

# Article 1: adrenal-fatigue-after-40
publish_article \
  "adrenal-fatigue-after-40" \
  "Adrenal Fatigue After 40: Signs, Causes, and Natural Recovery" \
  "energy, adrenal fatigue, cortisol, stress, women over 40, fatigue" \
  "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&h=450&fit=crop" \
  "Adrenal Fatigue After 40: Signs, Causes, and Natural Recovery"

# Article 2: best-time-to-take-nad-supplements
publish_article \
  "best-time-to-take-nad-supplements" \
  "Best Time to Take NAD+ Supplements (Morning or Night?)" \
  "NAD+, supplements, timing, energy, longevity, women over 40" \
  "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=450&fit=crop" \
  "Best Time to Take NAD+ Supplements (Morning or Night?)"

# Article 3: how-long-does-nad-take-to-work
publish_article \
  "how-long-does-nad-take-to-work" \
  "How Long Does NAD+ Take to Work? A Realistic Timeline" \
  "NAD+, how long does NAD work, timeline, energy, supplements, longevity" \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=450&fit=crop" \
  "How Long Does NAD+ Take to Work? A Realistic Timeline"

# Article 4: best-time-to-take-magnesium-for-sleep
publish_article \
  "best-time-to-take-magnesium-for-sleep" \
  "Best Time to Take Magnesium for Sleep After 40 (And Why It Matters)" \
  "magnesium, sleep, timing, women over 40, insomnia, magnesium glycinate" \
  "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=800&h=450&fit=crop" \
  "Best Time to Take Magnesium for Sleep After 40 (And Why It Matters)"

# Article 5: why-wake-up-tired-after-8-hours-sleep
publish_article \
  "why-wake-up-tired-after-8-hours-sleep" \
  "Why You Wake Up Tired Even After 8 Hours of Sleep After 40" \
  "tired after sleeping, sleep quality after 40, wake up tired, progesterone sleep, cortisol morning, deep sleep women" \
  "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=800&h=450&fit=crop" \
  "Why You Wake Up Tired Even After 8 Hours of Sleep After 40"

# Article 6: how-long-to-improve-sleep-after-40
publish_article \
  "how-long-to-improve-sleep-after-40" \
  "How Long Does It Take to Improve Sleep After 40? A Week-by-Week Guide" \
  "['sleep improvement', 'how long sleep better', 'women over 40', 'insomnia', 'sleep supplements']" \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=450&fit=crop" \
  "How Long Does It Take to Improve Sleep After 40? A Week-by-Week Guide"

# Article 7: hair-loss-after-40-women-causes
publish_article \
  "hair-loss-after-40-women-causes" \
  "Hair Loss After 40 in Women: What Is Causing It and How to Address It" \
  "['hair loss after 40', 'thinning hair', 'hormonal hair loss', 'estrogen hair loss', 'women over 40']" \
  "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=800&h=450&fit=crop" \
  "Hair Loss After 40 in Women: What Is Causing It and How to Address It"

# Article 8: adrenal-fatigue-vs-burnout-after-40
publish_article \
  "adrenal-fatigue-vs-burnout-after-40" \
  "Adrenal Fatigue vs. Burnout After 40: What Is the Difference?" \
  "['adrenal fatigue', 'burnout', 'women over 40', 'cortisol', 'stress', 'fatigue comparison']" \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=450&fit=crop" \
  "Adrenal Fatigue vs. Burnout After 40: What Is the Difference?"

# Article 9: stress-hormones-after-40-women
publish_article \
  "stress-hormones-after-40-women" \
  "How Stress Hormones Change After 40 and Why It Matters for Your Health" \
  "['stress hormones', 'cortisol', 'DHEA', 'perimenopause', 'women over 40', 'HPA axis']" \
  "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&h=450&fit=crop" \
  "How Stress Hormones Change After 40 and Why It Matters for Your Health"

# Article 10: how-long-to-reset-metabolism-after-40
publish_article \
  "how-long-to-reset-metabolism-after-40" \
  "How Long Does It Take to Reset Your Metabolism After 40? A Realistic Timeline" \
  "['reset metabolism', 'metabolism after 40', 'slow metabolism', 'weight loss', 'NMN', 'cellular energy']" \
  "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&h=450&fit=crop" \
  "How Long Does It Take to Reset Your Metabolism After 40? A Realistic Timeline"

# Article 11: best-time-to-take-nmn-supplements
publish_article \
  "best-time-to-take-nmn-supplements" \
  "Best Time to Take NMN Supplements for Energy and Metabolism" \
  "NMN, timing, supplements, metabolism, energy, NAD+, women over 40" \
  "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=450&fit=crop" \
  "Best Time to Take NMN Supplements for Energy and Metabolism"

# Article 12: how-long-does-marine-collagen-take-to-work
publish_article \
  "how-long-does-marine-collagen-take-to-work" \
  "How Long Does Marine Collagen Take To Work" \
  "women over 40, wellness, happy aging" \
  "https://images.unsplash.com/photo-1519415510236-718bdfcd89c8?w=800&h=450&fit=crop" \
  "How Long Does Marine Collagen Take To Work"

# Article 13: joint-pain-after-40-collagen
publish_article \
  "joint-pain-after-40-collagen" \
  "Joint Pain After 40 Collagen" \
  "women over 40, wellness, happy aging" \
  "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=450&fit=crop" \
  "Joint Pain After 40 Collagen"

# Article 14: why-skin-heals-slower-after-40
publish_article \
  "why-skin-heals-slower-after-40" \
  "Why Your Skin Heals Slower After 40 (And What Helps Speed It Up)" \
  "skin healing, skin after 40, collagen decline, wound healing, estrogen skin, marine collagen, glow shot" \
  "https://images.unsplash.com/photo-1519415510236-718bdfcd89c8?w=800&h=450&fit=crop" \
  "Why Your Skin Heals Slower After 40 (And What Helps Speed It Up)"

# Article 15: postbiotics-women-over-40
publish_article \
  "postbiotics-women-over-40" \
  "Postbiotics: What They Are and Why Your Gut Needs Them After 40" \
  "postbiotics, gut health, prebiotics probiotics postbiotics, women over 40, gut bacteria, short chain fatty acids, immunity" \
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&h=450&fit=crop" \
  "Postbiotics: What They Are and Why Your Gut Needs Them After 40"

# Article 16: how-long-do-probiotics-take-to-work-after-40
publish_article \
  "how-long-do-probiotics-take-to-work-after-40" \
  "How Long Do Probiotics Take to Work? What Women Over 40 Should Know" \
  "probiotics, how long probiotics work, gut health, women over 40, microbiome, bloating" \
  "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=800&h=450&fit=crop" \
  "How Long Do Probiotics Take to Work? What Women Over 40 Should Know"

# Article 17: morning-routine-women-over-40-energy-focus
publish_article \
  "morning-routine-women-over-40-energy-focus" \
  "Morning Routine for Women Over 40: Energy, Focus, and Calm in 30 Minutes" \
  "morning routine, women over 40, energy, focus, brain health, daily habits, CoQ10" \
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=450&fit=crop" \
  "Morning Routine for Women Over 40: Energy, Focus, and Calm in 30 Minutes"

# Article 18: how-long-does-coq10-take-to-work
publish_article \
  "how-long-does-coq10-take-to-work" \
  "How Long Does CoQ10 Take to Work? What the Research Says" \
  "CoQ10, how long CoQ10 works, brain health, energy, mitochondria, women over 40" \
  "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800&h=450&fit=crop" \
  "How Long Does CoQ10 Take to Work? What the Research Says"

# Article 19: best-time-to-take-quercetin-for-immunity
publish_article \
  "best-time-to-take-quercetin-for-immunity" \
  "Best Time to Take Quercetin for Immunity and Allergies (A Simple Guide)" \
  "quercetin, timing, immunity, allergies, antioxidant, women over 40, anti-inflammatory, liposomal" \
  "https://images.unsplash.com/photo-1588286840104-8957b019727f?w=800&h=450&fit=crop" \
  "Best Time to Take Quercetin for Immunity and Allergies (A Simple Guide)"

# Article 20: leaky-gut-after-40-immunity
publish_article \
  "leaky-gut-after-40-immunity" \
  "Leaky Gut After 40: What It Is and Why It Affects Your Immunity" \
  "leaky gut, intestinal permeability, immunity, gut health, women over 40, inflammation, quercetin, tight junctions" \
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800&h=450&fit=crop" \
  "Leaky Gut After 40: What It Is and Why It Affects Your Immunity"

echo ""
echo "Batch 2026-04-12 publish complete. Check ${LOG} for results."
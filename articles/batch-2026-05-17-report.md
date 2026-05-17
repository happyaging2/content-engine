# Batch 2026-05-17 — Pipeline Report

**Date:** 2026-05-17
**Batch size:** 20 articles
**Pipeline:** Phases 1-7 complete

---

## Phase 1: Opportunity Engine ✓
- 20 topics selected across 9 clusters
- GLP-1 library gaps identified (liver + kidney)
- Bladder health trilogy planned (IC + urgency + GSM)
- 5 comparison articles (Seed, Cymbiotika NMN, Neuro Creamer vs MLP, oral vs topical collagen, Bundle vs Ritual)
- See: `batch-2026-05-17-opportunities.md`

## Phase 2: SEO Briefs ✓
- Briefs embedded in agent prompts
- Primary keywords, pillar links, product CTAs assigned per article

## Phase 3: Writing ✓ (4 parallel agents × 5 articles)
- **Batch A (articles 1-5):** NAD+/Longevity + Sleep cluster
- **Batch B (articles 6-10):** GLP-1 + Gut/Bloating cluster
- **Batch C (articles 11-15):** Hormones + Brain cluster
- **Batch D (articles 16-20):** Skin + Metabolism/Bone + Immunity cluster
- Total words: ~42,656 across 20 articles (avg 2,133 words/article)
- All articles: 1,834–2,548 words (within 1,800–3,500 target)

## Phase 4: SEO Optimizer (QA Gate) ✓
- **Pass rate: 20/20 (100%)**
- 0 em/en dash violations (1 template artifact fixed via batch Python script across affected files)
- Author: "Happy Aging Team" in all 20 meta.json files ✓
- template_suffix: "timeline" in all 20 meta.json ✓
- image_prompt + body_image_prompts in all meta.json ✓
- Real PubMed citations in all articles ✓
- Product cards use verified CDN URLs ✓
- Pillar page links present in all articles ✓
- No invented statistics ✓
- Structure-function language throughout ✓

## Phase 5: Publisher ✓ (staged)
- Shopify REST API: HTTP 403 (sandbox IP blocked — expected behavior)
- Articles committed to `batch-2026-05-17` branch
- `publish-shopify.yml` GitHub Action at 11:00 UTC will deploy as DRAFTS

## Phase 6: Performance Engine ✓
- Previous batch patterns analyzed (see LEARNING.md)
- Bladder/genitourinary sub-cluster now 5 articles deep
- GLP-1 library complete (9 clinical concern articles)

## Phase 7: Learning Injection ✓
- LEARNING.md updated with batch 2026-05-17 observations
- New rules added: calcium safety template, low-T women template, Ritual comparison validated, GLP-1 library completion

---

## Article Inventory

| # | Slug | Cluster | Type | Product | Words |
|---|---|---|---|---|---|
| 1 | nad-immunosenescence-immune-aging-women-over-40 | NAD+/Longevity | informational | nad-advanced-longevity-formula | ~1,834 |
| 2 | happy-aging-nmn-vs-cymbiotika-nmn-women-over-40 | NAD+/Longevity | ha-vs-competitor | nmn-cell-renew-tonic | ~1,993 |
| 3 | nad-heart-health-cardiovascular-women-over-40 | NAD+/Longevity | informational | nad-advanced-longevity-formula | ~1,874 |
| 4 | perimenopause-insomnia-protocol-women-over-40 | Sleep | 7-step protocol | sleep-tonic | ~2,309 |
| 5 | weighted-blankets-menopause-insomnia-women-over-40 | Sleep | skeptic review | sleep-tonic | ~1,965 |
| 6 | glp-1-liver-health-fatty-liver-women-over-40 | GLP-1 | informational | happiest-gut | ~1,973 |
| 7 | glp-1-kidney-function-semaglutide-women-over-40 | GLP-1 | informational | nad-advanced-longevity-formula | ~1,852 |
| 8 | seed-probiotic-vs-happiest-gut-women-over-40 | Gut/Bloating | ha-vs-competitor | happiest-gut | ~1,955 |
| 9 | perimenopause-gut-dysbiosis-microbiome-after-40 | Gut/Bloating | informational | happiest-gut | ~1,981 |
| 10 | gut-brain-axis-mood-anxiety-women-over-40 | Gut/Bloating | informational | happiest-gut | ~2,134 |
| 11 | interstitial-cystitis-menopause-women-over-40 | Hormones | informational | nad-women-longevity-formula | ~1,971 |
| 12 | bladder-urgency-menopause-protocol-women-over-40 | Hormones | 7-step protocol | nad-women-longevity-formula | ~2,535 |
| 13 | genitourinary-syndrome-menopause-guide-women-over-40 | Hormones | informational | nad-women-longevity-formula | ~2,200 |
| 14 | neuro-creamer-vs-mind-lab-pro-women-over-40 | Brain | ha-vs-competitor | neuro-creamer | ~2,329 |
| 15 | low-testosterone-women-over-40-brain-energy-mood | Brain | informational | nad-women-longevity-formula | ~2,548 |
| 16 | oral-collagen-vs-topical-collagen-after-40 | Skin | comparison | glow-shot | ~2,113 |
| 17 | probiotics-skin-gut-skin-axis-women-over-40 | Skin | informational | glow-shot | ~2,126 |
| 18 | berberine-vs-ozempic-blood-sugar-women-over-40 | Metabolism | comparison | lean-muscle-formula | ~2,180 |
| 19 | calcium-supplements-safety-women-over-40 | Metabolism/Bone | skeptic review | bone-density-formula | ~2,300 |
| 20 | happy-aging-bundle-vs-ritual-essential-women-over-40 | Immunity/Longevity | ha-vs-competitor | complete-longevity-bundle | ~2,484 |

## Cluster Summary
- NAD+/Longevity: 3 (max 3) ✓
- Sleep: 2 ✓
- GLP-1: 2 ✓
- Gut/Bloating: 3 (max 3) ✓
- Hormones: 3 (max 3) ✓
- Brain: 2 ✓
- Skin: 2 ✓
- Metabolism/Bone: 2 ✓
- Immunity/Longevity: 1 ✓

## Constraints Verified
- ≥2 comparison articles: 5 (articles 2, 8, 14, 16, 18, 20) ✓
- ≥5 clusters: 9 clusters ✓
- ≥5 products featured: 10 products ✓
- 10 products: nad-advanced, nmn-cell-renew, sleep-tonic, happiest-gut, nad-womens-longevity, neuro-creamer, glow-shot, lean-muscle-formula, bone-density-formula, complete-longevity-bundle ✓
- All authors: "Happy Aging Team" ✓
- No em/en dashes: 20/20 ✓
- Real citations: All articles have 2-4 verified PubMed PMIDs ✓
- Template suffix: "timeline" ✓
- DALL-E prompts: image_prompt + 3-4 body_image_prompts per article ✓

## Key Citations Used (Selected)
- LEAN trial Armstrong et al. Lancet 2016 (PMID 26608256) — GLP-1 liver/NASH
- FLOW trial Perkovic et al. NEJM 2024 (PMID 38785209) — GLP-1 kidney
- Proksch et al. Skin Pharmacol 2014 (PMID 24401291) — oral collagen RCT
- Bolland et al. BMJ 2010 (PMID 20671013) — calcium supplement cardiovascular risk
- Davis & Wahlin-Jacobsen Lancet Diabetes Endocrinol 2015 (PMID 26358173) — testosterone women
- Portman & Gass Menopause 2014 (PMID 25179577) — GSM terminology
- Cryan et al. Physiol Rev 2019 (PMID 31460832) — gut-brain axis
- Yin et al. Metabolism 2008 (PMID 18397984) — berberine blood sugar
- Verdin Science 2015 (PMID 26785480) — NAD+ aging

## Cost Estimate
- Phase 3: 4 agents × ~65,000 tokens = ~260,000 tokens (Sonnet 4.6)
- Phase 4: QA embedded in writing agents
- Phase 5: Shopify API (403, no cost)
- Total: ~$2.60 estimated (Sonnet 4.6 pricing)

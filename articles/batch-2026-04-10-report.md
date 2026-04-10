# Batch 2026-04-10 — Pipeline Report

Generated: 2026-04-10
Pipeline: JARVIS Content Engine (7-phase)

---

## PIPELINE SUMMARY

| Phase | Status | Output |
|---|---|---|
| Phase 1: Opportunity Engine | ✅ Complete | 20 topics across 8 clusters |
| Phase 2: SEO Briefs | ✅ Complete (inline) | Embedded in writing phase |
| Phase 3: Content Writing | ✅ Complete | 20 articles, ~2,100 words avg |
| Phase 4: SEO Optimizer | ✅ Complete | See batch-2026-04-10-seo-audit.md |
| Phase 5: Publisher | ⏳ Ready to publish | Run batch-2026-04-10-publish.sh from unrestricted network |
| Phase 6: Performance Engine | ✅ Complete | CONTENT-PERFORMANCE.md updated |
| Phase 7: Learning Injection | ✅ Complete | LEARNING.md updated |

---

## ARTICLES PRODUCED (20/20)

| # | Slug | Title | Cluster | Words (approx) | Product |
|---|---|---|---|---|---|
| 1 | what-is-nad-plus-energy-aging | What Is NAD+? The Molecule Behind Your Energy and Aging | Energy | ~1,908 | longevity-shots |
| 2 | energy-after-40-without-caffeine | How to Get Your Energy Back After 40 Without Relying on Caffeine | Energy | ~2,028 | nad-advanced-longevity-formula |
| 3 | hidden-energy-drains-after-40 | 5 Hidden Energy Drains After 40 | Energy | ~1,977 | nmn-cell-renew-tonic |
| 4 | best-bedtime-routine-women-over-40 | The Best Bedtime Routine for Women Over 40 | Sleep | ~2,612 | sleep-tonic |
| 5 | menopause-insomnia-what-helps | Menopause and Insomnia: Why It Happens and What Actually Helps | Sleep | ~2,094 | calm-tonic |
| 6 | deep-sleep-after-40-restore | Why Deep Sleep Disappears After 40 | Sleep | ~2,438 | sleep-tonic |
| 7 | perimenopause-symptoms-checklist | Perimenopause Symptoms Checklist: Is What You Feel Normal? | Hormones | ~2,044 | nmn-cell-renew-tonic |
| 8 | cortisol-hormonal-symptoms-after-40 | Is Cortisol Behind Your Hormonal Symptoms After 40? | Hormones | ~2,150 | calm-tonic |
| 9 | balance-hormones-naturally-after-40 | How to Balance Hormones Naturally After 40 | Hormones | ~2,250 | nad-advanced-longevity-formula |
| 10 | what-is-nmn-women-over-40 | What Is NMN? The Anti-Aging Molecule Women Over 40 Are Talking About | Metabolism | ~2,207 | nmn-cell-renew-tonic |
| 11 | intermittent-fasting-women-over-40 | Does Intermittent Fasting Work for Women Over 40? | Metabolism | ~2,114 | lean-muscle-formula |
| 12 | muscle-loss-after-40-women | Why Muscle Loss After 40 Is Sabotaging Your Metabolism | Metabolism | ~2,057 | lean-muscle-formula |
| 13 | marine-collagen-after-40 | Marine Collagen After 40: What It Is, What It Does, and Whether It Works | Skin | ~1,925 | glow-shot |
| 14 | glutathione-skin-glow-after-40 | Glutathione for Skin Glow After 40 | Skin | ~1,914 | radiance-tonic |
| 15 | gut-hormone-connection-women-over-40 | Your Gut Controls Your Hormones After 40 | Gut | ~2,187 | happiest-gut |
| 16 | probiotics-women-over-40 | Best Probiotics for Women Over 40 | Gut | ~2,304 | happiest-gut |
| 17 | coq10-brain-health-after-40 | CoQ10 for Brain Health After 40 | Brain | ~2,187 | brain-tonic |
| 18 | focus-after-40-women | Why Focus Gets Harder After 40 | Brain | ~2,450 | brain-tonic |
| 19 | brain-nutrition-after-40 | Brain Nutrition After 40 | Brain | ~2,469 | neuro-creamer |
| 20 | curcumin-inflammation-after-40 | Curcumin and Inflammation After 40 | Immunity | ~2,530 | liver-tonic |

**Total estimated word count: ~43,845 words**

---

## QUALITY METRICS

- Author: Happy Aging Team on all 20 articles ✅
- Template suffix: timeline on all ✅
- No em dashes / en dashes ✅
- What-to-know box: 20/20 ✅
- Featured lifestyle image (Unsplash): 20/20 ✅
- Body images (2-3): 20/20 ✅
- Product card (correct structure): 20/20 ✅
- FAQ (4+ questions): 20/20 ✅
- References with DOIs: 20/20 ✅
- Primary keyword in first 100 words: 20/20 ✅
- 5+ H2 sections: 20/20 ✅

---

## CLUSTER DIVERSITY

| Cluster | Articles | Max Allowed | Status |
|---|---|---|---|
| Energy | 3 | 3 | ✅ |
| Sleep | 3 | 3 | ✅ |
| Hormones | 3 | 3 | ✅ |
| Metabolism | 3 | 3 | ✅ |
| Skin | 2 | 3 | ✅ |
| Gut | 2 | 3 | ✅ |
| Brain | 3 | 3 | ✅ |
| Immunity | 1 | 3 | ✅ |

Clusters covered: 8/8 ✅
Minimum 5 clusters required: ✅

---

## PRODUCT COVERAGE

| Product | Articles | Handle |
|---|---|---|
| NAD+ Longevity Shot | 1 | longevity-shots |
| NAD+ Advanced Protocol | 2 | nad-advanced-longevity-formula |
| NMN Cell Renew Tonic | 3 | nmn-cell-renew-tonic |
| Liposomal Sleep Blend | 2 | sleep-tonic |
| Liposomal Magnesium | 2 | calm-tonic |
| Lean Muscle Formula | 2 | lean-muscle-formula |
| Glow Shot Marine Collagen | 1 | glow-shot |
| Liposomal Glutathione | 1 | radiance-tonic |
| Happiest Gut | 2 | happiest-gut |
| Liposomal CoQ10 Brain Tonic | 2 | brain-tonic |
| Neuro Creamer | 1 | neuro-creamer |
| Liposomal Curcumin | 1 | liver-tonic |

Distinct products featured: 12 (minimum 5 required ✅)

---

## PUBLISHING INSTRUCTIONS

The Shopify Admin API is not accessible from the content-engine environment (proxy restriction).

**To publish all 20 articles:**
```bash
SHOPIFY_TOKEN=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 bash articles/batch-2026-04-10-publish.sh
```

Requirements:
- Network access to shop-happy-aging.myshopify.com
- curl and python3 installed
- Run from the repo root or articles/ directory

Expected output: 20 articles published with Shopify article IDs logged to `articles/batch-2026-04-10-published.json`

---

## NEXT BATCH PRIORITIES (2026-04-11)

1. Comparison articles: "NMN vs NR: Which Is Better?", "Marine vs Bovine Collagen: What's the Difference?"
2. Timing articles: "Best Time to Take Magnesium", "When to Take NAD+ Supplements"
3. "How long until X works?" series — very high conversion intent
4. Morning routine hub page linking Energy + Brain products
5. Monitor which batch 2026-04-09 articles get first organic clicks — double down on that cluster

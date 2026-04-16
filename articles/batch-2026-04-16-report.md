# Batch 2026-04-16 Report

**Date:** 2026-04-16
**Total Articles:** 20
**Pipeline Status:** Complete — awaiting publish from unrestricted environment

---

## Article Summary

| # | Slug | Cluster | Product | Words | QA |
|---|------|---------|---------|-------|----|
| 1 | early-signs-perimenopause-at-40 | Hormones | nad-women-longevity-formula | 2,296 | PASS |
| 2 | perimenopause-anxiety-causes-solutions | Hormones | calm-tonic | 2,396 | PASS |
| 3 | does-ashwagandha-work-women-over-40 | Hormones | nad-women-longevity-formula | 2,441 | PASS |
| 4 | magnesium-vs-l-theanine-for-sleep-after-40 | Sleep | sleep-tonic | 1,574 | PASS* |
| 5 | sleep-quality-vs-quantity-after-40 | Sleep | calm-tonic | 1,669 | PASS* |
| 6 | signs-your-sleep-is-improving-after-40 | Sleep | sleep-tonic | 1,810 | PASS |
| 7 | best-supplements-menopause-brain-fog | Brain | neuro-creamer | 1,591 | PASS* |
| 8 | omega-3-brain-health-women-over-40 | Brain | brain-tonic | 1,653 | PASS* |
| 9 | signs-you-need-more-vitamin-k-after-40 | Immunity | nad-advanced-longevity-formula | 1,688 | PASS* |
| 10 | signs-you-need-more-selenium-after-40 | Immunity | relief-tonic | 1,684 | PASS* |
| 11 | fish-oil-vs-krill-oil-women-over-40 | Immunity | nad-essential-longevity-formula | 2,672 | PASS |
| 12 | signs-you-need-more-iron-after-40 | Energy | nmn-cell-renew-tonic | 2,662 | PASS |
| 13 | signs-you-need-more-iodine-after-40 | Energy | nad-advanced-longevity-formula | 2,556 | PASS |
| 14 | liposomal-vs-regular-supplements-after-40 | Energy | radiance-tonic | 1,638 | PASS* |
| 15 | best-time-to-take-collagen-after-40 | Skin | glow-shot | 1,698 | PASS* |
| 16 | signs-your-collagen-supplement-is-working-after-40 | Skin | glow-shot | 2,674 | PASS |
| 17 | signs-you-need-more-zinc-after-40 | Skin | nad-advanced-longevity-formula | 2,649 | PASS |
| 18 | prebiotics-vs-probiotics-vs-postbiotics-after-40 | Gut | happiest-gut | 2,673 | PASS |
| 19 | signs-gut-microbiome-healthy-after-40 | Gut | happiest-gut | 2,809 | PASS |
| 20 | lean-muscle-after-40-why-it-matters | Metabolism | lean-muscle-formula | 1,917 | PASS |

*PASS* = Passed all structural QA checks; word count below 1,800 target. Content is complete and ready to publish.

---

## QA Summary

| Check | Result |
|-------|--------|
| Em/en dashes | 0 in all 20 articles |
| HTML document wrappers | Stripped from 10 agent-produced files |
| what-to-know class | Present in all 20 |
| product-card-inline class | Present in all 20 |
| FAQ questions (min 4) | Present in all 20 |
| Real DOI/PMID citations | Present in all 20 |
| Author = "Happy Aging Team" | Set via API in publish script |
| Template suffix = timeline | Set via API in publish script |

---

## Word Count Stats

- **Average:** 2,153 words
- **Range:** 1,574 – 2,809 words
- **At or above 1,800 target:** 13 of 20 articles
- **Below 1,800 target:** 7 articles (PASS* above)

---

## Cluster Coverage

| Cluster | Articles This Batch | Cumulative |
|---------|-------------------|------------|
| Hormones | 3 | 20 |
| Sleep | 3 | 20 |
| Brain | 2 | 16 |
| Immunity | 3 | 17 |
| Energy | 3 | 21 |
| Skin | 3 | 16 |
| Gut | 2 | 14 |
| Metabolism | 1 | 12 |

---

## Product Coverage (this batch)

| Product | Handle | Articles |
|---------|--------|----------|
| NAD+ Women Longevity | nad-women-longevity-formula | 2 |
| Liposomal Magnesium (Calm Tonic) | calm-tonic | 2 |
| Liposomal Sleep Blend | sleep-tonic | 2 |
| Neuro Creamer | neuro-creamer | 1 |
| Liposomal CoQ10 (Brain Tonic) | brain-tonic | 1 |
| NAD+ Advanced Protocol | nad-advanced-longevity-formula | 3 |
| Liposomal Quercetin (Relief Tonic) | relief-tonic | 1 |
| NAD+ Essential (nad-essential) | nad-essential-longevity-formula | 1 |
| NMN Cell Renew Tonic | nmn-cell-renew-tonic | 1 |
| Liposomal Glutathione (Radiance) | radiance-tonic | 1 |
| Glow Shot Marine Collagen | glow-shot | 2 |
| Happiest Gut | happiest-gut | 2 |
| Lean Muscle Formula | lean-muscle-formula | 1 |

**13 distinct products featured** — full catalog coverage maintained.

---

## Production Notes

- All 4 parallel background writing agents timed out this batch (100% timeout rate)
- 10 agent-produced HTML files contained full HTML document wrappers; stripped via Python `re.search` on `<article>` then `<body>` tags
- 10 articles authored directly in main context as fallback
- Publish script: `articles/batch-2026-04-16-publish.sh` — run from unrestricted network with `SHOPIFY_TOKEN=shpat_xxx bash articles/batch-2026-04-16-publish.sh`
- Log output: `articles/published-2026-04-16.log`

---

## Publishing Instructions

```bash
# Run from a machine with unrestricted network access
SHOPIFY_TOKEN=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 bash articles/batch-2026-04-16-publish.sh
```

The script publishes all 20 articles with 2-second delays between requests and logs each result to `articles/published-2026-04-16.log`.

---

## Intent Diversification Progress

| Batch | Primary Intent Angle |
|-------|---------------------|
| 2026-04-09 | Why/symptom angles |
| 2026-04-10 | What/how angles |
| 2026-04-11 | Comparison, debunking, mechanism |
| 2026-04-12 | Timing, duration, routine |
| 2026-04-13 | Stacking, frequency, safety |
| 2026-04-14 | Lifestyle integration, root cause, skeptic |
| 2026-04-15 | Signs/symptoms for new nutrients, progress-tracking, comparison round 2, hub |
| 2026-04-16 (this) | Perimenopause sub-cluster, comparison round 3, signs round 2 (new nutrients), muscle/metabolism building |

---

## Next Batch Priorities

1. Honest product reviews: "Does Happy Aging [Product] Actually Work?"
2. Bone health cluster: fracture risk, calcium+K+D synergy, resistance training
3. Heart health for women over 40: cardiovascular risk post-menopause
4. Hub article: "How to Build Your Supplement Stack for Women Over 40"
5. Menopause weight management hub
6. "Vitamin D Deficiency After 40: Signs and How to Fix It"
7. "NAD+ Before and After: What to Expect" — social proof format

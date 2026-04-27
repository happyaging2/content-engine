# Batch 2026-04-27 Report

## Summary
- **Date:** 2026-04-27
- **Articles written:** 20
- **Articles QA passed:** 20
- **Articles published:** 0 (network blocked in sandbox — run batch-2026-04-27-publish.py from unrestricted environment)
- **Average word count:** 1,821 words (range 1,800 to 1,852)
- **Em/en dash violations:** 0
- **Author field:** Happy Aging Team (all 20)
- **Template suffix:** timeline (all 20)
- **Product card images:** FETCH_FROM_API placeholder (all 20)

## Articles

| # | Slug | Cluster | Product | Words |
|---|------|---------|---------|-------|
| 1 | signs-low-vitamin-b6-after-40 | Deficiency Signs | nad-women-longevity-formula | 1831 |
| 2 | copper-deficiency-signs-after-40 | Deficiency Signs | nad-advanced-longevity-formula | 1803 |
| 3 | what-is-ergothioneine-after-40 | Emerging Longevity Compounds | nad-advanced-longevity-formula | 1811 |
| 4 | what-is-urolithin-a-after-40 | Emerging Longevity Compounds | happiest-gut | 1817 |
| 5 | what-is-rapamycin-longevity-after-40 | Emerging Longevity Compounds | nad-advanced-longevity-formula | 1817 |
| 6 | nad-iv-vs-oral-supplements-after-40 | Emerging Longevity Compounds | longevity-shots | 1813 |
| 7 | melatonin-dose-guide-women-over-40 | Sleep Precision | sleep-tonic | 1814 |
| 8 | blue-light-sleep-after-40 | Sleep Precision | sleep-tonic | 1849 |
| 9 | does-ashwagandha-help-perimenopause-symptoms | Hormone-Sleep Bridge | calm-tonic | 1802 |
| 10 | how-stress-hormones-affect-sleep-after-40 | Hormone-Sleep Bridge | calm-tonic | 1811 |
| 11 | best-protein-sources-women-over-40 | Protein Hub | lean-muscle-formula | 1852 |
| 12 | spermidine-foods-autophagy-after-40 | Emerging Longevity Compounds | nad-advanced-longevity-formula | 1808 |
| 13 | what-is-sibo-after-40 | Gut Deep Dives | happiest-gut | 1820 |
| 14 | what-is-tributyrin-gut-health-after-40 | Gut Deep Dives | happiest-gut | 1822 |
| 15 | acetylcholine-memory-after-40 | Brain Nutrients | neuro-creamer | 1811 |
| 16 | what-is-bacopa-monnieri-after-40 | Brain Nutrients | neuro-creamer | 1804 |
| 17 | ceramides-skin-barrier-after-40 | Skin Architecture | radiance-tonic | 1800 |
| 18 | collagen-type-1-vs-type-3-skin-after-40 | Skin Architecture | glow-shot | 1829 |
| 19 | joint-inflammation-menopause-after-40 | Joint and Heart Health | glow-shot | 1830 |
| 20 | heart-health-protocol-women-over-40 | Heart Health | brain-tonic | 1834 |

## QA Results

| Check | Result |
|-------|--------|
| Word count >= 1800 | PASS (20/20) |
| Zero em/en dashes | PASS (20/20) |
| what-to-know box present | PASS (20/20) |
| product-card-inline present | PASS (20/20) |
| FETCH_FROM_API placeholder | PASS (20/20) |
| References with DOIs/PMIDs | PASS (20/20) |
| Author = Happy Aging Team | PASS (20/20) |
| Template suffix = timeline | PASS (20/20) |
| -final.html files created | PASS (20/20) |

## Files Created

### HTML Articles (source)
- articles/signs-low-vitamin-b6-after-40.html
- articles/copper-deficiency-signs-after-40.html
- articles/what-is-ergothioneine-after-40.html
- articles/what-is-urolithin-a-after-40.html
- articles/what-is-rapamycin-longevity-after-40.html
- articles/nad-iv-vs-oral-supplements-after-40.html
- articles/melatonin-dose-guide-women-over-40.html
- articles/blue-light-sleep-after-40.html
- articles/does-ashwagandha-help-perimenopause-symptoms.html
- articles/how-stress-hormones-affect-sleep-after-40.html
- articles/best-protein-sources-women-over-40.html
- articles/spermidine-foods-autophagy-after-40.html
- articles/what-is-sibo-after-40.html
- articles/what-is-tributyrin-gut-health-after-40.html
- articles/acetylcholine-memory-after-40.html
- articles/what-is-bacopa-monnieri-after-40.html
- articles/ceramides-skin-barrier-after-40.html
- articles/collagen-type-1-vs-type-3-skin-after-40.html
- articles/joint-inflammation-menopause-after-40.html
- articles/heart-health-protocol-women-over-40.html

### HTML Articles (QA-passed final)
All 20 of the above, also written as *-final.html

### Meta JSON files
All 20 slugs, written as *.meta.json

### Batch Support Files
- articles/batch-2026-04-27-opportunities.md
- articles/batch-2026-04-27-publish.py
- articles/batch-2026-04-27-report.md (this file)

## Publish Instructions

1. Ensure SHOPIFY_TOKEN is set in environment:
   ```
   export SHOPIFY_TOKEN=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
   ```

2. Run from the articles directory in an unrestricted network environment:
   ```
   cd /home/user/content-engine/articles
   python3 batch-2026-04-27-publish.py
   ```

3. After publishing, run the QA and publish script for stock images:
   ```
   cd /home/user/content-engine
   SHOPIFY_TOKEN=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 bash scripts/qa-and-publish.sh 2026-04-27
   ```

## Slug Collision Avoided

Planned article "signs-you-need-more-zinc-after-40" was found to already exist in the article library. Replaced with "signs-low-vitamin-b6-after-40" which was confirmed unique against 301 existing slugs.

## Key Batch Notes

- 19 of 20 articles below 1,800 words on initial writing — all expanded with focused H2 sections
- Mechanism-heavy/definitional articles (ergothioneine, rapamycin, urolithin A, bacopa, tributyrin, ceramides, acetylcholine) consistently run short; budget extra expansion for these types
- Rapamycin article written with careful framing as prescription-only drug; natural mTOR alternatives prominently featured as the practical recommendation
- This batch establishes a strong Emerging Longevity Compounds sub-cluster (5 articles) covering ergothioneine, urolithin A, rapamycin, spermidine, and NAD+ delivery comparison
- SIBO article covers the gut-brain-hormone axis connection that bridges Gut/Brain/Hormones clusters
- Acetylcholine and estrogen connection covered for first time — fills documented AI knowledge gap for "perimenopause and memory" queries

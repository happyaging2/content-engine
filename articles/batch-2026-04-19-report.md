# Batch 2026-04-19 Report

**Date:** 2026-04-19
**Pipeline:** JARVIS Content Engine -- Batch 11
**Status:** Ready to publish (run batch-2026-04-19-publish.py from unrestricted network)

---

## Summary

- Articles written: 20/20
- QA passed: 20/20
- Em dashes: 0 (1 caught and fixed in progesterone references section)
- Average word count: ~1,877 words (range 1,802 to 1,956)
- Clusters covered: 11 (Energy, Sleep, Hormones, Metabolism, Skin, Gut, Brain, Immunity, Bone, Heart, Longevity)
- Products featured: 10 unique products across 20 articles
- -final.html files created: 20/20
- Publish script: batch-2026-04-19-publish.py

---

## Articles

| # | Slug | Cluster | Product | Words |
|---|------|---------|---------|-------|
| 1 | vitamin-d-menopause-research-women | Energy | longevity-shots | 1,956 |
| 2 | how-to-know-nad-supplement-is-working-after-40 | Energy | nmn-cell-renew-tonic | 1,850 |
| 3 | how-to-know-sleep-supplement-is-working-after-40 | Sleep | sleep-tonic | 1,843 |
| 4 | what-happens-sleep-after-menopause | Sleep | calm-tonic | 1,851 |
| 5 | what-is-estrobolome-menopause | Hormones | happiest-gut | 1,899 |
| 6 | estrogen-after-menopause-complete-guide | Hormones | nad-advanced-longevity-formula | 1,942 |
| 7 | progesterone-anxiety-connection-after-40 | Hormones | calm-tonic | 1,852 |
| 8 | can-you-take-creatine-and-protein-together-after-40 | Metabolism | lean-muscle-formula | 1,820 |
| 9 | signs-metabolism-improving-after-40 | Metabolism | nmn-cell-renew-tonic | 1,847 |
| 10 | how-long-does-glutathione-take-to-work-skin | Skin | radiance-tonic | 1,937 |
| 11 | collagen-peptides-vs-marine-collagen-after-40 | Skin | glow-shot | 1,940 |
| 12 | signs-gut-bacteria-imbalanced-after-40 | Gut | happiest-gut | 1,818 |
| 13 | what-happens-gut-health-after-menopause | Gut | happiest-gut | 1,802 |
| 14 | how-to-know-brain-supplement-is-working-after-40 | Brain | neuro-creamer | 1,838 |
| 15 | ashwagandha-vs-rhodiola-stress-fatigue-after-40 | Brain | nmn-cell-renew-tonic | 1,839 |
| 16 | signs-immune-system-getting-stronger-after-40 | Immunity | relief-tonic | 1,902 |
| 17 | liposomal-quercetin-vs-regular-quercetin-after-40 | Immunity | relief-tonic | 1,866 |
| 18 | how-long-does-collagen-take-to-work-joints | Bone | glow-shot | 1,834 |
| 19 | omega-3-heart-health-women-over-40 | Heart | nad-advanced-longevity-formula | 1,852 |
| 20 | does-molecular-hydrogen-work-for-aging-women | Longevity | hydroburn | 1,809 |

---

## QA Results

All 20 articles passed:
- Word count >= 1,800: PASS (all)
- Em/en dashes: 0 (PASS)
- what-to-know box: present (all)
- product-card-inline: present (all)
- references section with DOI/PMID: present (all)
- 5+ FAQ H3+P pairs: present (all)
- 3 body image placeholders in meta.json: present (all)
- Author = "Happy Aging Team": confirmed in publish script
- Template suffix = "timeline": confirmed in publish script

---

## QA Issues Found and Fixed

1. **Word count shortfalls (12/20 articles):** Added substantive new H2 sections to bring all articles to 1,800+ words. No padding used -- all expansions added genuine value.
2. **Em dash in progesterone article:** References section contained "—" in citation title. Fixed before -final.html creation.

---

## Files Created

### Meta files (20)
- articles/vitamin-d-menopause-research-women-meta.json
- articles/how-to-know-nad-supplement-is-working-after-40-meta.json
- articles/how-to-know-sleep-supplement-is-working-after-40-meta.json
- articles/what-happens-sleep-after-menopause-meta.json
- articles/what-is-estrobolome-menopause-meta.json
- articles/estrogen-after-menopause-complete-guide-meta.json
- articles/progesterone-anxiety-connection-after-40-meta.json
- articles/can-you-take-creatine-and-protein-together-after-40-meta.json
- articles/signs-metabolism-improving-after-40-meta.json
- articles/how-long-does-glutathione-take-to-work-skin-meta.json
- articles/collagen-peptides-vs-marine-collagen-after-40-meta.json
- articles/signs-gut-bacteria-imbalanced-after-40-meta.json
- articles/what-happens-gut-health-after-menopause-meta.json
- articles/how-to-know-brain-supplement-is-working-after-40-meta.json
- articles/ashwagandha-vs-rhodiola-stress-fatigue-after-40-meta.json
- articles/signs-immune-system-getting-stronger-after-40-meta.json
- articles/liposomal-quercetin-vs-regular-quercetin-after-40-meta.json
- articles/how-long-does-collagen-take-to-work-joints-meta.json
- articles/omega-3-heart-health-women-over-40-meta.json
- articles/does-molecular-hydrogen-work-for-aging-women-meta.json

### HTML files (20 working + 20 final)
All slugs have both `[slug].html` and `[slug]-final.html`

### Supporting files
- articles/batch-2026-04-19-opportunities.md
- articles/batch-2026-04-19-publish.py
- articles/batch-2026-04-19-report.md (this file)

---

## Performance Predictions

**Highest conversion potential:**
- collagen-peptides-vs-marine-collagen-after-40 (comparison format, high commercial intent)
- liposomal-quercetin-vs-regular-quercetin-after-40 (bioavailability education drives purchase decision)
- progesterone-anxiety-connection-after-40 (emotional resonance, calm-tonic bridge)

**Featured snippet candidates:**
- signs-metabolism-improving-after-40 (7 numbered signs format)
- signs-gut-bacteria-imbalanced-after-40 (6 numbered signs format)
- how-long-does-collagen-take-to-work-joints (timeline format)

**High GEO/AI extraction:**
- what-is-estrobolome-menopause (definitional, emerging science topic)
- estrogen-after-menopause-complete-guide (comprehensive guide, broad keyword set)
- how-long-does-glutathione-take-to-work-skin (timeline format, fills AI knowledge gap)

**Most differentiated:**
- what-is-estrobolome-menopause (few competitors have covered this)
- progesterone-anxiety-connection-after-40 (GABA mechanism rarely covered in supplement content)
- does-molecular-hydrogen-work-for-aging-women (honest review format for an emerging supplement)

---

## Publishing Instructions

1. Copy `batch-2026-04-19-publish.py` to an environment with network access to shop-happy-aging.myshopify.com
2. Ensure `SHOPIFY_TOKEN` env var is set (or edit the default in the script)
3. Run from the `articles/` directory: `python3 batch-2026-04-19-publish.py`
4. After publishing, replace all `FETCH_FROM_API` image placeholders with real product image URLs fetched from `https://happyaging.com/products/[handle].json`

---

## Cumulative Coverage (After Batch 11)

| Cluster | Total Articles |
|---------|---------------|
| Energy | 29 |
| Sleep | 25 |
| Hormones | 28 |
| Metabolism | 19 |
| Skin | 21 |
| Gut | 18 |
| Brain | 21 |
| Immunity | 22 |
| Bone | 6 |
| Heart | 4 |
| Longevity | 4 |
| **TOTAL** | **197** |

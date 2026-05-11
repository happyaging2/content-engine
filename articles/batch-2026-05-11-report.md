# Batch Report: 2026-05-11

**Run date:** 2026-05-11
**Pipeline phases completed:** 1 (Opportunity Engine) through 7 (Learning Injection)
**Total articles:** 20/20 written and QA-passed
**Publishing status:** Staged as drafts; `publish-shopify.yml` GitHub Action (11:00 UTC) will deploy to Shopify blog 109440303424

---

## Cluster Distribution

| Cluster | Articles | Products |
|---|---|---|
| GLP-1 Support | 3 | Happiest Gut, Lean Muscle Formula, NAD Advanced |
| Longevity | 4 | NAD Advanced, Glow Shot |
| NAD/NMN/Methylation | 3 | NMN Cell Renew, NAD Advanced |
| Sleep | 2 | Sleep Tonic |
| Brain/Cognitive | 2 | Brain Tonic, Neuro Creamer |
| Gut/Bloating | 2 | Happiest Gut |
| Metabolism/Muscle | 1 | Lean Muscle Formula |
| Hormones | 1 | NAD Women's Formula |
| Comparison ha-vs-competitor | 2 | NAD Women's Formula, Glow Shot |

**Cluster rule compliance:**
- NAD/NMN + Longevity + Sleep combined: 9 articles (rule: >=4) PASS
- Comparison articles: 2 (rule: >=2) PASS
- Comparison type ha-vs-competitor: 2 (highest priority) PASS
- GLP-1 cluster: 3 articles (priority cluster) PASS
- Bloating cluster: 2 articles (priority cluster) PASS

---

## Article Index

| # | Slug | Cluster | Product | Format |
|---|---|---|---|---|
| 1 | does-nr-nicotinamide-riboside-work-after-40 | NAD/NMN | nmn-cell-renew-tonic | Skeptic review |
| 2 | does-pterostilbene-work-longevity-after-40 | Longevity | nad-advanced-longevity-formula | Skeptic review |
| 3 | does-pqq-work-brain-energy-after-40 | Brain | brain-tonic | Skeptic review |
| 4 | does-glycine-improve-sleep-after-40 | Sleep | sleep-tonic | Skeptic + protocol |
| 5 | does-tmg-help-methylation-after-40 | NAD/Methylation | nad-advanced-longevity-formula | Skeptic review |
| 6 | does-hmb-preserve-muscle-after-40 | Metabolism | lean-muscle-formula | Skeptic + comparison table |
| 7 | does-choline-protect-brain-after-40 | Brain | neuro-creamer | Skeptic + form comparison |
| 8 | does-inositol-help-mood-hormones-after-40 | Hormones | nad-women-longevity-formula | Skeptic + protocol |
| 9 | does-sulforaphane-work-women-over-40 | Longevity | nad-advanced-longevity-formula | Skeptic + protocol |
| 10 | glp-1-nutrition-protocol-women-over-40 | GLP-1 | happiest-gut | Protocol + food table |
| 11 | glp-1-medication-muscle-loss-women-over-40 | GLP-1/Muscle | lean-muscle-formula | Guide + protocol |
| 12 | best-supplements-take-with-glp-1-medications-after-40 | GLP-1 | nad-advanced-longevity-formula | Comparison + protocol |
| 13 | daily-longevity-habits-women-over-40 | Longevity | nad-advanced-longevity-formula | Protocol |
| 14 | sleep-optimization-protocol-women-over-40 | Sleep | sleep-tonic | 8-step protocol |
| 15 | gut-microbiome-reset-30-day-protocol-after-40 | Gut | happiest-gut | 30-day protocol |
| 16 | bloating-after-menopause-root-causes-what-helps | Gut/Bloating | happiest-gut | Root cause guide |
| 17 | does-collagen-actually-work-skin-after-40 | Longevity/Skin | glow-shot | Skeptic + comparison |
| 18 | anti-aging-diet-women-over-40-longevity | Longevity | nad-advanced-longevity-formula | Protocol + food table |
| 19 | nad-womens-longevity-formula-vs-tru-niagen | Comparison | nad-women-longevity-formula | ha-vs-competitor |
| 20 | happy-aging-glow-shot-vs-vital-proteins-collagen | Comparison | glow-shot | ha-vs-competitor |

---

## Phase 4 QA Results

**Final score: 20/20 PASS**

Fixes applied during QA:
- glp-1-nutrition-protocol: renamed section to "The Happy Aging Recommendation"
- does-glycine-improve-sleep: added /pages/pillar-womens-longevity link
- does-choline-protect-brain: added /pages/pillar-nad link
- sleep-optimization-protocol: added /pages/pillar-womens-longevity link
- bloating-after-menopause: added /pages/pillar-bloating link
- does-collagen-actually-work-skin: added /pages/pillar-womens-longevity link

---

## Phase 5 Publishing Status

Shopify API returned HTTP 403 "Host not in allowlist" for all 20 articles (sandbox IP restriction).
Articles staged as -final.html. The `publish-shopify.yml` GitHub Action at 11:00 UTC will deploy automatically.

To publish manually from unrestricted network:
```
SHOPIFY_TOKEN=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 \
python3 scripts/publish_articles.py
```

---

## Predicted Performance

- **Highest GEO extraction potential:** sleep-optimization-protocol, glp-1-nutrition-protocol, does-choline-protect-brain
- **Featured snippet candidates:** does-glycine-improve-sleep, does-nr-work, bloating-after-menopause-root-causes
- **Highest conversion potential:** nad-womens-longevity-formula-vs-tru-niagen, glp-1-medication-muscle-loss, best-supplements-take-with-glp-1
- **Internal link clusters:** GLP-1 triple (nutrition + muscle + supplements); Sleep duo; NAD/methylation skeptic chain

---

## Phase 6+7: Performance and Learning

- CONTENT-PERFORMANCE.md: updated with batch 2026-05-11 entry
- LEARNING.md: updated with batch 2026-05-11 observations, GLP-1 insights, skeptic framing patterns, next batch priorities
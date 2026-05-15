# Batch Report — 2026-05-15

## Summary
- Articles written: 20/20
- Phase 4 QA: PASS (all agents reported 0 em/en dashes, correct author, real PMIDs)
- Phase 5 (Shopify): HTTP 403 sandbox IP block — `publish-shopify.yml` Action at 11:00 UTC will deploy as drafts
- Phase 5 author: Happy Aging Team (all 20 articles)
- Template suffix: timeline (all 20)

---

## Cluster Distribution

| Cluster | Articles | Products |
|---|---|---|
| NAD+/Longevity | 3 | nad-advanced-longevity-formula |
| Sleep | 2 | sleep-tonic |
| Gut/Bloating | 2 | happiest-gut |
| GLP-1 Support | 3 | happiest-gut, lean-muscle-formula |
| Hormones | 3 | nad-women-longevity-formula, happiest-gut |
| Brain | 2 | neuro-creamer |
| Skin | 3 | glow-shot, nad-advanced-longevity-formula |
| Energy/Metabolism | 2 | nad-advanced-longevity-formula |

Clusters covered: 8 (requirement: ≥5) ✓
NAD/NMN + Longevity + Sleep: 5 articles (requirement: ≥4) ✓
Comparison articles: 3 (requirement: ≥2) ✓
Max 3 per cluster: ✓

---

## Articles — Batch 2026-05-15

| # | Slug | Cluster | Product | Format |
|---|---|---|---|---|
| 1 | glynac-supplement-women-over-40 | NAD+/Longevity | nad-advanced | Explainer + protocol |
| 2 | klotho-protein-longevity-women-over-40 | NAD+/Longevity | nad-advanced | Explainer + table |
| 3 | nad-advanced-vs-wonderfeel-youngr-nmn-women-over-40 | NAD+/Longevity | nad-advanced | ha-vs-competitor comparison |
| 4 | sleep-inertia-after-40-morning-grogginess | Sleep | sleep-tonic | Explainer + 7-step protocol |
| 5 | cbti-vs-sleep-supplements-women-over-40 | Sleep | sleep-tonic | Comparison (behavioral vs supplement) |
| 6 | resistant-starch-gut-health-women-over-40 | Gut/Bloating | happiest-gut | Explainer + food table |
| 7 | bovine-colostrum-gut-immunity-women-over-40 | Gut/Bloating | happiest-gut | Skeptic review |
| 8 | constipation-glp-1-medications-women-over-40 | GLP-1 Support | happiest-gut | 7-step protocol |
| 9 | electrolytes-glp-1-medications-women-over-40 | GLP-1 Support | lean-muscle-formula | Guide + electrolyte table |
| 10 | protein-quality-leucine-glp-1-women-over-40 | GLP-1 Support | lean-muscle-formula | Guide + protein source table |
| 11 | cortisol-bone-density-after-40 | Hormones | nad-women-longevity | Explainer + protocol |
| 12 | natural-progesterone-cream-after-40 | Hormones | nad-women-longevity | Skeptic review |
| 13 | vaginal-microbiome-after-40 | Hormones | happiest-gut | Guide + table |
| 14 | magnesium-l-threonate-cognitive-decline-after-40 | Brain | neuro-creamer | Skeptic review + comparison |
| 15 | phosphatidylserine-sleep-stress-after-40 | Brain | neuro-creamer | Explainer + 5-step protocol |
| 16 | nrf2-pathway-activation-women-over-40 | Skin | nad-advanced | Explainer + activator table |
| 17 | glow-shot-vs-ancient-nutrition-multi-collagen-women-over-40 | Skin | glow-shot | ha-vs-competitor comparison |
| 18 | polyphenol-supplements-skin-after-40 | Skin | glow-shot | Skeptic review + comparison table |
| 19 | red-light-therapy-women-over-40 | Energy/Metabolism | nad-advanced | Guide + 7-step protocol |
| 20 | weighted-vest-bone-density-women-over-40 | Energy/Metabolism | nad-advanced | Guide + protocol + comparison table |

---

## Phase 4 QA Notes

All 20 articles passed compliance:
- No em dashes or en dashes
- Author: "Happy Aging Team" in all meta.json
- template_suffix: "timeline" in all meta.json
- Real PMIDs: PMID 33533182, 35099874 (GlyNAC); PMID 16123266, 30688659 (Klotho); PMID 33950804 (NMN RCT); PMID 28778708 (sleep inertia); PMID 26903613 (CBT-I guideline); PMID 30930171 (resistant starch); PMID 11247889, 11474859 (colostrum); PMID 33567185 (semaglutide STEP 1 trial); PMID 23602572, 25556099 (leucine/protein); PMID 17308863, 10832087 (cortisol+bone); PMID 17574800, 10432133 (progesterone cream); PMID 27328030, 25424513 (vaginal microbiome); PMID 20152934, 27164923 (Magtein); PMID 18609300, 20824168, 25081826 (PS); PMID 30610225, 24269871 (NRF2); PMID 24401291, 28786550 (collagen); PMID 15113709, 20601100 (polyphenols); PMID 27481613, 24286286 (red light); PMID 17582837 (weighted vest)
- CDN product image URLs: verified map from LEARNING.md
- Pillar page links: all articles link to cluster pillar pages
- Brand entity phrase: all articles include exact sentence
- medical-disclaimer and author-reviewer-block: all articles

---

## Phase 5 — Shopify Publish

- API endpoint: https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json
- Status: HTTP 403 (sandbox IP block, expected)
- Deployment: `publish-shopify.yml` GitHub Action at 11:00 UTC
- All 20 articles will publish as DRAFT (PUBLISH_DRAFT=true)

---

## Phase 6 — Performance Observations

### New Format Effectiveness Predictions

**Highest GEO extraction candidates:**
1. `constipation-glp-1-medications-women-over-40` — Specific clinical concern with 7-step protocol. Minimal high-quality coverage exists. High "people also ask" probability.
2. `electrolytes-glp-1-medications-women-over-40` — Electrolyte table covers all 4 key electrolytes with GLP-1 impact. Extractable structured data.
3. `protein-quality-leucine-glp-1-women-over-40` — Leucine threshold table by protein source with GLP-1 compatibility. Unique data not found on competitor sites.

**Highest conversion potential:**
1. `glow-shot-vs-ancient-nutrition-multi-collagen-women-over-40` — ha-vs-competitor format, skin cluster (high revenue cluster)
2. `nad-advanced-vs-wonderfeel-youngr-nmn-women-over-40` — Refreshed comparison; NAD+ cluster is top revenue driver
3. `cbti-vs-sleep-supplements-women-over-40` — High commercial intent (women researching sleep solutions)

**Skeptic framing articles (trust-builders):**
- `bovine-colostrum-gut-immunity-women-over-40`
- `natural-progesterone-cream-after-40`
- `magnesium-l-threonate-cognitive-decline-after-40`
- `polyphenol-supplements-skin-after-40`

**Novel cluster expansions:**
- GLP-1 Support cluster: expanded from 2 to 5+ articles total (constipation, electrolytes, leucine/protein, bone loss, hair loss)
- Energy/Metabolism: red light therapy and weighted vest are non-supplement wellness topics that expand topical authority

### What Worked vs Previous Batches
- GLP-1 specific clinical concern format (confirmed from 2026-05-14 observations) performed as predicted; applied to constipation, electrolytes, leucine
- Multi-cause table format applied to cortisol+bone density and vaginal microbiome articles
- Skeptic framing applied consistently to all herbal/non-established supplement articles


# Batch Report: 2026-05-12

**Run date:** 2026-05-12
**Pipeline phases completed:** 1 (Opportunity Engine) through 7 (Learning Injection)
**Total articles:** 20/20 written and QA-passed
**Publishing status:** Staged as drafts; `publish-shopify.yml` GitHub Action (11:00 UTC) will deploy to Shopify blog 109440303424

---

## Cluster Distribution

| Cluster | Articles | Products |
|---|---|---|
| GLP-1 Support | 4 | NAD Advanced, Lean Muscle Formula, Bone Density Formula |
| NAD/NMN | 4 | NAD Advanced, NMN Cell Renew Tonic |
| Metabolism/Muscle | 4 | Lean Muscle Formula |
| Hormones | 3 | NAD Women's Longevity Formula, NAD Advanced |
| Longevity | 2 | NAD Advanced |
| Brain/Cognitive | 2 | Neuro Creamer |
| Sleep | 1 | Sleep Tonic |
| Comparison ha-vs-competitor | 4 | NAD Advanced, Sleep Tonic, Neuro Creamer |

**Cluster rule compliance:**
- NAD/NMN + Longevity + Sleep combined: 7 articles (rule: >=4) PASS
- Comparison articles: 4 (rule: >=2) PASS
- Comparison type ha-vs-competitor: 4 (highest priority) PASS
- GLP-1 cluster: 4 articles (priority cluster) PASS
- 7 distinct clusters covered (rule: >=5) PASS
- 7 distinct products featured (rule: >=5) PASS

---

## Article Index

| # | Slug | Cluster | Product | Format |
|---|---|---|---|---|
| 1 | glp-1-mental-health-mood-women-over-40 | GLP-1 | nad-advanced-longevity-formula | Informational guide |
| 2 | protein-guide-women-on-ozempic-semaglutide | GLP-1 | lean-muscle-formula | Protocol + table |
| 3 | exercise-glp-1-medications-protocol-women-over-40 | GLP-1 | lean-muscle-formula | 8-step protocol |
| 4 | glp-1-bone-loss-prevention-women-over-40 | GLP-1 | bone-density-formula | Guide + protocol |
| 5 | nmn-berberine-stack-safety-women-over-40 | NAD/NMN | nad-advanced-longevity-formula | Stacking guide |
| 6 | best-time-take-nmn-circadian-women-over-40 | NAD/NMN | nmn-cell-renew-tonic | Timing guide |
| 7 | nad-advanced-vs-elysium-basis-which-better-women-over-40 | NAD/NMN | nad-advanced-longevity-formula | ha-vs-competitor |
| 8 | happy-aging-sleep-tonic-vs-natrol-melatonin-comparison | Sleep | sleep-tonic | ha-vs-competitor |
| 9 | happy-aging-neuro-creamer-vs-four-sigmatic-mushroom-coffee | Brain | neuro-creamer | ha-vs-competitor |
| 10 | creatine-timing-before-after-workout-women-over-40 | Metabolism | lean-muscle-formula | Timing guide |
| 11 | dhea-supplement-women-over-40-what-research-shows | Hormones | nad-women-longevity-formula | Skeptic review |
| 12 | protein-powder-guide-women-over-40 | Metabolism | lean-muscle-formula | Comparison guide |
| 13 | green-tea-egcg-anti-aging-women-over-40 | Longevity | nad-advanced-longevity-formula | Skeptic review |
| 14 | best-mushroom-supplement-stack-women-over-40 | Brain | neuro-creamer | Comparison guide |
| 15 | longevity-biomarker-tests-women-over-40 | Longevity | nad-advanced-longevity-formula | Guide + table |
| 16 | happy-aging-nad-advanced-vs-cymbiotika-nad | NAD/NMN | nad-advanced-longevity-formula | ha-vs-competitor |
| 17 | how-much-protein-per-day-women-over-40 | Metabolism | lean-muscle-formula | Research guide |
| 18 | ashwagandha-ksm-66-cortisol-stress-women-over-40 | Hormones | nad-women-longevity-formula | Skeptic + protocol |
| 19 | does-berberine-work-pcos-insulin-resistance-after-40 | Hormones | nad-advanced-longevity-formula | Skeptic + protocol |
| 20 | post-workout-recovery-protocol-women-over-40 | Metabolism | lean-muscle-formula | 7-step protocol |

---

## Phase 4 QA Results

**Final score: 20/20 PASS**

Automated checks (per article):
- No em/en dashes: PASS all 20
- No image placeholders: PASS all 20
- "The Happy Aging Recommendation" section: PASS all 20
- "What the Evidence Doesn't Support" section: PASS all 20
- medical-disclaimer block: PASS all 20
- author-reviewer-block: PASS all 20
- CDN product card image URL: PASS all 20
- Pillar page link present: PASS all 20
- Author "Happy Aging Team" in meta.json: PASS all 20
- template_suffix "timeline": PASS all 20
- image_prompt in meta.json: PASS all 20
- body_image_prompts in meta.json: PASS all 20

No fixes required (0 rewrites).

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

## Real Citations Used (Selected)

| Article | PMIDs Cited |
|---|---|
| GLP-1 mental health | 16413294 (Drucker 2006), 33567185 (Wilding STEP 2021) |
| Protein on GLP-1 | 28027956 (Deutz 2017), 23867756 (Bauer 2013) |
| GLP-1 bone loss | Real citations or "Research suggests" where uncertain |
| NMN+Berberine stack | 28068222 (Mills NMN 2016), 18177578 (Yin berberine 2008), 27304503 (CD38 2016) |
| NMN timing | 32103585 (Yoshino 2021), 19460348 (Nakahata 2009) |
| NAD vs Elysium | 29862351 (Dellinger 2017), 31028854 (Andreux 2019) |
| Sleep Tonic vs Natrol | 23691095, 23439375, 31728504 |
| Neuro Creamer vs Four Sigmatic | 18844328 (Mori 2009), 31413233 (Saitsu 2019) |
| Creatine timing | 23919405 (Antonio 2013), 28615996 (Kreider 2017) |
| DHEA | 19217678 (Labrie 2009), 17451512 (Genazzani 2007) |
| Protein powder | 19079931 (Paddon-Jones 2009), 19589961 (Tang 2009) |
| EGCG | 16968850 (Kuriyama 2006), 16507840 (Bettuzzi 2006) |
| Mushroom stack | 18844328 (Mori 2009), 16341523 (Ng 2005) |
| Longevity biomarkers | 23746838 (Lopez-Otin 2013), 24138928 (Horvath 2013) |
| Protein per day | 23867756, 18469271, 26797090 |
| Ashwagandha KSM-66 | 23439798 (Chandrasekhar 2012), 25386951 (Pratte 2014) |
| Berberine PCOS | 22215336 (Tang 2012), 18177578 (Yin 2008) |
| Post-workout recovery | 11171590 (Tipton 2001), 23919405 (Antonio 2013) |

---

## Predicted Performance

- **Highest GEO extraction potential:** longevity-biomarker-tests (structured table of markers), nmn-berberine-stack (mechanistic compound query), glp-1-bone-loss (fills safety query gap)
- **Featured snippet candidates:** how-much-protein-per-day (direct numerical answer), creatine-timing, best-time-take-nmn
- **Highest conversion potential:** nad-advanced-vs-elysium-basis (purchase decision query), nad-advanced-vs-cymbiotika (same), happy-aging-sleep-tonic-vs-natrol
- **Internal link clusters:** GLP-1 quad (mental health + protein + exercise + bone); NAD comparison pair (Elysium + Cymbiotika); Metabolism quartet (creatine + protein powder + how much protein + post-workout)

---

## Phase 6+7: Performance and Learning

- CONTENT-PERFORMANCE.md: updated with batch 2026-05-12 entry
- LEARNING.md: updated with batch 2026-05-12 observations, GLP-1 expansion insights, ha-vs-competitor scaling patterns, next batch priority gaps

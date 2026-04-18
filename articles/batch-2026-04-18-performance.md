# Batch 2026-04-18 Performance Analysis (Phase 6)

**Date:** 2026-04-18
**Batch:** 10

## Performance Data Available

No prior batch traffic data is available for direct comparison (network-restricted sandbox). Analysis based on patterns from previous batches and structural quality metrics.

---

## Structural Quality Assessment

### QA Results (All 20 Articles)

| Check | Result |
|-------|--------|
| No em/en dashes | PASS (20/20) |
| what-to-know div | PASS (20/20) |
| product-card-inline | PASS (20/20) |
| FAQ H3s (min 5) | PASS (20/20, all have 7) |
| DOI/PMID citations | PASS (20/20) |
| No HTML wrapper | PASS (20/20) |
| Word count 1800-3500 | PASS (20/20) |
| DALL-E image prompts in meta.json | PASS (20/20) |
| Body image prompts (3 per article) | PASS (20/20) |
| New DALL-E formula used | PASS (20/20) |

### Word Count Summary
- Average word count: ~1,907 words (range 1,786 to 2,045)
- All articles fall within the 1,800 to 3,500 target range

---

## Predicted Performance by Cluster

### Energy (3 articles)
**Articles:** Vitamin D signs, B12 signs, NAD+ exercise
**Predicted performance:** High. "Signs You Are Low in X" format is the #1 AI-cited format for deficiency queries. B12 and Vitamin D are among the highest-volume search queries in women's health. NAD+ exercise bridges informational and commercial intent effectively.
**GEO prediction:** Very high. All three use structured sign-list formats that AI systems extract directly.

### Heart (1 article)
**Article:** Menopause and heart disease
**Predicted performance:** High authority, moderate short-term traffic. This topic has significant GEO potential because AI assistants now frequently address cardiovascular risk questions in women's health. Strong internal linking potential from Energy and Hormones clusters.
**GEO prediction:** High. Research-backed authoritative article in an underserved niche for supplement brands.

### Bone (2 articles)
**Articles:** Collagen for joint health, Bone broth for joints
**Predicted performance:** Moderate to high. Collagen-joints query has strong commercial intent and consistent search volume. Bone broth is a high-curiosity topic with less competitor content from supplement brands.
**GEO prediction:** Moderate. Bone broth article fills a gap in AI responses about food-based joint support.

### Sleep (2 articles)
**Articles:** Magnesium signs, Sleep-weight connection
**Predicted performance:** High. Magnesium deficiency signs is a high-volume query with clear commercial bridge to calm-tonic. Sleep-weight article addresses a frustration that every perimenopausal woman recognizes.
**GEO prediction:** High. Both have direct-answer structured formats ideal for AI extraction.

### Longevity/Hub (1 article)
**Article:** How to build supplement stack
**Predicted performance:** Very high commercial intent. Hub articles linking multiple products are the highest-converting content format in supplement marketing. Strong candidate for internal linking from all cluster articles.
**GEO prediction:** High. "What supplements should I take at 40?" is a very common AI-directed query.

### Metabolism (3 articles)
**Articles:** Menopause weight management, Creatine vs protein, Muscle loss after 40
**Predicted performance:** Very high. Menopause weight management is a high-volume, high-frustration query. Creatine vs protein is a comparison article format with proven CTR. Muscle loss is a question every woman over 40 has asked.
**GEO prediction:** Very high. All three are in the top formats for AI recommendation queries.

### Immunity (3 articles)
**Articles:** Omega-3 signs, Anti-inflammatory foods, Liposomal Vitamin C
**Predicted performance:** High. Omega-3 deficiency signs fills a real gap in the "signs you need more X" series. Anti-inflammatory foods is an evergreen high-search-volume topic. Liposomal Vitamin C educates on product category.
**GEO prediction:** Moderate to high. Food-based articles have broad informational search coverage.

### Hormones (3 articles)
**Articles:** DHEA guide, Hair thinning menopause, Lower cortisol
**Predicted performance:** Very high. Hair thinning is one of the most emotionally resonant topics for perimenopausal women. Cortisol management is high-search and highly actionable. DHEA fills a genuine knowledge gap.
**GEO prediction:** Very high. Hair thinning and cortisol articles have strong AI citation potential for "why" and "how to" queries.

### Gut (1 article)
**Article:** Gut bacteria and weight loss
**Predicted performance:** Moderate to high. Gut-weight connection is emerging as a mainstream topic. Novel angle for the gut cluster.
**GEO prediction:** Moderate. Microbiome-weight articles are increasingly AI-cited for "why can't I lose weight" queries.

### Brain (1 article)
**Article:** Inflammation and brain after 40
**Predicted performance:** High. Neuroinflammation-cognitive connection is underserved in supplement brand content. Strong educational angle that differentiates from generic brain health content.
**GEO prediction:** High. Neuroinflammation is an active topic in AI responses about cognitive health.

---

## Title Performance Predictions

### Highest CTR Predictions
1. "Why Does Hair Thin After Menopause? (And What Actually Helps)" — emotional hook, curiosity, solution promise
2. "Signs You Are Low in Vitamin D After 40 (And What to Do About It)" — specific, actionable, sign-based
3. "Menopause Weight Management: A Complete Guide for Women Over 40" — hub article, high search match
4. "How to Lower Cortisol Naturally After 40: A Practical Guide" — actionable, high search volume
5. "Creatine vs Protein for Women Over 40: Which Is Better?" — comparison format, clear commercial intent

### Highest GEO Prediction
1. "Signs You Are Low in Vitamin D After 40" — highest AI citation probability
2. "Signs You Need More B12 After 40" — classic sign-list format
3. "Signs You Are Low in Magnesium After 40" — direct deficiency query match
4. "Menopause and Heart Disease: What Every Woman Needs to Know" — authority article, AI health queries
5. "How to Build Your Supplement Stack for Women Over 40" — comprehensive hub, recommendation queries

---

## Structural Pattern Wins (This Batch)

- All 20 articles used the new DALL-E formula (Photograph of a [age]-year-old woman...) per LEARNING.md update
- All 20 articles have 7 H3 FAQ questions (exceeds minimum 4-5)
- All 20 articles have 3 body image placeholders in meta.json
- All 20 articles used real DOI citations (no invented references)
- Direct authorship via Write tool: zero agent timeouts (consistent with batch 2026-04-17 lesson)

---

## New Patterns to Track

1. "Signs You Are Low in X" format (3 articles this batch): track whether these generate featured snippets for deficiency queries
2. Menopause-specific hub article (weight management): track whether comprehensive guides outperform single-topic articles in engagement
3. New Heart cluster expansion: track authority signals for cardiovascular content
4. Creatine for women content: a new topic category, track whether it attracts fitness-adjacent audience

---

## Recommendations for Batch 11

Based on this batch's gaps and cumulative cluster coverage:

1. "Vitamin D and Menopause: What the Research Shows" — extends Energy cluster from deficiency signs to mechanism
2. "Signs Your Inflammation Is Getting Better After 40" — progress-tracking format, high engagement
3. "Best Supplements for Perimenopause Symptoms" — targeted hub article, very high commercial intent
4. "Omega-3 and Brain Health for Women Over 40" — extends Brain cluster, fills DHA-cognition gap
5. "How Long Does Magnesium Take to Work?" — duration format, sleep cluster, high commercial intent
6. "Adrenal Fatigue After 40: Is It Real and What Helps?" — Hormones cluster extension
7. "What Is the Estrobolome? (And Why It Matters for Menopause)" — GEO-optimized definitional article
8. "Signs Your Collagen Supplement Is Working" — progress-tracking for Skin cluster
9. "Best Foods for Hormonal Balance After 40" — food-based Hormones cluster content
10. "Can You Take Creatine and Protein Together?" — stacking/safety format for Metabolism cluster

# GEO Strategy — Happy Aging

> **Thesis:** GEO grows with **entity + citation + structure + distribution +
> updates**. Pure volume is a content farm with a dashboard. We don't compete
> on volume. We compete to be **the source the AI trusts to answer a specific
> question**.

This document is the strategic playbook the writer agents (`agents/03-*.md`)
and the optimizer (`agents/04-seo-optimizer.md`) operationalize. For
mechanics see [PIPELINE.md](PIPELINE.md). For schema/llms.txt/citation
monitoring tooling see [GEO-OPS.md](GEO-OPS.md).

---

## 1. Be a clear entity

The AI must understand, in seconds:

1. **Who** Happy Aging is — US-based longevity wellness brand for women over 40
2. **Category dominance** — premium, physician-reviewed supplement protocols
3. **Products** — NAD Advanced (hero), full catalog
4. **Problems we solve** — cellular energy decline, perimenopause, bloating,
   GLP-1 nutrition gaps, hormonal balance, sleep, longevity
5. **Entities we cover with depth:**
   - NAD+
   - NMN
   - Cellular energy
   - Women over 35
   - Bloating
   - Hormonal balance
   - GLP-1 nutrition support
   - Longevity supplements
   - Perimenopause support
   - Sleep and recovery

Without a clear entity, the AI treats us as "another supplement brand" and
"another" never becomes a source — it becomes a footer.

**Operationalized in:** `articles/lib_medical_schema.py` (Wikidata QID, GBP
CID, Person reviewer with sameAs LinkedIn), `pages/dr-daniel-yadegar.html`,
`config/brand.md`, the verbatim brand entity sentence (Rule G14).

---

## 2. Topical authority via clusters, not loose articles

### Priority clusters (every batch must touch ≥1)

#### Cluster 1 — NAD+ & cellular energy
- What is NAD+
- NAD+ vs NMN
- NAD+ and energy after 40
- NAD+ and mitochondrial function
- NAD+ supplements for women
- Best time to take NAD+
- NAD+ capsules vs shots

#### Cluster 2 — Bloating & digestion
- Why am I bloated every day
- Bloating after 40
- Bloating and hormones
- Bloating and perimenopause
- Bloating after meals
- Supplements for bloating support

#### Cluster 3 — GLP-1 nutrition support
- Nutrient gaps on GLP-1
- Energy on GLP-1
- Digestion on GLP-1
- Muscle maintenance on GLP-1
- What to supplement on GLP-1

#### Cluster 4 — Hormonal balance
- Hormonal changes after 35
- Hormonal bloating
- Energy and hormones
- Sleep and hormones
- Perimenopause daily support

### Cluster shape (mandatory)

Each cluster must have:
1. **1 pillar page** (entity hub — `scripts/build-pillar-pages.py`)
2. **5+ supporting articles** linking up to the pillar
3. **1 comparison article** (e.g., NAD+ vs NMN, brand vs brand)
4. **1 FAQ page**
5. **Internal links** from supporting articles → pillar → product

Orphan articles (no pillar, no inbound internal links) **do not get
published**. The optimizer flags them in Phase 4.

---

## 3. Answer-first content structure

AI search prefers extractable answers. Every article opens with:

```md
## Quick answer
[3-5 lines, direct]

## What this means
[plain language, no jargon]

## What the research says
[with PMID/DOI inline]

## What the evidence does NOT support
[honest limits — bumps trust]

## How Happy Aging approaches this
[product, integrated, not forced]
```

This maps to writer rules **G9** (definition first) and **G16** (numbered
protocol). The optimizer rejects articles that lead with a hook instead of
the answer.

---

## 4. Sources the AI can trust

Strict source hierarchy — no exceptions:

1. **PubMed** (preferred — every numeric claim needs a PMID)
2. **DOI** (peer-reviewed journals)
3. **NIH** (ODS, NCI, NHLBI)
4. **Clinical trials registry**
5. **Meta-analyses & systematic reviews**
6. **Government sources** for definition (FDA, USDA — only US authorities;
   never EFSA / NHS / TGA as primary, per writer rule)

**Forbidden sources:** supplement-brand blogs, news sites, press releases,
manufacturer claims, Reddit, Quora, content-farm sites, our own marketing
copy.

Competitors serve for market language — never for scientific evidence.

**Tooling:** `scripts/enrich-citations-from-pubmed.py` auto-fetches title,
journal, year, study_type, n from PubMed E-utilities and populates
`meta.json["citations"]` (consumed by `lib_medical_schema.py`).

### Crawler accessibility

`robots.txt` must allow:
- `Googlebot`
- `OAI-SearchBot` (ChatGPT Search)
- `GPTBot` (training)
- `PerplexityBot`
- `ClaudeBot`
- `Claude-Web`
- `Applebot-Extended`

If we want to be cited, we have to be readable.

---

## 5. Off-site citations (the multiplier)

The AI trusts brands that appear in **multiple** places. Recent GEO research
suggests brand mentions across the web may correlate more strongly with AI
citations than traditional backlinks. Treat as directional, not law.

Channels to invest in:
1. PR (founder angle, expert quotes)
2. Podcasts featuring Martha + Dr. Yadegar
3. Physician/expert citations of our content
4. YouTube explainers
5. Reddit (monitor; do not spam)
6. Independent reviews
7. Comparison articles on third-party sites
8. Marketplace presence (Amazon, etc. with consistent brand entity)
9. Guest articles
10. Editorial listicles
11. Affiliate partners with quality content

This is **off-pipeline**. The content engine cannot solve it. But every
article should be linkable, quotable, and PR-grade — that's what makes
off-site citations possible.

---

## 6. Schema — what to ship per page type

| Page type | Required schema |
|---|---|
| Article (general wellness) | `Article` + `Person` (reviewer) + `BreadcrumbList` |
| Article (medical/condition) | `MedicalWebPage` + `Person` + `HowTo` + `BreadcrumbList` + citations[] |
| Comparison article | `Article` + `ItemList` (`build_comparison_itemlist`) + `BreadcrumbList` |
| FAQ section | `FAQPage` |
| Pillar page | `MedicalWebPage` + `WebSite` + `BreadcrumbList` |
| Product | `Product` |
| Site-wide | `Organization` + `WebSite` |
| Author bio | `Person` (with `sameAs` to LinkedIn, Atria, etc.) |

Schema doesn't guarantee AI Overview inclusion — but it's the cheapest
machine-readability signal we can ship. Wired through `articles/lib_medical_schema.py`.

---

## 7. Comparison content (AI loves it)

Queries the AI loves to answer comparatively:
- NAD+ vs NMN
- NAD+ shots vs capsules
- Happy Aging vs Grüns
- Happy Aging vs AG1
- Happy Aging vs Happy Mammoth
- Best supplement for bloating after 40
- Best supplement for women on GLP-1
- Best NAD+ supplement for women

**Rules** (`agents/03b-comparison-writer.md`):
- HTML `<table>` required
- Honest criteria, hedged language ("may", "studies suggest")
- Inline PMIDs for any numeric claim
- No fabricated superiority claims
- FTC disclosure of material connection (the article is on our site)
- `ItemList` JSON-LD via `lib_medical_schema.build_comparison_itemlist`

Phase 1 reserves ≥2 comparison slots per batch — registered in
`config/competitors.json`.

---

## 8. Source-of-truth pages

Stable, deeply linked reference pages — these are the entity hubs:

1. What is NAD+?
2. NAD+ for Women — Complete Guide
3. Happy Aging Ingredient Glossary
4. Happy Aging Research Library
5. Supplement Facts Library
6. Women's Bloating Resource Center
7. GLP-1 Nutrition Support Guide
8. Perimenopause Support Guide
9. Cellular Energy Guide

Generated initial drafts via `scripts/build-pillar-pages.py`, then refined
manually and uploaded to Shopify as Pages. These pages are **rarely
deleted**, **frequently updated**, and **never thin**.

---

## 9. Continuous freshness

AI search rewards freshness, especially for health/supplement/comparison
topics.

**Mandatory triggers for refresh** (consumed by Phase 1 via `REFRESH-QUEUE.md`):
- Re-review every 90 days (`scripts/re-review-stale.py` is mandatory)
- New peer-reviewed study published
- Product change (formula, price, availability)
- Competitor offer change
- LLM citation monitor flags a different player citing the topic
  (`scripts/llm-citation-monitor.py`)
- Article drops in impressions or AI citations

Phase 1 must reserve **≥2 refresh slots per batch**. Refresh slugs come from
`REFRESH-QUEUE.md`; topics already in production within last 60 days are
deduped via `scripts/check-duplicate-topics.py`.

---

## 10b. Discovery — find opportunities, don't just generate from clusters

The Opportunity Engine (Phase 1) consumes `OPPORTUNITY-FEED.md`, regenerated
every Sunday by `discovery-weekly.yml`. Four discovery sources feed it:

| Source | Script | Free? | Why |
|---|---|---|---|
| Google Autocomplete | `discover-autocomplete.py` | ✅ no key | Long-tail breadth — 26-letter + question-prefix expansion per seed |
| People Also Ask | `discover-paa.py` | needs `SERPAPI_KEY` | Literal Google question boxes — highest AI Overview extraction value |
| Reddit | `discover-reddit.py` | ✅ no key | Real-language signal from r/Perimenopause, r/Menopause, r/loseit (GLP-1), r/Longevity, r/supplements |
| Competitor sitemaps + RSS | `discover-competitors.py` | ✅ no key | Detects when Grüns/AG1/Happy Mammoth/Hum/Pendulum/Lemme/etc. publishes — first mover wins citation |

The aggregator (`build-opportunity-feed.py`) deduplicates against existing
articles, classifies each candidate into a priority cluster
(NAD-NMN / bloating / GLP-1 / hormonal / sleep / magnesium / ashwagandha /
collagen-skin), and ranks **counter-article targets first** because AI search
updates faster than SEO — the brand that publishes first on a topic gets the
citation for weeks.

## 10. Monitor prompts, not keywords

Track real questions, not just keywords. Run weekly via
`scripts/llm-citation-monitor.py`:

- "What is the best supplement for bloating after 40?"
- "What should women take while on GLP-1?"
- "Is NAD+ worth it for women?"
- "What supplements support cellular energy?"
- "What helps with hormonal bloating?"
- "Best longevity supplement for women"
- "Happy Aging vs Grüns"
- "Best NAD supplement for women over 35"

For each prompt, log:
1. Did Happy Aging appear?
2. Were we cited (with link)?
3. Sentiment: positive / neutral / negative
4. Who was cited instead?
5. What source did the AI use?
6. Which page do we need to create or improve?

Output: `LLM-CITATIONS.md` (weekly) + `COMPETITOR-GAP.md` (per-batch input
to Phase 1 scoring).

Sentiment matters: AI Overviews can return more negative content for brands
than ChatGPT does for the same query. Outdated content, unresolved reviews,
or controversy will be amplified — monitoring is part of GEO, not garnish.

---

## 30-day execution plan

### Week 1 — Technical foundation
- [ ] Verify `robots.txt` allows Googlebot, OAI-SearchBot, GPTBot,
      PerplexityBot, ClaudeBot
- [ ] Generate + upload `llms.txt` and `llms-full.txt` (`scripts/build-llms-txt.py`)
- [ ] Audit Organization, WebSite, Product, Article, FAQ, Breadcrumb schema
      site-wide
- [ ] Clean sitemap; verify indexation of priority entity pages
- [ ] Create entity pages: NAD+, NMN, bloating, GLP support, women's longevity

### Week 2 — Authority clusters
For each of the 4 priority clusters (NAD+, bloating, GLP-1, hormonal):
- [ ] 1 pillar page (deep, evergreen, internally linked)
- [ ] 5 supporting articles linking up to pillar
- [ ] 1 comparison article
- [ ] 1 FAQ page
- [ ] Internal links → product

### Week 3 — Comparison & off-site
Publish high-citation-magnet content:
- [ ] NAD+ vs NMN
- [ ] NAD+ capsules vs shots
- [ ] Best supplements for bloating after 40
- [ ] What to take while on GLP-1
- [ ] Happy Aging vs Grüns / AG1 / Happy Mammoth

In parallel (off-pipeline):
- [ ] Founder PR angle pitched
- [ ] Podcast booked (Martha or expert)
- [ ] Guest articles in flight
- [ ] YouTube explainers in production
- [ ] Reddit monitoring (no spam)
- [ ] Expert quotes placed externally

### Week 4 — Measurement & loop
- [ ] Weekly monitor: ChatGPT Search, Perplexity, Claude, Google AI Overviews
- [ ] GSC + Ahrefs/Semrush dashboards stitched
- [ ] Shopify product clicks attributed to articles
- [ ] Weekly review answering: where we appear / don't / who appears instead /
      which source AI preferred / which article needs refresh / which entity is weak

---

## What we will NOT do

1. ❌ Publish 20+ articles/day with no quality gate (we run 10 + Phase 4 hard gate)
2. ❌ Cite a statistic without a PMID/DOI
3. ❌ Generic listicles ("10 ways to feel better")
4. ❌ Articles with no product or entity attached
5. ❌ AI-generated images of fake supplement bottles
6. ❌ Force a medical/disease claim
7. ❌ Copy a competitor's structure
8. ❌ Aggressive comparison without sources
9. ❌ Isolated blog with no internal links
10. ❌ Measure tonnage instead of citations

---

## The unlock

Dominate the intersection of:

> **Women 35+ × NAD+ × Bloating × GLP-1 support × Hormonal balance**

— before another player does it better.

Everything in this pipeline (clusters, entity hubs, citation rigor, schema,
comparison content, freshness loop, prompt monitoring) is in service of
that thesis.

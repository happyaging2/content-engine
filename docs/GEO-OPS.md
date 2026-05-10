# GEO Operations Manual — Happy Aging

This document covers the GEO (Generative Engine Optimization) infrastructure
that surrounds the writer/optimizer agents. Most pieces are automated; a handful
are manual one-time ops flagged at the bottom.

---

## Pipeline summary

```
01 Opportunity Engine         → topics
   ├── check-duplicate-topics.py    (mandatory dedup)
   └── competitor-citation-gap.py   (optional GEO scoring input)

02 SEO Brief Engine           → brief

03 Content Writer             → article + meta.json (G1–G18 GEO rules)

04 SEO Optimizer (gate)       → quality + FDA/FTC compliance

   qa-and-publish.sh:
     ├── enrich-citations-from-pubmed.py  (auto-fetch PMID metadata)
     ├── lib_medical_schema.py             (MedicalWebPage + Person + HowTo)
     ├── auto-internal-links.py            (graph-based linking)
     └── existing FAQ + Article schema

05 Publisher                  → Shopify
   └── indexnow-submit.sh    (notify Bing → ChatGPT Search)

06 Performance Engine
   └── llm-citation-monitor.py  (weekly: ChatGPT, Perplexity, Claude, AIO)

07 Learning Injection         → LEARNING.md (consumes LLM-CITATIONS.md)

re-review-stale.py            → REFRESH-QUEUE.md (90-day cadence, weekly)
build-llms-txt.py             → /llms.txt + /llms-full.txt (after each batch)
build-pillar-pages.py         → pages/pillar-*.html (when new entities are added)
```

---

## Autonomous execution — GitHub Actions

Everything below runs on a schedule with **no local machine required**. Just
configure repository secrets once (see next section) and the workflows trigger
themselves.

| Workflow file | Trigger | What it does |
|---|---|---|
| `.github/workflows/publish-shopify.yml`     | daily 11:00 UTC + manual | QA + publish today's batch to Shopify |
| `.github/workflows/geo-post-publish.yml`    | on push to `articles/**` | Build llms.txt, pillar pages, internal links, IndexNow ping |
| `.github/workflows/geo-weekly.yml`          | Mondays 06:00 UTC + manual | Flag stale articles (>90d) + LLM citation monitor |
| `.github/workflows/geo-monthly.yml`         | 1st of month 05:00 UTC + manual | Enrich PMIDs from PubMed + retro-patch MedicalWebPage schema |
| `.github/workflows/update-images.yml`       | manual                  | Force re-fetch covers + body images (legacy) |

The post-publish workflow uses a `concurrency: geo-post-publish` group with
`cancel-in-progress: true`, so back-to-back commits from the daily publish
collapse into a single run.

The `[skip ci]` suffix on auto-commits prevents recursive workflow triggers.

### Local cron alternative

If you ever want to run from a local machine instead, the equivalent crontab is:

```cron
0  8 * * * bash ~/Desktop/content-engine/scripts/daily-publish.sh
0  6 * * 1 cd ~/Desktop/content-engine && python3 scripts/re-review-stale.py
0  7 * * 1 cd ~/Desktop/content-engine && python3 scripts/llm-citation-monitor.py
0  5 1 * * cd ~/Desktop/content-engine && python3 scripts/enrich-citations-from-pubmed.py
```

But GitHub Actions is preferred — single source of truth, no maintenance.

---

## Repository Secrets (one-time setup for autonomy)

Add these in **GitHub → Settings → Secrets and variables → Actions → New
repository secret**. Required ones unblock the daily publish; optional ones
unlock additional autonomous behaviors (citation monitoring, IndexNow, etc.).

### Required (without these, the daily publish breaks)

| Secret | Purpose |
|---|---|
| `SHOPIFY_TOKEN`        | Shopify Admin API — publish + retro-patch |
| `PEXELS_API_KEY`       | Cover/body images (primary) |
| `PIXABAY_API_KEY`      | Cover/body images (secondary) |

### Recommended (each unlocks a piece of GEO autonomy)

| Secret | Unlocks |
|---|---|
| `NCBI_API_KEY`         | Monthly PMID enrichment at 10 req/s instead of 3 (faster, more reliable) |
| `INDEXNOW_KEY`         | Auto-notification of Bing → ChatGPT Search index after every publish |
| `PERPLEXITY_API_KEY`   | Weekly Perplexity citation tracking |
| `OPENAI_API_KEY`       | Weekly ChatGPT search citation tracking |
| `ANTHROPIC_API_KEY`    | Weekly Claude web-search citation tracking |
| `SERPAPI_KEY`          | Weekly Google AI Overviews citation tracking |
| `UNSPLASH_ACCESS_KEY`  | Image fallback when Pexels + Pixabay miss |

If a recommended secret is missing, the workflow logs a friendly skip message
and continues — nothing fails.

---

## Required env vars (legacy — for local cron use only)

| Var | Used by | Purpose |
|---|---|---|
| `SHOPIFY_TOKEN`           | publish, retro-patch | Shopify Admin API |
| `PEXELS_API_KEY`          | qa-and-publish     | Cover/body images (primary) |
| `PIXABAY_API_KEY`         | qa-and-publish     | Cover/body images (secondary) |
| `UNSPLASH_ACCESS_KEY`     | qa-and-publish     | Image fallback |
| `NCBI_API_KEY`            | enrich-citations   | PubMed (raises rate limit 3→10/s) |
| `INDEXNOW_KEY`            | indexnow-submit    | Bing IndexNow notification |
| `PERPLEXITY_API_KEY`      | llm-citation-monitor, competitor-gap | Sonar API |
| `OPENAI_API_KEY`          | llm-citation-monitor | gpt-4o-search-preview |
| `ANTHROPIC_API_KEY`       | llm-citation-monitor | Claude web search |
| `SERPAPI_KEY`             | llm-citation-monitor, competitor-gap | Google AI Overviews |

---

## 90-day re-review cadence

Every Monday, `re-review-stale.py` scans every `meta.json` and flags articles
whose `date_reviewed` (or `date_modified` / `date_published` fallback) is older
than 90 days. Flagged articles get:

- `needs_refresh: true`
- `refresh_reason: "..."`
- `refresh_flagged_on: <date>`

The list is also written to `REFRESH-QUEUE.md`. The Opportunity Engine reads
this queue and reserves at least 2 of every 20 batch slots for refreshes
(Phase 4 re-runs PMID validation, citation enrichment, and bumps the dates).

Why 90 days:
- Google YMYL freshness signal weighs `dateModified` heavily for health content.
- LLMs (Perplexity, ChatGPT Search, Google AIO) prefer content < 6 months old.
- Quarterly cadence catches new PMIDs and FDA updates without overwhelming review capacity.

---

## Dedup rules (Phase 1)

`check-duplicate-topics.py` rejects a candidate when ANY of:

1. Slug collision (exact, prefix, or suffix match).
2. Title token-overlap ≥ 55% (Jaccard, stopwords removed).
3. Same `primary_topic` + ≥2 shared `about` entities + existing article < 180 days old.

This guarantees the 548-article corpus doesn't accumulate near-duplicates that
cannibalize each other in Google and dilute entity authority for LLMs.

---

## Schema rendered per article

`lib_medical_schema.py` emits one JSON-LD block per article:

- `@type: MedicalWebPage` (or `Article` for non-clinical topics)
- `author` → Organization (Happy Aging Team)
- `reviewedBy` → Person (Dr. Daniel Yadegar) with `sameAs: [LinkedIn]`
- `publisher` → Organization with `sameAs` social network
- `citation: [ScholarlyArticle, …]` — every PMID/DOI as structured data
- `about: [Thing, …]` and `mentions: [Thing, …]`
- `inLanguage: en-US`
- `lastReviewed` and `dateModified`

When the article contains a numbered `<ol>` protocol (Rule G16), an additional
`HowTo` JSON-LD block is emitted.

Existing `BlogPosting` and `FAQPage` schemas are preserved (multiple
JSON-LD blocks per page is valid and Google reads all of them).

---

## /llms.txt

Generated by `scripts/build-llms-txt.py`. Two files:

- `public/llms.txt` — concise index, grouped by topic. Editorial standards
  upfront. Tells LLMs which page is canonical for which entity.
- `public/llms-full.txt` — full corpus with summaries. Used by LLMs that
  prefer a denser ingestion format.

**Manual upload step:** After running the script, upload both files to the
Shopify theme as static assets so they're served at:
- `https://happyaging.com/llms.txt`
- `https://happyaging.com/llms-full.txt`

(If Shopify won't serve `.txt` from the theme root, create a Shopify Page with
the matching slug and a redirect, or host them on the theme's `assets/` and
configure a redirect in `config/redirects.yaml`.)

---

## Pillar pages

`scripts/build-pillar-pages.py` produces hub pages for the 8 core entities:
NMN, NAD+, magnesium, perimenopause, sleep, longevity, ashwagandha, sirtuins.

Each pillar page:
- Carries the canonical `DefinedTerm` (or `MedicalCondition`) JSON-LD.
- Lists every related article in the corpus.
- Receives an internal link from every article in its cluster (via
  `auto-internal-links.py` and the `PILLAR_MAP` it consumes).

After running the script, upload each `pages/pillar-*.html` to Shopify as a
Page with the matching `pillar-<entity>` handle.

---

## Manual one-time ops (not automated — flag for human)

These build entity authority but require human accounts / approvals:

1. **Wikidata entry for "Happy Aging"** — create a free Wikidata item (Q-number).
   Add it to the Organization schema's `sameAs` list in `lib_medical_schema.py`.
   LLMs disambiguate brands via Wikidata.

2. **Google Business Profile** — create one even though Happy Aging is
   ecommerce. The Knowledge Panel feeds the brand entity recognition.

3. **Bing Webmaster Tools** — submit `sitemap.xml`. ChatGPT Search uses Bing's
   index; this guarantees ingestion.

4. **`<INDEXNOW_KEY>.txt`** — host the verification file at
   `https://happyaging.com/<key>.txt`. One-time. Then export `INDEXNOW_KEY`.

5. **Reviewer page upload** — upload `pages/dr-daniel-yadegar.html` to Shopify
   as a Page with handle `dr-daniel-yadegar`. Confirm the LinkedIn `rel=me`
   link works (LinkedIn must list the page back for full mutual verification —
   request via LinkedIn profile edit).

6. **Reddit / Quora seeding** — separate ops effort. LLMs train on community
   content. Strategy: real accounts, on-topic answers in r/longevity,
   r/Supplements, r/Menopause, with contextual links only when genuinely useful.

7. **Doximity / NPI listing for Dr. Yadegar** — once linked, add those URLs
   to `DEFAULT_REVIEWER["sameAs"]` in `lib_medical_schema.py`.

8. **Schema validator pass** — run https://validator.schema.org/ on a sample
   article, the author page, and a pillar page after first publish to confirm
   no JSON-LD errors.

# JARVIS Content Engine

Automated SEO/GEO content pipeline for Happy Aging (happyaging.com).
Daily run, 20 articles per cycle.

## Agent System

| Phase | Agent | File |
|---|---|---|
| — | Orchestrator | agents/orchestrator.md |
| 1 | Opportunity Engine | agents/01-opportunity-engine.md |
| 2 | SEO Brief Engine | agents/02-seo-brief-engine.md |
| 3 | Content Writer | agents/03-content-writer.md |
| 4 | SEO Optimizer (quality gate) | agents/04-seo-optimizer.md |
| 5 | Publisher | agents/05-publisher.md |
| 6 | Performance Engine | agents/06-performance-engine.md |
| 7 | Learning Injection | agents/07-learning-injection.md |

## Pipeline Flow
```
1. Opportunity Engine   → find top 20 topics
2. SEO Brief Engine     → deterministic brief per topic
3. Content Writer       → write article (injects LEARNING.md)
4. SEO Optimizer        → quality gate each article
5. Publisher            → push to Shopify
6. Performance Engine   → analyze patterns
7. Learning Injection   → update LEARNING.md (feeds back into Phase 3)
```

## Configuration
- Brand context: config/brand.md
- Learning rules (feedback loop): LEARNING.md
- Published articles: articles/
- Performance data: CONTENT-PERFORMANCE.md
- QA + publish script: scripts/qa-and-publish.sh
- **GEO operations manual: docs/GEO-OPS.md** — schema, llms.txt, pillar pages,
  90-day re-review, citation monitor, dedup, IndexNow, manual ops checklist

## GEO Infrastructure (US wellness market)
- **Schema per article** (`articles/lib_medical_schema.py`): MedicalWebPage /
  Article + Person reviewer (Dr. Daniel Yadegar, sameAs LinkedIn) + HowTo +
  citation array. Wired into `qa-and-publish.sh` and `articles/patch-seo.py`.
- **Retroactive schema patch**: `articles/patch-medical-schema.py` applies the
  above to all already-published articles via Shopify Admin API.
- **/llms.txt + /llms-full.txt**: `scripts/build-llms-txt.py` generates them
  in `public/`. Upload as Shopify theme assets at the site root.
- **Author page**: `pages/dr-daniel-yadegar.html` — upload as Shopify Page,
  handle `dr-daniel-yadegar`. Carries Person JSON-LD with sameAs LinkedIn.
- **Pillar pages**: `scripts/build-pillar-pages.py` produces 8 entity hubs
  (NMN, NAD+, magnesium, perimenopause, sleep, longevity, ashwagandha, sirtuins).
- **PMID enrichment**: `scripts/enrich-citations-from-pubmed.py` fetches title,
  journal, year, study_type, n from PubMed E-utilities and populates
  `meta.json["citations"]` (consumed by the medical schema lib).
- **LLM citation monitor**: `scripts/llm-citation-monitor.py` queries
  Perplexity, ChatGPT (gpt-4o-search-preview), Claude (web_search), and Google
  AI Overviews (SerpAPI) weekly. Output: `LLM-CITATIONS.md`.
- **Competitor citation gap**: `scripts/competitor-citation-gap.py` scores each
  candidate query by current LLM citation landscape (low-authority cited =
  green field). Output: `COMPETITOR-GAP.md`.
- **Internal linking**: `scripts/auto-internal-links.py` builds the knowledge
  graph by injecting cross-article links from shared `about`/`mentions`
  entities + linking primary entities to pillar pages.
- **IndexNow**: `scripts/indexnow-submit.sh` notifies Bing (= ChatGPT Search
  index) on each publish. Requires `INDEXNOW_KEY`.
- **90-day re-review**: `scripts/re-review-stale.py` flags articles where
  `date_reviewed` > 90 days. Output: `REFRESH-QUEUE.md` consumed by Phase 1.
- **Dedup**: `scripts/check-duplicate-topics.py` rejects candidate topics
  with slug collisions, ≥55% title token overlap, or recent overlapping
  entities. Mandatory pre-step before Phase 1 scoring.
- **Comparison content**: `config/competitors.json` registers competing brands
  per cluster. `scripts/generate-comparison-topics.py` produces
  `COMPARISON-QUEUE.md`; Phase 1 reserves ≥2 batch slots/cycle. When a brief's
  `format: comparison`, Phase 3 routes to `agents/03b-comparison-writer.md`
  (extends 03 with FTC compliance, required `<table>`, hedged-language rules).
  `lib_medical_schema.build_comparison_itemlist` emits `ItemList` JSON-LD.

## Publishing
Published via Shopify Admin API (REST). Prefer the script over raw curl:
```bash
cd /path/to/content-engine && bash scripts/qa-and-publish.sh [YYYY-MM-DD]
```

Required env vars: `SHOPIFY_TOKEN`. Optional: `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`.
Pexels is **primary**; Pixabay (free, no attribution) is secondary; Unsplash is fallback.

For daily automation: `scripts/daily-publish.sh` (cron-ready, lock file, logging).
Cron: `0 8 * * * bash ~/Desktop/content-engine/scripts/daily-publish.sh`

### Images
Article cover and body images are fetched from **Pexels** (primary) with
**Unsplash** as fallback. The writer emits `image_query` and
`body_image_queries` in each `*.meta.json`. The writer must NOT write `<img>` tags
or any `[BODY_IMAGE_N]` placeholders in the article HTML — the pipeline handles all images.

**Image variety strategy (patch-seo.py + qa-and-publish.sh):**
- Pre-fetch phase builds `image_pool`: per-article title queries + TOPIC_VISUAL_CONTEXT
- Pexels: `per_page=80` → up to 60 safe photos per query; Pixabay adds up to 30 more = 90 per query
- Covers: `pool[abs(hash(slug)) % len(pool)]` — unique per article, stable on re-runs
- Body images: `pool[abs(hash(slug + section_index)) % len(pool)]` — unique per article per section
- Each article gets its own title-derived cover query → nearly zero duplicate covers

**Image safety rules (enforced in both scripts):**
- Queries must use lifestyle / food / activity language only — NO "supplement", "bottle", "product", "vitamin", "pill"
- `BLOCKED_TERMS`: rejects alt text with product/bottle/medical/explicit/off-brand phrases (multi-word only)
- `COMPETITOR_BRANDS`: rejects OSH Wellness, Missha, VigorVault, Thorne, Jarrow, GNC, and 20+ others
- `TOPIC_VISUAL_CONTEXT`: maps supplement/medical keywords to safe lifestyle visual queries
- To re-fetch all images (e.g. after brand safety incident): clear `resolved_cover`/`resolved_body` from `*.meta.json`, then re-run `update-images.py`

**Acceptable imagery:** woman in nature, cooking, yoga, reading, portrait, walking, eating healthy food.  
**Never use:** supplement bottles, product shots, hands holding anything, medical/clinical settings, tattoos, book covers.

### What qa-and-publish.sh injects at publish time (Step 4)
- **`[BODY_IMAGE_N]` strip** — removes all placeholder text/tags in any format before injecting real images
- **Section images** — one per H2 section (skips first + FAQ/References); unique per article via slug hash
- **Contextual product links** — 1-2 inline `<a>` links per article, color `#8B7355`, matched by keyword to relevant Happy Aging product; skips intro paragraphs and existing links; idempotent
- **Product CTA block** — `article-product-cta` div before FAQ; flex layout with product image (CDN), contextual intro sentence derived from article title, real price, buy button; idempotent
- **FAQ JSON-LD schema** — FAQPage structured data before FAQ H2
- **Meta description** — first paragraph, ≤155 chars, saved to `meta.json` → `summary_html`

### Image APIs — important
- **Pexels**: must send `User-Agent` browser header (Cloudflare 403 without it). Free tier: 200 req/hour. Uses `per_page=80` to maximize variety per call.
- **Pixabay**: free API, no attribution required, 200 req/hour. Used as supplemental source to reach ~90 photos/query.
- **Unsplash**: fallback only (50 req/hour free tier).
- Image pool pre-fetched before article loop; article loop uses zero live calls.
- `TOPIC_VISUAL_CONTEXT` dict maps supplement/medical keywords to safe lifestyle visual queries (50+ entries).

### One-time fixes for already-published articles
```bash
# Fix SEO + images + product links + CTA on ALL published articles (511+):
SHOPIFY_TOKEN=... PEXELS_API_KEY=... PIXABAY_API_KEY=... python3 articles/patch-seo.py

# Inject Blog/ItemList/BreadcrumbList schema on blog listing page:
SHOPIFY_TOKEN=... python3 articles/patch-blog-schema.py

# Re-fetch all images (brand safety refresh):
SHOPIFY_TOKEN=... PEXELS_API_KEY=... python3 articles/update-images.py
```

Raw endpoint (parametrize in shell):
```bash
SHOPIFY_STORE="shop-happy-aging.myshopify.com"
BLOG_ID="109440303424"
curl -X POST "https://${SHOPIFY_STORE}/admin/api/2024-01/blogs/${BLOG_ID}/articles.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article": {"title": "...", "body_html": "...", "author": "Dr. Daniel Yadegar, MD", "tags": "...", "published": true, "template_suffix": "timeline"}}'
```

## Rules
- All text in English (US)
- No medical claims without citations
- No invented statistics
- Max 20 articles per batch
- Template suffix: `timeline`
- Author: `Happy Aging Team` (not Dr. Daniel Yadegar)
- Brand is **premium** — images must reflect that (no product bottles, no tattoos, no book covers, no competitor brands)
- Writer emits `image_query` + `body_image_queries` in meta.json — NOT `image_prompt` / DALL-E prompts
- Writer must NOT write `<img>` tags or `[BODY_IMAGE_N]` placeholders in article HTML
- Writer must NOT write a `article-product-cta` block — the pipeline injects it automatically
- Each article must include at least one "According to Happy Aging's review of..." proprietary data framing
- Priority clusters every batch: NAD/NMN + longevity + sleep = minimum 4 articles combined

## Writing Language Rules (CRITICAL)
- **Simple language**: 6th-8th grade reading level. Our persona is a busy woman over 40 — she wants clear, practical answers, not a medical journal.
- **No invented or estimated data**: NEVER cite statistics, percentages, or study findings unless they come from a real, verifiable source (PubMed PMID or DOI). If a number can't be verified, remove it.
- **No unreliable sources**: Do not use non-peer-reviewed blogs, news sites, press releases, or manufacturer claims as data sources. Only peer-reviewed studies.
- **Avoid jargon**: Replace technical terms with plain equivalents whenever possible. If a technical term must be used, explain it in the same sentence.
- **No condescending tone**: Write like a knowledgeable friend, not a doctor lecturing. Warm, direct, and encouraging.
- **Product linkage**: Every article must naturally lead to a Happy Aging product recommendation. The CTA intro connects the article topic to the specific product benefit (injected by the pipeline).

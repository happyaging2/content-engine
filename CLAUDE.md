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

## Publishing
Published via Shopify Admin API (REST). Prefer the script over raw curl:
```bash
cd /path/to/content-engine && bash scripts/qa-and-publish.sh [YYYY-MM-DD]
```

Required env vars: `SHOPIFY_TOKEN`, `UNSPLASH_ACCESS_KEY`. Optional:
`PEXELS_API_KEY` (fallback when Unsplash has no result).

For daily automation: `scripts/daily-publish.sh` (cron-ready, lock file, logging).
Cron: `0 8 * * * bash ~/Desktop/content-engine/scripts/daily-publish.sh`

### Images
Article cover and body images are fetched from **Pexels** (primary) with
**Unsplash** as fallback. The writer emits `image_query` and
`body_image_queries` in each `*.meta.json`.

**Image safety rules (enforced in both scripts):**
- Queries must use lifestyle / food / activity language only — NO "supplement", "bottle", "product", "vitamin", "pill"
- `BLOCKED_TERMS`: rejects any alt text containing product/bottle/medical/explicit/off-brand terms
- `COMPETITOR_BRANDS`: rejects OSH Wellness, Missha, VigorVault, Thorne, Jarrow, GNC, and 20+ others
- `TOPIC_QUERIES` map in `articles/update-images.py`: slug keyword → 2 curated lifestyle queries
- To re-fetch all images (e.g. after brand safety incident): clear `resolved_cover`/`resolved_body` from `*.meta.json`, then re-run `update-images.py`

**Acceptable imagery:** woman in nature, cooking, yoga, reading, portrait, walking, eating healthy food.  
**Never use:** supplement bottles, product shots, hands holding anything, medical/clinical settings, tattoos, book covers.

### SEO (injected at publish time by qa-and-publish.sh Step 4)
- **FAQ JSON-LD schema** — FAQPage structured data before FAQ H2
- **Meta description** — first paragraph, ≤155 chars, saved to `meta.json` → `summary_html`
- **Section images** — one per H2 section (skips first + FAQ/References), derived from H2 text

### One-time fixes for already-published articles
```bash
# Fix SEO (schema + meta description + section images) on all published articles:
SHOPIFY_TOKEN=... PEXELS_API_KEY=... python3 articles/patch-seo.py

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
- Brand is **premium** — images must reflect that (no product bottles, no tattoos, no book covers, no competitor brands)
- Content writer must use `image_query` + `body_image_queries` (NOT `image_prompt` / DALL-E prompts)

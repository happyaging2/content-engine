# Publishing & Asset Pipeline

Mechanics of `scripts/qa-and-publish.sh` — image fetch, schema injection,
product CTA, Shopify push. For runner internals see
[PIPELINE.md](PIPELINE.md). For agent rules see [CLAUDE.md](../CLAUDE.md).

---

## Daily flow

```bash
cd /path/to/content-engine && bash scripts/qa-and-publish.sh [YYYY-MM-DD]
```

Steps (each scoped to today's batch — see Batch Scoping below):

| Step | What |
|---|---|
| 0   | `git pull --rebase origin main` (handles race with agent-pipeline) |
| 0a  | PMID validation against PubMed (HEAD requests, 404 → strip `<li>`) |
| 1   | Fetch stock photos: Pexels → Pixabay → Unsplash |
| 2   | Fix product card images + prices (live `happyaging.com/products.json`) |
| 3   | DOI validation (HEAD `doi.org/<id>`, 404 → strip `<li>`) |
| 4   | Section images, contextual product links, CTA block, FAQ JSON-LD, MedicalWebPage JSON-LD, meta description |
| 5   | Push to Shopify Admin REST as **DRAFT** (`PUBLISH_DRAFT=true` default) |
| 6   | Verify count |

`set -e` is active — any step failing aborts the run. Exception: missing
image API keys causes Step 1 to `SystemExit(0)` (graceful), not 1.

---

## Batch scoping (critical)

Every step is scoped to today's batch via:

```python
meta["date_published"] == os.environ["BATCH_DATE"]
```

`BATCH_DATE` is exported at the top of `qa-and-publish.sh`. Without scoping,
the loops would iterate 500+ legacy articles re-fetching images and re-injecting
CTAs every run, wasting Pexels/Pixabay quota and risking rate limits.

The fallback (BATCH_DATE not set or no matching metas): legacy global glob —
preserved only for one-off backfills.

---

## Dedup at publish (Step 5)

Dedups against Shopify by **both slug (handle) and title**, paginating the
full Admin API list via the `Link: rel="next"` header. Phase 4 is allowed to
rewrite titles — slug-based dedup is the source of truth.

```python
if slug.lower() in existing_handles: continue
if title.lower() in existing_titles: continue
```

---

## Draft publishing

Articles publish as DRAFT by default (`PUBLISH_DRAFT=true`). User reviews +
clicks "Publish" in Shopify admin. Override for one-off auto-publish runs:

```bash
PUBLISH_DRAFT=false bash scripts/qa-and-publish.sh
```

---

## Images

Cover and body images come from **Pexels** (primary) → **Pixabay** (secondary,
free, no attribution) → **Unsplash** (fallback). Writer emits `image_query`
and `body_image_queries[]` in `meta.json`. **The writer must NOT write `<img>`
tags or `[BODY_IMAGE_N]` placeholders** — the pipeline handles all images.

### Image safety (enforced in Step 1 + Step 4)

- **Queries** must use lifestyle / food / activity language — never
  "supplement", "bottle", "product", "vitamin", "pill"
- **`BLOCKED_TERMS`** rejects alt text with product / bottle / medical /
  explicit / off-brand phrases (multi-word only — single words like "jar" are
  innocuous in cooking contexts)
- **`COMPETITOR_BRANDS`** rejects: OSH Wellness, Missha, VigorVault, Thorne,
  Jarrow, GNC, Life Extension, Tru Niagen, Wonderfeel, Elysium, and 20+ others
- **`TOPIC_VISUAL_CONTEXT`** dict (50+ entries) maps supplement/medical
  keywords to safe lifestyle visual queries (e.g. `"magnesium" → "relaxing
  calm evening"`)

### Acceptable / forbidden imagery

✅ woman in nature, cooking, yoga, reading, portrait, walking, eating healthy
food.

❌ supplement bottles, product shots, hands holding anything,
medical/clinical settings, tattoos, book covers, men, children.

### Re-fetching images (brand safety refresh)

```bash
# Clear resolved fields and re-run
SHOPIFY_TOKEN=... PEXELS_API_KEY=... python3 articles/update-images.py
```

To force re-fetch on a specific article: delete `resolved_cover` /
`resolved_body` from its `meta.json`, then re-run Step 1.

### Image variety strategy (in `articles/patch-seo.py`)

The one-time backfill script `patch-seo.py` builds a shared `image_pool`:
- Pexels `per_page=80` → up to 60 safe photos per query
- Pixabay adds up to 30 more = ~90 candidates per query
- Covers: `pool[abs(hash(slug)) % len(pool)]` — unique per article, stable
  on re-runs
- Body images: `pool[abs(hash(slug + section_index)) % len(pool)]`

The daily `qa-and-publish.sh` does per-article fetches (`per_page=10`); the
pool strategy is patch-seo only.

### Image API rate limits

- **Pexels**: requires browser `User-Agent` (Cloudflare 403 without it). Free
  tier 200 req/hour.
- **Pixabay**: free, no attribution, 200 req/hour.
- **Unsplash**: 50 req/hour free tier (fallback only).

---

## What Step 4 injects

| Element | Where |
|---|---|
| `[BODY_IMAGE_N]` strip | removes all placeholder formats (text, `<img>`, `<figure>`) |
| Section images | one per H2 (skips first H2 + FAQ + References) |
| Contextual product links | 1-2 inline `<a style="color:#8B7355">` per article, keyword-matched, idempotent |
| `article-product-cta` block | flex layout, product image (CDN), contextual intro derived from article title, real price, "Try {product} →" button |
| FAQ JSON-LD | `FAQPage` before FAQ H2 |
| MedicalWebPage / Article JSON-LD | Person reviewer (Dr. Daniel Yadegar, sameAs LinkedIn), HowTo, citations |
| Meta description | first paragraph, ≤155 chars, saved to `meta.json["meta_description"]` |

⚠️ Step 4 must `import sys` for the dynamic `articles/` path insert that
loads `lib_medical_schema`. Without it, `NameError` is silently swallowed by
the bare `except` and **medical schema is never injected** — fixed and verified.

---

## Shopify Admin REST endpoint

```bash
SHOPIFY_STORE="shop-happy-aging.myshopify.com"
BLOG_ID="109440303424"
curl -X POST "https://${SHOPIFY_STORE}/admin/api/2024-01/blogs/${BLOG_ID}/articles.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article": {"title": "...", "body_html": "...", "author": "Happy Aging Team", "tags": "...", "published": false, "template_suffix": "timeline"}}'
```

Always `published: false` (= draft). Always `template_suffix: timeline`.
Author is `Happy Aging Team` (NOT Dr. Daniel Yadegar — he is the
**reviewer**, surfaced in JSON-LD only).

---

## One-time fixes for already-published articles

```bash
# Fix SEO + images + product links + CTA on ALL published articles (511+):
SHOPIFY_TOKEN=... PEXELS_API_KEY=... PIXABAY_API_KEY=... python3 articles/patch-seo.py

# Inject Blog/ItemList/BreadcrumbList schema on the blog listing page:
SHOPIFY_TOKEN=... python3 articles/patch-blog-schema.py

# Re-fetch all images (brand safety refresh):
SHOPIFY_TOKEN=... PEXELS_API_KEY=... python3 articles/update-images.py

# Apply MedicalWebPage schema to legacy articles:
SHOPIFY_TOKEN=... python3 articles/patch-medical-schema.py
```

---

## Files

- `scripts/qa-and-publish.sh` — daily publish driver
- `articles/lib_medical_schema.py` — schema builders (MedicalWebPage,
  Article, HowTo, ItemList for comparisons, Person reviewer)
- `articles/patch-seo.py` — one-time backfill (image pool strategy)
- `articles/patch-medical-schema.py` — retroactive schema for legacy posts
- `articles/patch-blog-schema.py` — blog index ItemList + BreadcrumbList
- `articles/update-images.py` — image refresh (clears + re-resolves)

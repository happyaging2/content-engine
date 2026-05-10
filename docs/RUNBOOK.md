# Operations Runbook

Manual ops, environment variables, troubleshooting. For pipeline internals
see [PIPELINE.md](PIPELINE.md). For publishing see [PUBLISHING.md](PUBLISHING.md).

---

## Required environment / GitHub Secrets

| Secret | Required | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | All phases (Phase 1, 3, 4) |
| `SHOPIFY_TOKEN` | ✅ | `qa-and-publish.sh` Steps 5, 6 + all `articles/patch-*.py` |
| `PEXELS_API_KEY` | recommended | image fetch (primary) — without it, falls back to Pixabay/Unsplash |
| `PIXABAY_API_KEY` | recommended | image fetch (secondary) |
| `UNSPLASH_ACCESS_KEY` | optional | image fetch (last-resort fallback) |
| `NCBI_API_KEY` | optional | `enrich-citations-from-pubmed.py` (10x faster PMID lookups) |
| `INDEXNOW_KEY` | optional | `scripts/indexnow-submit.sh` (Bing/ChatGPT Search ping) |
| `PERPLEXITY_API_KEY` | optional | `llm-citation-monitor.py` |
| `OPENAI_API_KEY` | optional | `llm-citation-monitor.py` (gpt-4o-search-preview) |
| `SERPAPI_KEY` | optional | `llm-citation-monitor.py` (Google AI Overviews) |

If no image keys are set, Step 1 of `qa-and-publish.sh` exits gracefully
(SystemExit 0), Step 5 still publishes — articles just won't have stock
photos.

---

## Manual one-time setup (Shopify side)

1. Upload `pages/dr-daniel-yadegar.html` as a Shopify Page with handle
   `dr-daniel-yadegar` (carries Person JSON-LD with sameAs LinkedIn).
2. Run `scripts/build-pillar-pages.py`, then upload the 8 generated files in
   `pages/pillar-*.html` as Shopify Pages.
3. Run `scripts/build-llms-txt.py`, then upload `public/llms.txt` and
   `public/llms-full.txt` as theme assets at the site root.

---

## Daily operations checklist

Both schedules run in GitHub Actions (no local action needed):

- **06:00 UTC** — `agent-pipeline.yml` generates the day's batch, commits to main
- **11:00 UTC** — `publish-shopify.yml` runs `qa-and-publish.sh`, pushes drafts

After 11:00 UTC, open Shopify Admin → Blog → review drafts → bulk publish.

To trigger manually:

```bash
# CLI (gh)
gh workflow run agent-pipeline.yml -f batch_size=10
gh workflow run publish-shopify.yml -f batch_date=2026-05-10

# Or workflow_dispatch via the GitHub Actions UI
```

To run locally:

```bash
ANTHROPIC_API_KEY=... python3 scripts/run-pipeline.py
SHOPIFY_TOKEN=... PEXELS_API_KEY=... bash scripts/qa-and-publish.sh
```

---

## Troubleshooting

### Phase 4 keeps rejecting articles

Check `articles/<slug>.meta.json` → `fda_ftc_violations_at_review`. The
optimizer rejects on disease claims ("treats", "cures"), unsubstantiated
superlatives ("clinically proven" without inline PMID), or `geo_score < 70`.
Either bump `PHASE4_MODEL=claude-opus-4-7` (often resolves edge-case false
rejects), or update `agents/03-content-writer.md` rules to head off the
violation upstream.

### Pexels returns 403 / Cloudflare blocks

The script sends a browser `User-Agent` — if you see 403s, Pexels may have
rate-limited the GitHub Actions IP range. Free tier is 200 req/hour. Worst
case the script falls through to Pixabay (free, no rate limit issues seen).

### `MedicalWebPage` JSON-LD missing from published articles

Step 4 needs `import sys` in its heredoc to load `lib_medical_schema`. If
you see `WARN: medical schema injection failed for <slug>: NameError`, that
import is missing — it's there in current main, but watch for regressions.

### Duplicate publishes

Step 5 dedups by **slug (handle) AND title**. If you see duplicates,
verify the Shopify pagination loop is following the `Link: rel="next"`
header all the way through. Phase 4 may have rewritten the title — that's
why slug-based dedup matters.

### Push race between agent-pipeline and publish-shopify

Both have `concurrency:` groups + rebase-with-retry (4 attempts, exponential
backoff). If a push still fails, check for non-fast-forward conflicts on
`articles/*.meta.json` — usually means Step 1's resolved-cover commits raced
the agent-pipeline batch commit. Resolve with rebase manually.

### `[BODY_IMAGE_N]` placeholder visible on a live article

Writer (Phase 3) shouldn't emit these — `agents/03-content-writer.md`
forbids it explicitly. But Step 4 also strips them defensively. If one made
it through, run:

```bash
SHOPIFY_TOKEN=... python3 articles/patch-seo.py
```

…to re-inject images and clean the placeholders on Shopify.

---

## Cost monitoring

Per batch (10 articles):

| Phase | Model | Approx cost / article |
|---|---|---|
| 1 | Opus 4.7 | shared across all 10 (~$0.10 total) |
| 3 | Sonnet 4.6 (parallel, cached) | ~$0.04-0.08 each (cache hits after 1st) |
| 4 | Sonnet 4.6 (parallel, optional rewrite) | ~$0.02-0.05 each on pass; ~$0.10 on fix_and_pass |

Total daily target: **<$2/day for 10 articles** with current settings. Bump
to Opus on Phase 4 (`PHASE4_MODEL=claude-opus-4-7`) raises cost ~5x.

---

## Useful queries

```bash
# Today's batch report
cat articles/batch-$(date -u +%Y-%m-%d)-report.md

# How many drafts unpublished on Shopify
curl -s "https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles/count.json?published_status=unpublished" \
  -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN"

# Find articles below GEO score 80
jq -r 'select(.geo_score < 80) | "\(.slug) \(.geo_score)"' articles/*.meta.json

# Find articles missing citations
jq -r 'select((.citations | length) == 0) | .slug' articles/*.meta.json

# Articles overdue for re-review (>90 days)
python3 scripts/re-review-stale.py
```

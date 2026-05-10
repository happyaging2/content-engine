# JARVIS Content Engine

Automated SEO/GEO content pipeline for Happy Aging (happyaging.com).
Daily run, **10 articles per cycle** (default `batch_size=10`).

> This file is the operational contract — agents, models, commands, and
> inviolable rules. For deeper context see:
> - **GEO strategy & playbook** → [docs/GEO-STRATEGY.md](docs/GEO-STRATEGY.md)
> - **Runner internals** (Phase 1/3/4 mechanics, schemas, cost) → [docs/PIPELINE.md](docs/PIPELINE.md)
> - **Publishing pipeline** (`qa-and-publish.sh`, image rules, Shopify) → [docs/PUBLISHING.md](docs/PUBLISHING.md)
> - **GEO operations** (schema, llms.txt, pillars, citation monitor) → [docs/GEO-OPS.md](docs/GEO-OPS.md)
> - **Runbook** (env vars, troubleshooting, manual ops) → [docs/RUNBOOK.md](docs/RUNBOOK.md)

---

## Agent System

| Phase | Agent | File | Model |
|---|---|---|---|
| — | Orchestrator | `agents/orchestrator.md` | — |
| 1 | Opportunity Engine | `agents/01-opportunity-engine.md` | Opus 4.7 |
| 2 | SEO Brief Engine | `agents/02-seo-brief-engine.md` | (deterministic) |
| 3 | Content Writer | `agents/03-content-writer.md` (+ `03b-comparison-writer.md`) | Sonnet 4.6 (parallel) |
| 4 | SEO Optimizer (quality gate) | `agents/04-seo-optimizer.md` | Sonnet 4.6 (parallel; override `PHASE4_MODEL=claude-opus-4-7`) |
| 5 | Publisher | `agents/05-publisher.md` | — |
| 6 | Performance Engine | `agents/06-performance-engine.md` | — |
| 7 | Learning Injection | `agents/07-learning-injection.md` | — |

## Pipeline Flow
```
1. Opportunity Engine   → 10 prioritized topics (≥2 comparison, ≥2 refresh)
2. SEO Brief Engine     → deterministic brief per topic
3. Content Writer       → parallel writers (concurrency=5), Sonnet 4.6
4. SEO Optimizer        → parallel quality gate; pass = no rewrite (cost saver);
                          reject OR geo_score<70 = orphan files cleaned
5. Publisher            → push DRAFT to Shopify (PUBLISH_DRAFT=true default)
6. Performance Engine   → analyze patterns
7. Learning Injection   → update LEARNING.md (feeds back into Phase 3)
```

## Commands

```bash
# Generate today's batch (default 10 articles, concurrency 5)
ANTHROPIC_API_KEY=... python3 scripts/run-pipeline.py

# Override
python3 scripts/run-pipeline.py --batch-date 2026-05-10 --batch-size 10 --concurrency 5
python3 scripts/run-pipeline.py --dry-run                       # Phase 1 only
PHASE4_MODEL=claude-opus-4-7 python3 scripts/run-pipeline.py    # max-rigor gate

# Publish today's drafts
SHOPIFY_TOKEN=... PEXELS_API_KEY=... PIXABAY_API_KEY=... bash scripts/qa-and-publish.sh
```

## Configuration index

- Brand context → `config/brand.md`
- Hero product (default CTA = NAD Advanced) → `config/hero-product.json`
- Competitors per cluster → `config/competitors.json`
- Learning rules (feedback loop, consumed by Phase 3) → `LEARNING.md`
- Performance data → `CONTENT-PERFORMANCE.md`
- Published articles → `articles/`

---

## Inviolable Rules

### Strategy (see GEO-STRATEGY.md)
- We are not a content farm. We dominate **clusters**, not keywords.
  Priority clusters: NAD+ / NMN, bloating after 40, GLP-1 nutrition support,
  hormonal balance, women 35+ longevity.
- Every batch: ≥4 articles combined across NAD/NMN + longevity + sleep.
- Every batch: ≥2 comparison topics + ≥2 refreshes (90-day stale queue).
- Every article belongs to a cluster with a pillar page; orphan articles
  are not published.

### Writing
- All text in **English (US)**. 6th-8th grade reading level.
- **No invented statistics.** Numbers require an inline PMID or DOI to a
  peer-reviewed study. No blogs, no press releases, no manufacturer claims.
- **No medical / disease claims.** Use structure-function language only
  ("supports", "may help maintain", "associated with"). Never "treats",
  "cures", "prevents", "reverses" tied to a supplement.
- Persona: knowledgeable friend, not doctor lecturing. Warm, direct.
- Each article includes ≥1 "According to Happy Aging's review of..."
  proprietary framing.

### Publishing
- **10 articles per batch** (default `batch_size=10`)
- Publishes as **DRAFT** by default (`PUBLISH_DRAFT=true`); user reviews and
  publishes manually in Shopify Admin
- Template suffix: `timeline`
- Author: `Happy Aging Team` (NOT Dr. Daniel Yadegar — he is the **reviewer**,
  surfaced in JSON-LD only)
- Brand is **premium** — no product bottles, no tattoos, no book covers, no
  competitor brands in imagery
- Phase 4 reject (`verdict=reject` OR `geo_score<70`) drops the article AND
  removes any prior `-final.html` / `meta.json` for the same slug (orphan
  cleanup); reject is final, no retry

### Writer must NOT
- Write `<img>` tags or `[BODY_IMAGE_N]` placeholders in article HTML —
  the pipeline injects all images
- Write a `article-product-cta` block — pipeline injects it automatically
- Emit `image_prompt` / DALL-E prompts — only `image_query` and
  `body_image_queries[]` strings for stock-photo search

---

## GitHub Actions schedules

| Workflow | Cron | Action |
|---|---|---|
| `agent-pipeline.yml` | `0 6 * * *` (06:00 UTC) | Phase 1 → 4, commit to main |
| `publish-shopify.yml` | `0 11 * * *` (11:00 UTC) | `qa-and-publish.sh` → drafts |
| `geo-weekly.yml` | Mon 06:00 UTC | refresh queue + citation monitor |
| `geo-monthly.yml` | 1st of month | rank tracking + pillar refresh |
| `geo-post-publish.yml` | on push | llms.txt + internal links |

Both push workflows have `concurrency:` group + rebase-with-retry.

---

## Where to look when

| Working on… | Read |
|---|---|
| Topic / cluster strategy, pillar pages, prompt monitoring | `docs/GEO-STRATEGY.md` |
| Phase 1/3/4 internals, JSON schemas, model choices, costs | `docs/PIPELINE.md` |
| Image rules, Shopify push, CTA injection, dedup | `docs/PUBLISHING.md` |
| Schema (`MedicalWebPage`), `llms.txt`, IndexNow, dedup CLI | `docs/GEO-OPS.md` |
| Env vars, Secrets, troubleshooting, manual ops | `docs/RUNBOOK.md` |
| Writer rules (G1-G18), comparison writing, FDA/FTC checklist | `agents/03-*.md`, `agents/04-seo-optimizer.md` |

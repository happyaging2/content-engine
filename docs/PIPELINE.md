# Pipeline Internals

Runner mechanics for `scripts/run-pipeline.py` and `scripts/agent_runner/`.
For agent definitions and operational rules, see [CLAUDE.md](../CLAUDE.md).
For publishing mechanics, see [PUBLISHING.md](PUBLISHING.md).

---

## Runner

`scripts/run-pipeline.py` drives Phase 1 → Phase 4 autonomously and writes
`articles/<slug>-final.html` + `articles/<slug>.meta.json`. Downstream
`qa-and-publish.sh` picks them up and pushes to Shopify as drafts.

```bash
# Default: 10 articles, concurrency 5
ANTHROPIC_API_KEY=... python3 scripts/run-pipeline.py

# Overrides
python3 scripts/run-pipeline.py --batch-date 2026-05-10 --batch-size 10 --concurrency 5
python3 scripts/run-pipeline.py --dry-run                       # Phase 1 only
PHASE4_MODEL=claude-opus-4-7 python3 scripts/run-pipeline.py    # max-rigor gate
```

Phase 4 reject (`verdict=reject` OR `geo_score<70`) drops the article AND
removes any prior `-final.html` / `meta.json` for the same slug (orphan
cleanup). Prevents republishing yesterday's pass after today's reject.

---

## Phase 1 — Opportunity Engine

- Model: **Opus 4.7** with adaptive thinking + `effort=high`
- Output: JSON schema (`PHASE1_SCHEMA`) — list of topics with priority score,
  cluster, format (`standard` | `comparison`), `is_refresh`, `refresh_slug`
- Composition rules (enforced in user prompt):
  - ≥2 comparison slots from `COMPARISON-QUEUE.md`
  - ≥2 refresh slots from `REFRESH-QUEUE.md`
  - ≥4 combined NAD/NMN + longevity + sleep
- Persists `articles/batch-<date>-report.md` for traceability

---

## Phase 3 — Content Writer (parallel)

- Model: **Sonnet 4.6** with adaptive thinking + `effort=medium`
- Concurrency: `asyncio.Semaphore(--concurrency)` (default 5) over
  `AsyncAnthropic.messages.stream`
- Two cached system prompts: `standard_sys` and `comparison_sys` (writer rules
  + `agents/03b-comparison-writer.md` for comparison topics). Shared across all
  parallel calls → prompt-cache hit on every writer after the first.
- `max_tokens=32000` to allow long articles; streaming covers the timeout risk
- Output schema (`PHASE3_OUTPUT_SCHEMA`) requires: `body_html`, `slug`,
  `image_query`, `body_image_queries`, `about[]`, `mentions[]`, `citations[]`
  (each with `pmid`/`doi` + metadata), `schema_type` (`MedicalWebPage` |
  `Article`), `format`, `products_compared` (when comparison).
- Exception handling is broad (`except Exception`) so a single
  `JSONDecodeError` or transient `httpx` error never kills sibling articles
  in the gather.

---

## Phase 4 — SEO Optimizer (parallel quality gate)

- Default model: **Sonnet 4.6** (~5x cheaper than Opus 4.7) — sufficient for
  the deterministic checklist gate. Override per-run with
  `PHASE4_MODEL=claude-opus-4-7` for maximum rigor.
- Concurrency: same Semaphore pattern as Phase 3
- `max_tokens=32000`, adaptive thinking, `effort=high`
- Verdicts: `pass` | `fix_and_pass` | `reject`
- `geo_score` integer 0-100; `<70` = auto-reject
- `fda_ftc_violations[]` lists every disease claim, unsubstantiated
  superlative, fabricated testimonial. Empty array required if clean.

### Cost saver — optional `final_*` fields

`final_body_html`, `final_title`, `final_seo_title`, `final_meta_description`
are **optional** in the JSON schema. On `verdict=pass`, the gate omits them
and the runner reuses the Phase 3 article — avoids regenerating ~3-8k tokens
per clean article. Only `verdict=fix_and_pass` returns rewritten HTML.

`_phase4_finalize()` falls back to the Phase 3 article when fields are absent.

---

## GitHub Actions schedules

| Workflow | Cron | Action |
|---|---|---|
| `agent-pipeline.yml` | `0 6 * * *` (06:00 UTC) | Phase 1 → 4, commit to main |
| `publish-shopify.yml` | `0 11 * * *` (11:00 UTC) | `qa-and-publish.sh` → Shopify drafts |
| `geo-weekly.yml` | Mon 06:00 UTC | refresh queue + citation monitor |
| `geo-monthly.yml` | 1st of month | rank tracking + pillar refresh |
| `geo-post-publish.yml` | on push | llms.txt + internal links |

Both `agent-pipeline.yml` and `publish-shopify.yml` push to `main`. They have
a `concurrency:` group + rebase-with-retry (4 attempts, exponential backoff)
on every push to handle the race window between 06:00 (generation) and 11:00
(publish).

---

## Cost & performance notes

- Phase 4 default Sonnet 4.6 + optional `final_body_html` ≈ 80% cost
  reduction vs. the original always-Opus + always-rewrite design.
- Phase 3 prompt cache: first writer pays the cache-write cost; every
  subsequent parallel writer in the batch reads from cache.
- Phase 3 catches broad `Exception` so one malformed JSON never poisons the
  whole `asyncio.gather`.
- Concurrency is bounded by the semaphore (default 5) to respect Anthropic
  rate limits while still parallelizing 10/10 articles in roughly the time of
  two sequential ones.

---

## Files

- `scripts/run-pipeline.py` — orchestrator
- `scripts/agent_runner/__init__.py` — public exports
- `scripts/agent_runner/phases.py` — Phase 1, 3, 4 implementations
- `scripts/agent_runner/context.py` — system-prompt builders (cached)

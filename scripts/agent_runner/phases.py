"""
Phase implementations for the content-pipeline runner.

Phase 1 — Opus 4.7 strategy: emit 10 prioritized topics as JSON via
`output_config.format` (json_schema). Adaptive thinking + effort=high.

Phase 3 — Sonnet 4.6 writers in parallel: 10 articles concurrently via
AsyncAnthropic + asyncio.gather. Streamed with .stream() / .get_final_message()
to avoid HTTP timeouts on long generations. Same system prompt shared across
all 10 calls = prompt cache hit on each subsequent writer.

Phase 4 — Opus 4.7 quality gate: scores each article, returns verdict + final
HTML. Adaptive thinking + effort=high. Auto-rejects on FDA/FTC red flags.

All phases:
- Use SDK typed exceptions (anthropic.RateLimitError, etc.)
- Stream long responses (.stream())
- Default max_tokens 16000 unless streaming, then up to 64000
- Write outputs under articles/<slug>.html and articles/<slug>.meta.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any

import anthropic
from anthropic import Anthropic, AsyncAnthropic

from .context import (
    build_phase_system_blocks,
    build_writer_system_blocks,
)

log = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTICLES_DIR = os.path.join(ROOT, "articles")

# Models per claude-api skill recommendations:
#   Opus 4.7 — strategy + critical review (effort matters more than on prior Opus)
#   Sonnet 4.6 — high-volume writing (cheaper, faster, parallelizable)
MODEL_OPUS = "claude-opus-4-7"
MODEL_SONNET = "claude-sonnet-4-6"

# Adaptive thinking is the recommended mode on 4.6+ models. effort=high is the
# minimum for intelligence-sensitive work; xhigh would be ideal for Phase 4 but
# we keep cost predictable at high. Override per-call if needed.
THINKING_ADAPTIVE = {"type": "adaptive"}
EFFORT_HIGH = {"effort": "high"}
EFFORT_MEDIUM = {"effort": "medium"}


# ── Phase 1 — Opportunity Engine ───────────────────────────────────────────────

PHASE1_SCHEMA = {
    "type": "object",
    "properties": {
        "batch_date": {"type": "string"},
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "primary_keyword": {"type": "string"},
                    "search_intent": {
                        "type": "string",
                        "enum": ["informational", "comparison", "investigative", "transactional"],
                    },
                    "cluster": {"type": "string"},
                    "format": {
                        "type": "string",
                        "enum": ["standard", "comparison"],
                    },
                    "why_it_matters": {"type": "string"},
                    "conversion_angle": {"type": "string"},
                    "article_angle": {"type": "string"},
                    "priority_score": {"type": "number"},
                    "is_refresh": {"type": "boolean"},
                    "refresh_slug": {
                        "type": ["string", "null"],
                        "description": "If is_refresh=true, the existing slug to update.",
                    },
                },
                "required": [
                    "topic",
                    "primary_keyword",
                    "search_intent",
                    "cluster",
                    "format",
                    "why_it_matters",
                    "conversion_angle",
                    "article_angle",
                    "priority_score",
                    "is_refresh",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["batch_date", "topics"],
    "additionalProperties": False,
}


def run_phase1(
    *,
    batch_date: str,
    batch_size: int,
    refresh_queue_md: str = "",
    comparison_queue_md: str = "",
    performance_md: str = "",
    llm_citations_md: str = "",
    competitor_gap_md: str = "",
) -> dict:
    """Generate today's batch of topics. Returns {batch_date, topics: [...]}."""
    client = Anthropic()
    system = build_phase_system_blocks(["01-opportunity-engine.md"])

    user_message = (
        f"Generate exactly {batch_size} topics for batch date {batch_date}.\n\n"
        f"## Batch composition rules\n"
        f"- ≥2 of the {batch_size} slots must be **comparison topics** (set "
        f"`format: \"comparison\"`). Pull from COMPARISON-QUEUE below.\n"
        f"- ≥2 of the {batch_size} slots must be **refreshes of stale articles** "
        f"(set `is_refresh: true` and `refresh_slug` to the slug). Pull from "
        f"REFRESH-QUEUE below.\n"
        f"- Priority clusters (per docs/GEO-STRATEGY.md): NAD/NMN + "
        f"bloating + GLP-1 nutrition support + hormonal balance — at least "
        f"4 slots combined per batch. Each batch must touch ≥1 of these.\n"
        f"- Default product CTA for longevity/NAD/NMN/multi-system topics is "
        f"NAD Advanced (config/hero-product.json).\n\n"
        f"## Performance feedback loop (CRITICAL — read before scoring)\n"
        f"Bias topic selection toward clusters/topics that:\n"
        f"  - Show product-click conversion in CONTENT-PERFORMANCE.md\n"
        f"  - Are queries where competitors won AI citations this week\n"
        f"    (LLM-CITATIONS.md `Lost` rows) — generate counter-articles\n"
        f"  - Have low AI authority competitors per COMPETITOR-GAP.md\n\n"
        f"## CONTENT-PERFORMANCE.md (last batch outcomes)\n"
        f"```\n{performance_md or '(empty — first run)'}\n```\n\n"
        f"## LLM-CITATIONS.md (where Happy Aging was/wasn't cited this week)\n"
        f"```\n{llm_citations_md or '(empty — run scripts/llm-citation-monitor.py)'}\n```\n\n"
        f"## COMPETITOR-GAP.md (low-authority queries to attack)\n"
        f"```\n{competitor_gap_md or '(empty — run scripts/competitor-citation-gap.py)'}\n```\n\n"
        f"## REFRESH-QUEUE.md\n```\n{refresh_queue_md or '(empty)'}\n```\n\n"
        f"## COMPARISON-QUEUE.md\n```\n{comparison_queue_md or '(empty)'}\n```\n"
    )

    log.info("Phase 1: %s topics for %s", batch_size, batch_date)
    with client.messages.stream(
        model=MODEL_OPUS,
        max_tokens=16000,
        thinking=THINKING_ADAPTIVE,
        output_config={
            **EFFORT_HIGH,
            "format": {"type": "json_schema", "schema": PHASE1_SCHEMA},
        },
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        msg = stream.get_final_message()

    text = next((b.text for b in msg.content if b.type == "text"), "")
    data = json.loads(text)
    log.info(
        "Phase 1 complete. cache_read=%s cache_write=%s",
        msg.usage.cache_read_input_tokens,
        msg.usage.cache_creation_input_tokens,
    )
    return data


# ── Phase 3 — Content Writer (parallel) ────────────────────────────────────────

PHASE3_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "seo_title": {"type": "string"},
        "slug": {"type": "string"},
        "meta_description": {"type": "string"},
        "primary_keyword": {"type": "string"},
        "secondary_keywords": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "excerpt": {"type": "string"},
        "image_query": {"type": "string"},
        "body_image_queries": {"type": "array", "items": {"type": "string"}},
        "about": {"type": "array", "items": {"type": "string"}},
        "mentions": {"type": "array", "items": {"type": "string"}},
        "primary_topic": {"type": "string"},
        "schema_type": {
            "type": "string",
            "enum": ["MedicalWebPage", "Article"],
        },
        "format": {"type": "string", "enum": ["standard", "comparison"]},
        "products_compared": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "form": {"type": ["string", "null"]},
                    "active": {"type": ["string", "null"]},
                    "dose": {"type": ["string", "null"]},
                    "third_party_tested": {"type": ["string", "null"]},
                },
                "required": ["name", "url"],
                "additionalProperties": False,
            },
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pmid": {"type": ["string", "null"]},
                    "doi": {"type": ["string", "null"]},
                    "title": {"type": ["string", "null"]},
                    "year": {"type": ["integer", "null"]},
                    "study_type": {"type": ["string", "null"]},
                    "n": {"type": ["integer", "null"]},
                },
                "additionalProperties": False,
            },
        },
        "body_html": {
            "type": "string",
            "description": "The full article HTML. No <img> tags, no [BODY_IMAGE_N] placeholders, no product-card-cta.",
        },
    },
    "required": [
        "title",
        "seo_title",
        "slug",
        "meta_description",
        "primary_keyword",
        "tags",
        "excerpt",
        "image_query",
        "body_image_queries",
        "about",
        "primary_topic",
        "schema_type",
        "format",
        "citations",
        "body_html",
    ],
    "additionalProperties": False,
}


async def _write_one_article(
    async_client: AsyncAnthropic,
    *,
    topic: dict,
    batch_date: str,
    system_blocks: list[dict],
) -> dict:
    """Single Phase 3 writer call. Returns the parsed article object."""
    user_message = (
        f"Write today's article for batch {batch_date}.\n\n"
        f"## Topic brief\n"
        f"{json.dumps(topic, ensure_ascii=False, indent=2)}\n\n"
        f"## Output requirements\n"
        f"- Follow ALL writer rules (G1–G18) from agents/03-content-writer.md.\n"
        f"- If `format: \"comparison\"`, also follow agents/03b-comparison-writer.md "
        f"and populate `products_compared`.\n"
        f"- Default CTA: NAD Advanced for longevity / NAD / NMN / multi-system.\n"
        f"- Today's date is {batch_date}. Use it for the freshness signal "
        f"(Rule G17) and as `date_published` / `date_reviewed`.\n"
        f"- Output JSON only — body_html is the full article HTML, no preamble."
    )

    async with async_client.messages.stream(
        model=MODEL_SONNET,
        max_tokens=32000,  # allow long articles; streaming covers timeout risk
        thinking=THINKING_ADAPTIVE,
        output_config={
            **EFFORT_MEDIUM,
            "format": {"type": "json_schema", "schema": PHASE3_OUTPUT_SCHEMA},
        },
        system=system_blocks,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        msg = await stream.get_final_message()

    text = next((b.text for b in msg.content if b.type == "text"), "")
    article = json.loads(text)
    article["date_published"] = batch_date
    article["date_reviewed"] = batch_date
    article["date_modified"] = batch_date
    log.info(
        "  ✓ %s  cache_read=%s",
        article["slug"][:50],
        msg.usage.cache_read_input_tokens,
    )
    return article


async def _phase3_async(
    *,
    topics: list[dict],
    batch_date: str,
    concurrency: int = 5,
) -> list[dict]:
    """Write all topics concurrently. Concurrency bounded by `concurrency`
    to respect rate limits. The system prompt is shared across all calls so
    every parallel writer hits the same prompt cache."""
    async_client = AsyncAnthropic()

    # Two system prompts: one for standard articles, one for comparison.
    # We render both upfront so we don't redo the work per call.
    standard_sys = build_writer_system_blocks(comparison=False)
    comparison_sys = build_writer_system_blocks(comparison=True)

    sem = asyncio.Semaphore(concurrency)

    async def _bounded(topic):
        async with sem:
            sys_blocks = comparison_sys if topic.get("format") == "comparison" else standard_sys
            try:
                return await _write_one_article(
                    async_client,
                    topic=topic,
                    batch_date=batch_date,
                    system_blocks=sys_blocks,
                )
            except Exception as e:
                log.error("Writer failed for %r: %s: %s",
                          topic.get("topic"), type(e).__name__, e)
                return {"_failed": True, "topic": topic, "error": str(e)}

    return await asyncio.gather(*[_bounded(t) for t in topics])


def run_phase3_parallel(
    *,
    topics: list[dict],
    batch_date: str,
    concurrency: int = 5,
) -> list[dict]:
    """Sync entry point for the async Phase 3."""
    log.info("Phase 3: %s articles in parallel (concurrency=%s)", len(topics), concurrency)
    return asyncio.run(_phase3_async(
        topics=topics, batch_date=batch_date, concurrency=concurrency
    ))


# ── Phase 4 — SEO Optimizer (quality gate) ─────────────────────────────────────

# Phase 4 schema: `final_*` fields are OPTIONAL. When verdict=pass, the
# optimizer omits them and we fall back to the Phase 3 article — no expensive
# regeneration of the full HTML when nothing needs fixing.
PHASE4_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "fix_and_pass", "reject"]},
        "issues_found": {"type": "array", "items": {"type": "string"}},
        "fixes_applied": {"type": "array", "items": {"type": "string"}},
        "fda_ftc_violations": {"type": "array", "items": {"type": "string"}},
        "geo_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Cumulative GEO/FDA/FTC compliance score.",
        },
        "final_title": {"type": ["string", "null"]},
        "final_seo_title": {"type": ["string", "null"]},
        "final_meta_description": {"type": ["string", "null"]},
        "final_body_html": {
            "type": ["string", "null"],
            "description": "Required only when verdict=fix_and_pass. Omit/null on pass or reject.",
        },
    },
    "required": [
        "verdict",
        "issues_found",
        "fixes_applied",
        "fda_ftc_violations",
        "geo_score",
    ],
    "additionalProperties": False,
}


# Phase 4 model: Sonnet by default (5x cheaper, fast enough for checklist
# review). Override with PHASE4_MODEL=claude-opus-4-7 for max rigor.
PHASE4_MODEL = os.environ.get("PHASE4_MODEL", MODEL_SONNET)


def _phase4_user_message(article: dict, batch_date: str) -> str:
    return (
        f"Review and (if necessary) fix this article. Apply ALL gates from "
        f"agents/04-seo-optimizer.md, especially the FDA / FTC compliance "
        f"hard gate.\n\n"
        f"## Article (Phase 3 output)\n"
        f"```json\n"
        f"{json.dumps(article, ensure_ascii=False, indent=2)}\n"
        f"```\n\n"
        f"Today's date: {batch_date}\n\n"
        f"Output rules:\n"
        f"- `verdict`: pass = no changes needed (omit final_* fields); "
        f"fix_and_pass = include final_body_html / final_title / "
        f"final_seo_title / final_meta_description with your fixes; "
        f"reject = article cannot be salvaged (disease claim, fabricated PMIDs).\n"
        f"- `fda_ftc_violations`: every disease claim, unsubstantiated "
        f"superlative, fabricated testimonial. Empty array if clean.\n"
        f"- `geo_score`: 0-100. <70 = reject.\n"
        f"- IMPORTANT: do NOT regenerate the body when verdict=pass. Saves cost."
    )


def _phase4_finalize(verdict: dict, article: dict) -> dict:
    """Fill missing final_* fields from the Phase 3 article when pass."""
    if not verdict.get("final_body_html"):
        verdict["final_body_html"] = article.get("body_html", "")
    if not verdict.get("final_title"):
        verdict["final_title"] = article.get("title", "")
    if not verdict.get("final_seo_title"):
        verdict["final_seo_title"] = article.get("seo_title", article.get("title", ""))
    if not verdict.get("final_meta_description"):
        verdict["final_meta_description"] = article.get("meta_description", "")
    return verdict


def run_phase4(*, article: dict, batch_date: str) -> dict:
    """Score and (if needed) fix one article. Returns the optimizer's verdict
    plus the final HTML / title / meta. Returns reject -> the article should
    not be saved as -final.html."""
    client = Anthropic()
    system = build_phase_system_blocks(["04-seo-optimizer.md"])

    log.info("Phase 4: gating %s", article.get("slug", "<no-slug>")[:50])
    with client.messages.stream(
        model=PHASE4_MODEL,
        max_tokens=32000,
        thinking=THINKING_ADAPTIVE,
        output_config={
            **EFFORT_HIGH,
            "format": {"type": "json_schema", "schema": PHASE4_VERDICT_SCHEMA},
        },
        system=system,
        messages=[{"role": "user", "content": _phase4_user_message(article, batch_date)}],
    ) as stream:
        msg = stream.get_final_message()

    text = next((b.text for b in msg.content if b.type == "text"), "")
    verdict = _phase4_finalize(json.loads(text), article)
    log.info(
        "  [%s] %s  score=%s issues=%s violations=%s",
        verdict["verdict"].upper(),
        article.get("slug", "")[:40],
        verdict["geo_score"],
        len(verdict["issues_found"]),
        len(verdict["fda_ftc_violations"]),
    )
    return verdict


async def _phase4_async_one(
    async_client: AsyncAnthropic,
    *,
    article: dict,
    batch_date: str,
    system_blocks: list[dict],
) -> dict:
    async with async_client.messages.stream(
        model=PHASE4_MODEL,
        max_tokens=32000,
        thinking=THINKING_ADAPTIVE,
        output_config={
            **EFFORT_HIGH,
            "format": {"type": "json_schema", "schema": PHASE4_VERDICT_SCHEMA},
        },
        system=system_blocks,
        messages=[{"role": "user", "content": _phase4_user_message(article, batch_date)}],
    ) as stream:
        msg = await stream.get_final_message()
    text = next((b.text for b in msg.content if b.type == "text"), "")
    verdict = _phase4_finalize(json.loads(text), article)
    log.info(
        "  [%s] %s  score=%s",
        verdict["verdict"].upper(),
        article.get("slug", "")[:40],
        verdict["geo_score"],
    )
    return verdict


async def _phase4_async(
    *,
    articles: list[dict],
    batch_date: str,
    concurrency: int = 5,
) -> list[dict | None]:
    async_client = AsyncAnthropic()
    system_blocks = build_phase_system_blocks(["04-seo-optimizer.md"])
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(art):
        async with sem:
            try:
                return await _phase4_async_one(
                    async_client,
                    article=art,
                    batch_date=batch_date,
                    system_blocks=system_blocks,
                )
            except Exception as e:
                log.error("Phase 4 failed for %s: %s: %s",
                          art.get("slug"), type(e).__name__, e)
                return None

    return await asyncio.gather(*[_bounded(a) for a in articles])


def run_phase4_parallel(
    *,
    articles: list[dict],
    batch_date: str,
    concurrency: int = 5,
) -> list[dict | None]:
    """Sync entry point — gates all articles in parallel. None on per-article failure."""
    log.info("Phase 4: gating %s articles in parallel (concurrency=%s, model=%s)",
             len(articles), concurrency, PHASE4_MODEL)
    return asyncio.run(_phase4_async(
        articles=articles, batch_date=batch_date, concurrency=concurrency
    ))


# ── Disk persistence ───────────────────────────────────────────────────────────

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _safe_slug(slug: str) -> str:
    s = _SLUG_RE.sub("-", (slug or "").lower()).strip("-")
    return s[:120] or "untitled"


def save_article_files(
    *,
    article: dict,
    verdict: dict,
    batch_date: str,
) -> tuple[str, str]:
    """Persist <slug>-final.html and <slug>.meta.json. Returns (html_path, meta_path)."""
    slug = _safe_slug(article["slug"])
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(verdict["final_body_html"])

    meta = {
        "slug": slug,
        "title": verdict["final_title"],
        "seo_title": verdict["final_seo_title"],
        "primary_keyword": article.get("primary_keyword"),
        "secondary_keywords": article.get("secondary_keywords") or [],
        "meta_description": verdict["final_meta_description"],
        "tags": article.get("tags") or [],
        "excerpt": article.get("excerpt"),
        "image_query": article.get("image_query"),
        "body_image_queries": article.get("body_image_queries") or [],
        "about": article.get("about") or [],
        "mentions": article.get("mentions") or [],
        "primary_topic": article.get("primary_topic"),
        "schema_type": article.get("schema_type", "MedicalWebPage"),
        "format": article.get("format", "standard"),
        "products_compared": article.get("products_compared"),
        "citations": article.get("citations") or [],
        "date_published": batch_date,
        "date_reviewed": batch_date,
        "date_modified": batch_date,
        "reviewer": "Dr. Daniel Yadegar, MD, FACC, RPVI",
        "reviewer_title": "Cardiologist & Longevity Physician",
        "reviewer_url": "https://happyaging.com/pages/dr-daniel-yadegar",
        "reviewer_sameAs": [
            "https://www.linkedin.com/in/daniel-yadegar-md-facc-rpvi-aa55a958/",
            "https://www.atria.org/doctors/dr-daniel-yadegar/",
            "https://lumos-pharma.com/company/daniel-yadegar-m-d/",
            "https://www.instagram.com/drdanyadegar/",
        ],
        "geo_score": verdict["geo_score"],
        "fda_ftc_violations_at_review": verdict["fda_ftc_violations"],
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return html_path, meta_path

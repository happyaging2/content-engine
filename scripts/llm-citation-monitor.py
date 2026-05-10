#!/usr/bin/env python3
"""
llm-citation-monitor.py — Track whether ChatGPT, Perplexity, and Google AI
Overviews are citing happyaging.com for our target queries.

Runs weekly. Output: LLM-CITATIONS.md (consumed by Phase 7 — Learning Injection).

Required env vars (skip the ones you don't have):
  PERPLEXITY_API_KEY    — sonar-pro citation tracking
  OPENAI_API_KEY        — ChatGPT search via responses API with web_search tool
  ANTHROPIC_API_KEY     — Claude with web_search_20250305
  SERPAPI_KEY           — Google AI Overviews via SerpAPI (engine=google_ai_overview)

Usage:
    python3 scripts/llm-citation-monitor.py [--queries queries.txt]

Default query list comes from the top performers in CONTENT-PERFORMANCE.md plus
the article titles in articles/*.meta.json.
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
OUT = os.path.join(ROOT, "LLM-CITATIONS.md")

PERPLEXITY = os.environ.get("PERPLEXITY_API_KEY", "").strip()
OPENAI = os.environ.get("OPENAI_API_KEY", "").strip()
ANTHROPIC = os.environ.get("ANTHROPIC_API_KEY", "").strip()
SERPAPI = os.environ.get("SERPAPI_KEY", "").strip()

DOMAIN = "happyaging.com"


def _post_json(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "body": e.read().decode("utf-8", "ignore")[:400]}
    except Exception as e:
        return {"error": str(e)}


def _get_json(url: str, timeout: int = 60) -> dict:
    try:
        return json.loads(urllib.request.urlopen(url, timeout=timeout).read())
    except Exception as e:
        return {"error": str(e)}


# ── Perplexity (Sonar) ─────────────────────────────────────────────────────
def query_perplexity(query: str) -> dict:
    if not PERPLEXITY:
        return {"skipped": "no PERPLEXITY_API_KEY"}
    body = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": query}],
        "return_citations": True,
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY}",
        "Content-Type": "application/json",
    }
    resp = _post_json("https://api.perplexity.ai/chat/completions", headers, body)
    citations = resp.get("citations") or []
    cited = [c for c in citations if DOMAIN in c]
    return {
        "engine": "perplexity",
        "query": query,
        "happyaging_cited": bool(cited),
        "happyaging_urls": cited,
        "all_citations": citations,
        "raw_error": resp.get("error"),
    }


# ── OpenAI (ChatGPT with web_search) ───────────────────────────────────────
def query_chatgpt(query: str) -> dict:
    if not OPENAI:
        return {"skipped": "no OPENAI_API_KEY"}
    body = {
        "model": "gpt-4o-search-preview",
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }
    headers = {
        "Authorization": f"Bearer {OPENAI}",
        "Content-Type": "application/json",
    }
    resp = _post_json("https://api.openai.com/v1/chat/completions", headers, body)
    text = ""
    annotations = []
    try:
        msg = resp["choices"][0]["message"]
        text = msg.get("content") or ""
        annotations = msg.get("annotations") or []
    except Exception:
        pass
    urls = [a.get("url_citation", {}).get("url") for a in annotations]
    urls = [u for u in urls if u]
    cited = [u for u in urls if DOMAIN in u]
    return {
        "engine": "chatgpt",
        "query": query,
        "happyaging_cited": bool(cited),
        "happyaging_urls": cited,
        "all_citations": urls,
        "raw_error": resp.get("error"),
    }


# ── Anthropic (Claude with web_search tool) ────────────────────────────────
def query_claude(query: str) -> dict:
    if not ANTHROPIC:
        return {"skipped": "no ANTHROPIC_API_KEY"}
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": query}],
    }
    headers = {
        "x-api-key": ANTHROPIC,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = _post_json("https://api.anthropic.com/v1/messages", headers, body)
    urls: list[str] = []
    try:
        for block in resp.get("content", []):
            if block.get("type") == "web_search_tool_result":
                for r in block.get("content", []):
                    if r.get("url"):
                        urls.append(r["url"])
            for cit in (block.get("citations") or []):
                if cit.get("url"):
                    urls.append(cit["url"])
    except Exception:
        pass
    cited = [u for u in urls if DOMAIN in u]
    return {
        "engine": "claude",
        "query": query,
        "happyaging_cited": bool(cited),
        "happyaging_urls": cited,
        "all_citations": urls,
        "raw_error": resp.get("error"),
    }


# ── Google AI Overviews via SerpAPI ────────────────────────────────────────
def query_google_aio(query: str) -> dict:
    if not SERPAPI:
        return {"skipped": "no SERPAPI_KEY"}
    qs = urllib.parse.urlencode(
        {"engine": "google", "q": query, "api_key": SERPAPI, "google_domain": "google.com", "gl": "us", "hl": "en"}
    )
    resp = _get_json("https://serpapi.com/search.json?" + qs)
    aio = resp.get("ai_overview") or {}
    refs = aio.get("references") or []
    urls = [r.get("link") for r in refs if r.get("link")]
    cited = [u for u in urls if DOMAIN in u]
    return {
        "engine": "google_ai_overview",
        "query": query,
        "happyaging_cited": bool(cited),
        "happyaging_urls": cited,
        "all_citations": urls,
        "raw_error": resp.get("error"),
    }


def load_queries(path: str | None) -> list[str]:
    if path and os.path.exists(path):
        return [q.strip() for q in open(path) if q.strip() and not q.startswith("#")]
    # Default: derive from top 30 article titles (sorted alphabetically — replace
    # with CONTENT-PERFORMANCE.md ranking once that's structured).
    qs = []
    for mf in sorted(glob.glob(os.path.join(ARTICLES, "*.meta.json")))[:50]:
        m = json.load(open(mf))
        title = m.get("title") or ""
        # Convert title to a natural query.
        q = re.sub(r"[?:.]", "", title).strip().lower()
        if q:
            qs.append(q)
    return qs


def main():
    queries_path = None
    if "--queries" in sys.argv:
        i = sys.argv.index("--queries")
        queries_path = sys.argv[i + 1]
    queries = load_queries(queries_path)
    print(f"Querying {len(queries)} prompts across 4 engines...\n")

    results = []
    for q in queries:
        for fn in (query_perplexity, query_chatgpt, query_claude, query_google_aio):
            r = fn(q)
            if r.get("skipped"):
                continue
            results.append(r)
            cited = "✓" if r["happyaging_cited"] else "✗"
            print(f"  {cited} [{r['engine']:18}] {q[:60]}")

    # Aggregate
    by_engine: dict[str, dict] = {}
    for r in results:
        e = r["engine"]
        by_engine.setdefault(e, {"queries": 0, "cited": 0, "urls": set()})
        by_engine[e]["queries"] += 1
        if r["happyaging_cited"]:
            by_engine[e]["cited"] += 1
            by_engine[e]["urls"].update(r["happyaging_urls"])

    today = dt.date.today().isoformat()
    lines = [
        f"# LLM Citation Monitor — {today}",
        "",
        f"Domain tracked: `{DOMAIN}`. Queries: {len(queries)}.",
        "",
        "## Citation rate by engine",
        "",
        "| Engine | Queries | Cited | Rate | Unique URLs cited |",
        "|---|---:|---:|---:|---:|",
    ]
    for e, d in sorted(by_engine.items()):
        rate = d["cited"] / d["queries"] if d["queries"] else 0
        lines.append(
            f"| {e} | {d['queries']} | {d['cited']} | {rate:.0%} | {len(d['urls'])} |"
        )

    lines += ["", "## Cited URLs", ""]
    for e, d in sorted(by_engine.items()):
        if d["urls"]:
            lines.append(f"### {e}")
            for u in sorted(d["urls"]):
                lines.append(f"- {u}")
            lines.append("")

    lines += ["", "## Misses (no citation, top 30)", ""]
    misses = [r for r in results if not r["happyaging_cited"]][:30]
    for r in misses:
        lines.append(f"- [{r['engine']}] {r['query']}")

    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

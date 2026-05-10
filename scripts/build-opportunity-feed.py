#!/usr/bin/env python3
"""
build-opportunity-feed.py — aggregate discovery sources into OPPORTUNITY-FEED.md.

Sources (all optional — runs with whatever it finds):
  - data/discovery/autocomplete-<date>.json   (long-tail Google Suggest)
  - data/discovery/paa-<date>.json            (People Also Ask boxes)
  - data/discovery/reddit-<date>.json         (real-language community questions)
  - data/discovery/competitors-<date>.json    (counter-article targets)

Output: OPPORTUNITY-FEED.md at repo root — consumed by Phase 1 (Opportunity
Engine) at the next batch run, alongside REFRESH-QUEUE / COMPARISON-QUEUE /
LLM-CITATIONS / COMPETITOR-GAP / CONTENT-PERFORMANCE.

Filters:
  - dedups against existing article slugs in articles/*.meta.json
  - drops candidates with <5 word title or off-topic seeds
  - tags each candidate with its priority cluster (when matchable)
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DISC = os.path.join(ROOT, "data", "discovery")
ARTICLES = os.path.join(ROOT, "articles")
OUT = os.path.join(ROOT, "OPPORTUNITY-FEED.md")

# Cluster classifier — order matters (first match wins).
CLUSTER_RULES = [
    ("nad-nmn", ("nmn", "nad+", "nad ", "sirtuin", "resveratrol", "longevity supplement")),
    ("bloating", ("bloat", "gas ", "ibs", "digestive", "abdominal")),
    ("glp-1", ("ozempic", "wegovy", "tirzepatide", "semaglutide", "mounjaro", "zepbound", "glp-1", "glp1")),
    ("hormonal", ("hormone", "perimenopause", "menopause", "cortisol", "thyroid", "estrogen", "progesterone")),
    ("sleep", ("sleep", "insomnia", "melatonin")),
    ("magnesium", ("magnesium", "glycinate", "citrate")),
    ("ashwagandha", ("ashwagandha", "ksm-66")),
    ("collagen-skin", ("collagen", "skin",)),
]


def _cluster(title: str) -> str:
    t = title.lower()
    for slug, needles in CLUSTER_RULES:
        if any(n in t for n in needles):
            return slug
    return "uncategorized"


def _existing_topics() -> set[str]:
    out: set[str] = set()
    for mf in glob.glob(os.path.join(ARTICLES, "*.meta.json")):
        try:
            m = json.load(open(mf))
            t = (m.get("title") or "").lower().strip()
            if t:
                out.add(t)
            slug = m.get("slug") or os.path.basename(mf).replace(".meta.json", "")
            out.add(slug.replace("-", " ").lower())
        except Exception:
            pass
    return out


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")[:100]


def _newest(prefix: str) -> str | None:
    files = sorted(glob.glob(os.path.join(DISC, f"{prefix}-*.json")))
    return files[-1] if files else None


def main() -> None:
    existing = _existing_topics()

    candidates: list[dict] = []

    # ── Autocomplete ──────────────────────────────────────────────────────
    f = _newest("autocomplete")
    if f:
        data = json.load(open(f))
        for seed, queries in (data.get("by_seed") or {}).items():
            for q in queries:
                if q.lower() not in existing and len(q.split()) >= 4:
                    candidates.append({
                        "title": q,
                        "source": "autocomplete",
                        "seed": seed,
                        "cluster": _cluster(q),
                    })

    # ── PAA ───────────────────────────────────────────────────────────────
    f = _newest("paa")
    if f:
        data = json.load(open(f))
        for seed, qs in (data.get("by_seed") or {}).items():
            for q in qs:
                if q.lower() not in existing and len(q.split()) >= 4:
                    candidates.append({
                        "title": q,
                        "source": "paa",
                        "seed": seed,
                        "cluster": _cluster(q),
                    })

    # ── Reddit ────────────────────────────────────────────────────────────
    f = _newest("reddit")
    if f:
        data = json.load(open(f))
        for sub, posts in (data.get("by_subreddit") or {}).items():
            for p in posts:
                title = p.get("title", "")
                if title.lower() not in existing and len(title.split()) >= 5:
                    candidates.append({
                        "title": title,
                        "source": f"reddit:r/{sub}",
                        "score": p.get("score"),
                        "comments": p.get("comments"),
                        "permalink": p.get("permalink"),
                        "cluster": _cluster(title),
                    })

    # ── Competitors (counter-article targets) ─────────────────────────────
    f = _newest("competitors")
    if f:
        data = json.load(open(f))
        for comp, items in (data.get("by_competitor") or {}).items():
            for it in items:
                title = it.get("title") or it.get("url", "")
                candidates.append({
                    "title": title,
                    "source": f"competitor:{comp}",
                    "url": it.get("url"),
                    "cluster": _cluster(title),
                    "counter_target": True,
                })

    # Dedup by lowercased title (keep richest source)
    by_title: dict[str, dict] = {}
    for c in candidates:
        k = c["title"].lower().strip()
        if k not in by_title:
            by_title[k] = c
    candidates = list(by_title.values())

    # Bucket by cluster
    by_cluster: dict[str, list[dict]] = {}
    for c in candidates:
        by_cluster.setdefault(c["cluster"], []).append(c)

    # ── Render Markdown ───────────────────────────────────────────────────
    today = dt.date.today().isoformat()
    out = [
        f"# Opportunity Feed — {today}",
        "",
        f"Aggregated from autocomplete, PAA, Reddit, and competitor sitemaps. "
        f"**{len(candidates)} candidates** across **{len(by_cluster)} clusters**. "
        f"Phase 1 (Opportunity Engine) reads this file as input alongside "
        f"REFRESH-QUEUE.md, COMPARISON-QUEUE.md, LLM-CITATIONS.md, COMPETITOR-GAP.md.",
        "",
        "**How to use:** prioritize counter-article targets (a competitor "
        "just published — first mover wins citations) + Reddit high-score "
        "questions (real-language signal, often pre-Google) + autocomplete/PAA "
        "for breadth.",
        "",
    ]

    cluster_priority = [
        "nad-nmn", "bloating", "glp-1", "hormonal",
        "sleep", "magnesium", "ashwagandha", "collagen-skin", "uncategorized",
    ]
    for cl in cluster_priority:
        items = by_cluster.get(cl) or []
        if not items:
            continue
        out.append(f"## {cl}  ({len(items)})")
        # Counter-targets first
        items.sort(key=lambda x: (
            0 if x.get("counter_target") else 1,
            -(x.get("score") or 0),
        ))
        for c in items[:50]:
            tag = ""
            if c.get("counter_target"):
                tag = "[counter-target] "
            elif c["source"].startswith("reddit"):
                tag = f"[{c['source'].split(':')[-1]}, score={c.get('score','?')}, comments={c.get('comments','?')}] "
            elif c["source"] == "paa":
                tag = "[PAA] "
            else:
                tag = "[autocomplete] "
            out.append(f"- {tag}{c['title']}  → suggested slug: `{_slug(c['title'])}`")
        out.append("")

    with open(OUT, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {OUT} — {len(candidates)} candidates across {len(by_cluster)} clusters")


if __name__ == "__main__":
    main()

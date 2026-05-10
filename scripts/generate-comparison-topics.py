#!/usr/bin/env python3
"""
generate-comparison-topics.py — Produces a queue of comparison topics
for Phase 1 to consume, derived from config/competitors.json.

For each cluster, generates the high-intent comparison query patterns:
  - "<Happy Aging product> vs <Competitor>"
  - "Best <category> brands for women over 40 (2026)"
  - "<Competitor 1> vs <Competitor 2>: which is better for <use case>"
  - "Is <Competitor> worth it? An evidence-based review"
  - "<Category> brands compared: form, dose, third-party testing"

Runs through scripts/check-duplicate-topics.py before output, so the queue
only contains topics not already covered.

Output: COMPARISON-QUEUE.md (Phase 1 reads this and reserves >=2 slots per
batch for comparisons — same convention as REFRESH-QUEUE.md).

Usage:
    python3 scripts/generate-comparison-topics.py
"""

from __future__ import annotations

import datetime as dt
import itertools
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "competitors.json")
OUT = os.path.join(ROOT, "COMPARISON-QUEUE.md")
DEDUP = os.path.join(ROOT, "scripts", "check-duplicate-topics.py")


def main():
    data = json.load(open(CONFIG))
    candidates: list[dict] = []
    today = dt.date.today().isoformat()

    for cluster_name, cluster in data["clusters"].items():
        ha = cluster.get("happyaging_product")
        comps = cluster.get("competitors", [])
        if not comps:
            continue

        # 1. HA vs each competitor
        if ha:
            for c in comps:
                candidates.append({
                    "topic": f"{ha['name']} vs {c['name']}",
                    "cluster": cluster_name,
                    "type": "ha-vs-competitor",
                    "intent": "comparison",
                    "products": [ha["name"], c["name"]],
                })

        # 2. Best-of list
        candidates.append({
            "topic": f"Best {cluster_name} supplements for women over 40 (2026): brands compared",
            "cluster": cluster_name,
            "type": "best-of",
            "intent": "comparison",
            "products": [c["name"] for c in comps] + ([ha["name"]] if ha else []),
        })

        # 3. Cross-competitor comparison (top-2 by alphabetical for deterministic output)
        for c1, c2 in itertools.combinations(comps[:3], 2):
            candidates.append({
                "topic": f"{c1['name']} vs {c2['name']}: which is better for women over 40",
                "cluster": cluster_name,
                "type": "competitor-vs-competitor",
                "intent": "comparison",
                "products": [c1["name"], c2["name"]],
            })

        # 4. Evidence review of single competitor
        for c in comps:
            candidates.append({
                "topic": f"Is {c['name']} worth it? An evidence-based review",
                "cluster": cluster_name,
                "type": "single-brand-review",
                "intent": "investigative",
                "products": [c["name"]],
            })

        # 5. Category landscape
        candidates.append({
            "topic": f"{cluster_name.title()} brands compared: form, dose, and third-party testing",
            "cluster": cluster_name,
            "type": "landscape",
            "intent": "informational",
            "products": [c["name"] for c in comps] + ([ha["name"]] if ha else []),
        })

    # Run dedup
    titles_only = [c["topic"] for c in candidates]
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tmp:
        tmp.write("\n".join(titles_only))
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["python3", DEDUP, tmp_path],
            check=False,
            capture_output=True,
            text=True,
        )
        kept_path = os.path.join(os.path.dirname(tmp_path), "kept.txt")
        rejected_path = os.path.join(os.path.dirname(tmp_path), "rejected.txt")
        kept_titles = set(
            l.strip() for l in open(kept_path).read().splitlines() if l.strip()
        ) if os.path.exists(kept_path) else set(titles_only)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    kept = [c for c in candidates if c["topic"] in kept_titles]
    rejected = [c for c in candidates if c["topic"] not in kept_titles]

    # Write COMPARISON-QUEUE.md
    lines = [
        f"# Comparison Queue — generated {today}",
        "",
        f"Total candidates: **{len(candidates)}** · Kept after dedup: **{len(kept)}** · Rejected: {len(rejected)}",
        "",
        "Phase 1 reserves >=2 slots per batch of 20 for comparison topics. ",
        "When picking, prioritize types in this order: `ha-vs-competitor` > ",
        "`landscape` > `best-of` > `competitor-vs-competitor` > `single-brand-review`.",
        "",
        "## Queue (kept)",
        "",
        "| Topic | Cluster | Type | Products |",
        "|---|---|---|---|",
    ]
    for c in kept:
        prods = ", ".join(c["products"])
        lines.append(f"| {c['topic']} | {c['cluster']} | {c['type']} | {prods} |")

    if rejected:
        lines += ["", "## Rejected (already covered)", ""]
        for c in rejected:
            lines.append(f"- ~~{c['topic']}~~  ·  {c['type']}")

    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {OUT} — {len(kept)} kept / {len(rejected)} rejected.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
check-duplicate-topics.py — Prevent the Opportunity Engine from picking topics
that overlap with already-published articles.

Run as Phase 1 pre-step. Reads candidate topics from a file (one per line) and
filters out anything that:
  1. Has a slug collision with an existing article (slug exact match)
  2. Has high token-overlap with an existing title (Jaccard >= 0.55)
  3. Shares the same `primary_topic` AND >=2 overlapping `about` entities with
     an article published in the last 180 days

Usage:
    python3 scripts/check-duplicate-topics.py candidates.txt
    # outputs: kept.txt + rejected.txt with reasons

Exit code is 0 even when duplicates are found — this is informational.
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")

if len(sys.argv) < 2:
    print("Usage: check-duplicate-topics.py <candidates.txt>")
    sys.exit(1)

CAND_FILE = sys.argv[1]
KEPT_FILE = os.path.join(os.path.dirname(CAND_FILE) or ".", "kept.txt")
REJECTED_FILE = os.path.join(os.path.dirname(CAND_FILE) or ".", "rejected.txt")

STOPWORDS = {
    "the", "a", "an", "for", "to", "of", "in", "and", "or", "with", "after",
    "before", "your", "you", "is", "are", "what", "how", "why", "vs", "best",
    "guide", "complete", "ultimate", "top", "women", "over",
}


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    s = re.sub(r"\s+", "-", s.strip())
    return re.sub(r"-+", "-", s)


def tokens(text: str) -> set[str]:
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return {t for t in text.split() if t and t not in STOPWORDS and len(t) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main():
    candidates = [
        l.strip() for l in open(CAND_FILE) if l.strip() and not l.startswith("#")
    ]

    existing = []
    today = dt.date.today()
    for mf in glob.glob(os.path.join(ARTICLES, "*.meta.json")):
        m = json.load(open(mf))
        slug = m.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title = m.get("title") or slug
        try:
            pub = dt.date.fromisoformat((m.get("date_published") or "")[:10])
        except Exception:
            pub = None
        existing.append(
            {
                "slug": slug,
                "title": title,
                "tokens": tokens(title),
                "about": set(map(str.lower, m.get("about") or [])),
                "primary_topic": (m.get("primary_topic") or "").lower(),
                "age_days": (today - pub).days if pub else None,
            }
        )

    kept, rejected = [], []
    for cand in candidates:
        cand_slug = slugify(cand)
        cand_tokens = tokens(cand)
        reason = None

        for e in existing:
            if e["slug"] == cand_slug or cand_slug in e["slug"] or e["slug"] in cand_slug:
                reason = f"slug collision with '{e['slug']}'"
                break
            jac = jaccard(cand_tokens, e["tokens"])
            if jac >= 0.55:
                reason = f"title overlap {jac:.0%} with '{e['title']}'"
                break
            shared_about = cand_tokens & e["about"]
            if (
                e["age_days"] is not None
                and e["age_days"] < 180
                and e["primary_topic"]
                and e["primary_topic"] in cand.lower()
                and len(shared_about) >= 2
            ):
                reason = (
                    f"same primary_topic + {len(shared_about)} entity overlap with "
                    f"recent article '{e['title']}' (age {e['age_days']}d)"
                )
                break

        if reason:
            rejected.append((cand, reason))
        else:
            kept.append(cand)

    with open(KEPT_FILE, "w") as f:
        f.write("\n".join(kept) + ("\n" if kept else ""))
    with open(REJECTED_FILE, "w") as f:
        for c, r in rejected:
            f.write(f"{c}\t# {r}\n")

    print(
        f"Candidates: {len(candidates)}  Kept: {len(kept)}  Rejected: {len(rejected)}"
    )
    print(f"  → {KEPT_FILE}")
    print(f"  → {REJECTED_FILE}")
    if rejected:
        print("\nSample rejections:")
        for c, r in rejected[:5]:
            print(f"  ✗ {c}\n    {r}")


if __name__ == "__main__":
    main()

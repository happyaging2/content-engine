#!/usr/bin/env python3
"""
discover-autocomplete.py — mine Google Suggest for long-tail opportunities.

Google's autocomplete endpoint is public, free, and exposes the actual queries
people are typing for any seed term. Expanding seeds with the alphabet (a-z)
typically yields 200-500 unique long-tail variants per seed.

Output: data/discovery/autocomplete-<date>.json
        + appended to OPPORTUNITY-FEED.md (via build-opportunity-feed.py)

Seeds come from docs/GEO-STRATEGY.md priority clusters. No API key required.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import string
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "discovery")
os.makedirs(OUT_DIR, exist_ok=True)

# Seed terms anchored to priority clusters (docs/GEO-STRATEGY.md).
# Edit to refocus discovery — every seed becomes 26 expansions (a-z) + 26
# question expansions ("how to {seed}", "best {seed}", etc.).
SEEDS = [
    # NAD+ / NMN cluster
    "nmn for women", "nad+ supplement women", "nad+ vs nmn",
    "best time to take nmn", "nmn side effects women",
    # Bloating cluster
    "bloating after 40", "bloating perimenopause", "hormonal bloating",
    "bloating after meals women", "supplements for bloating",
    # GLP-1 cluster
    "supplements on ozempic", "muscle loss on glp-1",
    "what to take with semaglutide", "energy on tirzepatide",
    "nutrition gaps glp-1",
    # Hormonal balance cluster
    "perimenopause supplements", "hormone balance after 35",
    "cortisol women 40", "thyroid support women",
    "hot flashes natural support",
    # Sleep / longevity / multi-system
    "sleep after 40 women", "magnesium glycinate women",
    "best longevity supplement women", "ashwagandha for women",
    "perimenopause anxiety natural",
]

QUESTION_PREFIXES = [
    "how to", "what is", "why does", "best", "top",
    "is", "can", "should i", "when to", "where to",
    "vs", "for", "without", "after",
]


def _suggest(query: str) -> list[str]:
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(
        {"client": "firefox", "q": query, "hl": "en", "gl": "us"}
    )
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (compatible; happy-aging-research)"}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=8).read())
        return data[1] if isinstance(data, list) and len(data) >= 2 else []
    except Exception as e:
        print(f"  fail '{query[:40]}': {str(e)[:50]}")
        return []


def main() -> None:
    out: dict[str, list[str]] = {}
    seen: set[str] = set()
    total = 0

    for seed in SEEDS:
        bucket: list[str] = []
        # Alphabet expansion
        for letter in string.ascii_lowercase:
            for variant in (f"{seed} {letter}", f"{letter} {seed}"):
                for s in _suggest(variant):
                    s_norm = s.lower().strip()
                    if s_norm and s_norm not in seen and len(s_norm) >= 12:
                        bucket.append(s)
                        seen.add(s_norm)
                time.sleep(0.15)
        # Question prefix expansion
        for prefix in QUESTION_PREFIXES:
            for s in _suggest(f"{prefix} {seed}"):
                s_norm = s.lower().strip()
                if s_norm and s_norm not in seen and len(s_norm) >= 12:
                    bucket.append(s)
                    seen.add(s_norm)
            time.sleep(0.15)

        out[seed] = sorted(set(bucket))
        total += len(out[seed])
        print(f"  {seed!r:50s} → {len(out[seed])} variants")

    today = dt.date.today().isoformat()
    path = os.path.join(OUT_DIR, f"autocomplete-{today}.json")
    with open(path, "w") as f:
        json.dump({"date": today, "total": total, "by_seed": out}, f, indent=2)
    print(f"\nWrote {path} — {total} unique long-tail queries from {len(SEEDS)} seeds")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
discover-paa.py — mine Google's "People Also Ask" boxes via SerpAPI.

PAA boxes are the literal questions Google believes are tightly related to a
query. Each PAA expansion typically reveals 4 NEW PAA questions when clicked,
forming a tree. We crawl 2 levels deep per seed.

Output: data/discovery/paa-<date>.json

Requires: SERPAPI_KEY (already used by llm-citation-monitor.py).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "discovery")
os.makedirs(OUT_DIR, exist_ok=True)

API_KEY = os.environ.get("SERPAPI_KEY", "")

# Cluster-anchored seeds for SERP scraping (paid endpoint — keep concise).
SEEDS = [
    "best supplement for bloating after 40",
    "what supplements to take on ozempic",
    "nmn vs nad for women",
    "perimenopause supplements that actually work",
    "magnesium glycinate vs citrate women",
    "happy aging vs ag1",
    "happy aging vs grüns",
    "happy aging vs happy mammoth",
    "what to take while on glp-1",
    "best longevity supplement for women over 40",
]


def _serpapi(query: str) -> dict:
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(
        {"q": query, "engine": "google", "hl": "en", "gl": "us", "api_key": API_KEY}
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "happy-aging-research/1.0"}
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())


def main() -> None:
    if not API_KEY:
        raise SystemExit("ERROR: SERPAPI_KEY not set")

    by_seed: dict[str, list[str]] = {}
    seen: set[str] = set()

    for seed in SEEDS:
        questions: list[str] = []
        try:
            data = _serpapi(seed)
        except Exception as e:
            print(f"  serpapi fail '{seed[:40]}': {str(e)[:60]}")
            continue
        for item in (data.get("related_questions") or []):
            q = (item.get("question") or "").strip()
            if q and q.lower() not in seen and len(q) >= 12:
                questions.append(q)
                seen.add(q.lower())
        # Level-2 expansion: fetch PAA for each top-level PAA (capped to 3
        # to limit cost — SerpAPI charges per request)
        for q in questions[:3]:
            try:
                sub = _serpapi(q)
            except Exception:
                continue
            for item in (sub.get("related_questions") or []):
                q2 = (item.get("question") or "").strip()
                if q2 and q2.lower() not in seen and len(q2) >= 12:
                    questions.append(q2)
                    seen.add(q2.lower())
            time.sleep(0.5)
        by_seed[seed] = questions
        print(f"  {seed!r:55s} → {len(questions)} PAA questions")
        time.sleep(0.5)

    today = dt.date.today().isoformat()
    path = os.path.join(OUT_DIR, f"paa-{today}.json")
    with open(path, "w") as f:
        json.dump(
            {"date": today, "total": len(seen), "by_seed": by_seed},
            f, indent=2,
        )
    print(f"\nWrote {path} — {len(seen)} unique PAA questions")


if __name__ == "__main__":
    main()

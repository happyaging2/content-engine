#!/usr/bin/env python3
"""
discover-reddit.py — mine Reddit search for real-language questions.

Why Reddit: AI Overviews increasingly cite Reddit threads. Reddit captures
the literal phrasing women use BEFORE Google query rewriting. A topic that
trends on r/Perimenopause this week often hits Google AI Overviews next month.

We hit Reddit's public JSON search endpoint (no auth) per subreddit + seed,
sort by `top` past month, and extract titles that look like questions.

Output: data/discovery/reddit-<date>.json
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

# Subreddits with our target audience.
SUBREDDITS = [
    "Perimenopause", "Menopause", "Menopause_Support",
    "Longevity", "Biohackers", "supplements",
    "loseit",          # GLP-1 questions surface here heavily
    "TirzepatideCompound",
    "Semaglutide",
    "WomensHealth",
    "TwoXChromosomes",  # general women-35+ questions
    "ScienceBasedParenting",  # adjacent — hormonal questions post-pregnancy
]

# Search seeds within those subs.
SEEDS = [
    "supplement", "bloating", "perimenopause", "hot flashes",
    "ozempic energy", "muscle loss",
    "nmn", "nad", "longevity", "magnesium",
    "ashwagandha", "cortisol", "thyroid",
    "weight loss women 40", "sleep women",
]

QUESTION_MARKERS = (
    "?", "how ", "why ", "what ", "is ", "should ", "anyone ",
    "does ", "can ", "advice", "help", "experience",
)


def _is_question(title: str) -> bool:
    t = (title or "").lower().strip()
    return any(m in t for m in QUESTION_MARKERS)


def _search(subreddit: str, query: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/search.json?" + urllib.parse.urlencode(
        {"q": query, "restrict_sr": 1, "sort": "top", "t": "month", "limit": 25}
    )
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "happy-aging-research/1.0 (research bot)"}
        )
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return [c["data"] for c in (data.get("data", {}).get("children") or [])]
    except Exception as e:
        print(f"  fail r/{subreddit} '{query}': {str(e)[:60]}")
        return []


def main() -> None:
    by_sub: dict[str, list[dict]] = {}
    seen_titles: set[str] = set()
    total_q = 0

    for sub in SUBREDDITS:
        bucket: list[dict] = []
        for seed in SEEDS:
            posts = _search(sub, seed)
            for p in posts:
                title = (p.get("title") or "").strip()
                if (
                    title
                    and title.lower() not in seen_titles
                    and _is_question(title)
                    and len(title) >= 20
                    and (p.get("score") or 0) >= 10
                ):
                    bucket.append({
                        "title": title,
                        "score": p.get("score"),
                        "comments": p.get("num_comments"),
                        "permalink": "https://www.reddit.com" + (p.get("permalink") or ""),
                        "seed": seed,
                    })
                    seen_titles.add(title.lower())
            time.sleep(1.5)  # respect Reddit rate limit
        by_sub[sub] = sorted(bucket, key=lambda x: -(x.get("score") or 0))[:50]
        total_q += len(by_sub[sub])
        print(f"  r/{sub:30s} → {len(by_sub[sub])} question posts")

    today = dt.date.today().isoformat()
    path = os.path.join(OUT_DIR, f"reddit-{today}.json")
    with open(path, "w") as f:
        json.dump({"date": today, "total": total_q, "by_subreddit": by_sub}, f, indent=2)
    print(f"\nWrote {path} — {total_q} ranked question posts across {len(SUBREDDITS)} subs")


if __name__ == "__main__":
    main()

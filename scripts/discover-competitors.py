#!/usr/bin/env python3
"""
discover-competitors.py — monitor competitor sitemaps and RSS for new posts.

Strategy: when a major competitor publishes a post, we want to know within 24h
so Phase 1 can decide whether to publish a counter-article. AI search updates
faster than SEO — first mover on a topic gets the citation for weeks.

We poll each competitor's sitemap (or /blog RSS) and diff against last run.
New URLs are appended to OPPORTUNITY-FEED.md as `[counter-target]` rows.

Output: data/discovery/competitors-<date>.json
        data/discovery/_competitor-seen.json (state for diff)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "discovery")
os.makedirs(OUT_DIR, exist_ok=True)
STATE_FILE = os.path.join(OUT_DIR, "_competitor-seen.json")

# Competitors to monitor. `kind` is `sitemap` (XML) or `rss` (RSS feed).
# Each Shopify-hosted brand exposes /sitemap_blogs_1.xml — we use that
# directly because it's faster than RSS for recent posts.
COMPETITORS = [
    {"name": "Happy Mammoth", "url": "https://www.happymammoth.com/blogs/library.atom", "kind": "rss"},
    {"name": "AG1 (Athletic Greens)", "url": "https://drinkag1.com/sitemap.xml", "kind": "sitemap"},
    {"name": "Grüns", "url": "https://www.gruns.co/sitemap.xml", "kind": "sitemap"},
    {"name": "Pendulum", "url": "https://pendulumlife.com/sitemap.xml", "kind": "sitemap"},
    {"name": "Tru Niagen", "url": "https://www.truniagen.com/sitemap.xml", "kind": "sitemap"},
    {"name": "Wonderfeel", "url": "https://wonderfeel.com/sitemap.xml", "kind": "sitemap"},
    {"name": "Lemme", "url": "https://www.lemmelive.com/sitemap.xml", "kind": "sitemap"},
    {"name": "O Positiv", "url": "https://opositiv.com/sitemap.xml", "kind": "sitemap"},
    {"name": "Hum Nutrition", "url": "https://www.humnutrition.com/blogs/the-wellnest.atom", "kind": "rss"},
    {"name": "Arrae", "url": "https://arrae.com/blogs/news.atom", "kind": "rss"},
]

UA = {"User-Agent": "Mozilla/5.0 (compatible; happy-aging-research/1.0)"}


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")


def _extract(content: str, kind: str) -> list[dict]:
    if kind == "sitemap":
        # Pull <loc> entries; filter for blog-y URLs
        urls = re.findall(r"<loc>([^<]+)</loc>", content)
        out = []
        for u in urls:
            if any(seg in u.lower() for seg in ("/blog", "/article", "/journal", "/learn", "/posts", "/news")):
                out.append({"url": u, "title": ""})
        return out
    if kind == "rss":
        # Atom feed
        items = re.findall(
            r"<entry>(.*?)</entry>", content, re.DOTALL | re.IGNORECASE,
        ) or re.findall(r"<item>(.*?)</item>", content, re.DOTALL | re.IGNORECASE)
        out = []
        for it in items:
            link_m = re.search(r'<link[^>]*href="([^"]+)"', it) or re.search(r"<link[^>]*>([^<]+)</link>", it)
            title_m = re.search(r"<title[^>]*>(.*?)</title>", it, re.DOTALL | re.IGNORECASE)
            if link_m:
                out.append({
                    "url": link_m.group(1).strip(),
                    "title": re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else "",
                })
        return out
    return []


def main() -> None:
    seen: dict[str, list[str]] = {}
    if os.path.exists(STATE_FILE):
        seen = json.load(open(STATE_FILE))

    today_new: dict[str, list[dict]] = {}
    total_new = 0

    for comp in COMPETITORS:
        try:
            content = _fetch(comp["url"])
        except Exception as e:
            print(f"  {comp['name']:25s} fetch fail: {str(e)[:60]}")
            continue
        items = _extract(content, comp["kind"])
        prior = set(seen.get(comp["name"], []))
        new = [it for it in items if it["url"] not in prior]
        seen[comp["name"]] = sorted(set(prior | {it["url"] for it in items}))
        if new:
            today_new[comp["name"]] = new
            total_new += len(new)
        print(f"  {comp['name']:25s} → {len(new)} new posts (of {len(items)} indexed)")
        time.sleep(1.0)

    # Persist state
    with open(STATE_FILE, "w") as f:
        json.dump(seen, f, indent=2)

    today = dt.date.today().isoformat()
    path = os.path.join(OUT_DIR, f"competitors-{today}.json")
    with open(path, "w") as f:
        json.dump({"date": today, "total_new": total_new, "by_competitor": today_new}, f, indent=2)
    print(f"\nWrote {path} — {total_new} new competitor posts since last run")


if __name__ == "__main__":
    main()

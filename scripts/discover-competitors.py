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

# Heuristics for filtering article URLs out of a sitemap. Tightened to exclude
# product / collection / cart / search pages from Shopify-style sitemaps.
ARTICLE_PATH_HINTS = ("/blog", "/article", "/journal", "/learn", "/posts", "/news")
NON_ARTICLE_PATH_HINTS = (
    "/products/", "/collections/", "/cart", "/search",
    "/policies/", "/account", "/checkout",
)


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")


def _is_sitemap_index(content: str) -> bool:
    """A sitemap index has <sitemapindex> as root element instead of <urlset>."""
    return "<sitemapindex" in content[:400].lower()


def _expand_sitemap(url: str, depth: int = 0, max_depth: int = 3) -> list[str]:
    """Return a flat list of leaf <loc> URLs from a sitemap, recursing into
    sitemap-index documents and into <loc> entries that point at .xml files.
    Prevents the index-only bug where /sitemap.xml never reveals child posts."""
    if depth > max_depth:
        return []
    try:
        content = _fetch(url)
    except Exception as e:
        print(f"    expand fail {url}: {str(e)[:60]}")
        return []
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", content)
    if not locs:
        return []
    if _is_sitemap_index(content) or any(loc.lower().endswith(".xml") or "/sitemap" in loc.lower() for loc in locs[:5]):
        # Recurse into child sitemaps. Cap to first 8 children to avoid
        # exploding on giant Shopify catalogs.
        out: list[str] = []
        for child in locs[:8]:
            if child.lower().endswith(".xml") or "/sitemap" in child.lower():
                out.extend(_expand_sitemap(child, depth=depth + 1, max_depth=max_depth))
                time.sleep(0.4)
            else:
                out.append(child)
        return out
    return locs


def _extract(content: str, kind: str, source_url: str = "") -> list[dict]:
    if kind == "sitemap":
        # Recursively walk sitemap indexes to leaf URLs, then filter for
        # blog-y paths and exclude product/collection/policy paths.
        urls = _expand_sitemap(source_url) if source_url else re.findall(r"<loc>([^<]+)</loc>", content)
        out: list[dict] = []
        for u in urls:
            ul = u.lower()
            if any(seg in ul for seg in NON_ARTICLE_PATH_HINTS):
                continue
            if any(seg in ul for seg in ARTICLE_PATH_HINTS):
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
        items = _extract(content, comp["kind"], source_url=comp["url"])
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

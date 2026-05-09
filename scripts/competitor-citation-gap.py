#!/usr/bin/env python3
"""
competitor-citation-gap.py — Phase 1 input: for each candidate query, see who's
currently being cited by Perplexity / ChatGPT / Google AI Overviews. Score the
opportunity gap (low-authority sites cited = high opportunity).

Output: COMPETITOR-GAP.md — markdown report ranked by opportunity score.

Required env: PERPLEXITY_API_KEY (mandatory — primary signal).
Optional:     OPENAI_API_KEY, SERPAPI_KEY (for ChatGPT and AI Overviews).

Usage:
    python3 scripts/competitor-citation-gap.py candidates.txt
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "COMPETITOR-GAP.md")

PERPLEXITY = os.environ.get("PERPLEXITY_API_KEY", "").strip()
OPENAI = os.environ.get("OPENAI_API_KEY", "").strip()
SERPAPI = os.environ.get("SERPAPI_KEY", "").strip()

if not (PERPLEXITY or OPENAI or SERPAPI):
    raise SystemExit("ERROR: set at least one of PERPLEXITY_API_KEY, OPENAI_API_KEY, SERPAPI_KEY")

# Authority tiers — lower number = stronger competitor (harder to displace).
HIGH_AUTHORITY = {
    "mayoclinic.org", "clevelandclinic.org", "nih.gov", "ncbi.nlm.nih.gov",
    "harvard.edu", "webmd.com", "healthline.com", "medicalnewstoday.com",
    "wikipedia.org", "menopause.org", "acog.org",
}
MID_AUTHORITY = {
    "verywellhealth.com", "everydayhealth.com", "self.com", "prevention.com",
    "shape.com", "womenshealthmag.com", "drhyman.com", "drberg.com",
}


def _post(url, headers, body, timeout=60):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except Exception as e:
        return {"error": str(e)}


def _domain(u: str) -> str:
    m = re.match(r"https?://([^/]+)/?", u or "")
    if not m:
        return ""
    d = m.group(1).lower()
    if d.startswith("www."):
        d = d[4:]
    return d


def perplexity_citations(query: str) -> list[str]:
    if not PERPLEXITY:
        return []
    body = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": query}],
        "return_citations": True,
    }
    headers = {"Authorization": f"Bearer {PERPLEXITY}", "Content-Type": "application/json"}
    resp = _post("https://api.perplexity.ai/chat/completions", headers, body)
    return resp.get("citations") or []


def chatgpt_citations(query: str) -> list[str]:
    if not OPENAI:
        return []
    body = {
        "model": "gpt-4o-search-preview",
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }
    headers = {"Authorization": f"Bearer {OPENAI}", "Content-Type": "application/json"}
    resp = _post("https://api.openai.com/v1/chat/completions", headers, body)
    try:
        annot = resp["choices"][0]["message"].get("annotations") or []
        return [a["url_citation"]["url"] for a in annot if a.get("url_citation")]
    except Exception:
        return []


def aio_citations(query: str) -> list[str]:
    if not SERPAPI:
        return []
    qs = urllib.parse.urlencode(
        {"engine": "google", "q": query, "api_key": SERPAPI, "gl": "us", "hl": "en"}
    )
    try:
        resp = json.loads(
            urllib.request.urlopen("https://serpapi.com/search.json?" + qs, timeout=30).read()
        )
    except Exception:
        return []
    refs = (resp.get("ai_overview") or {}).get("references") or []
    return [r.get("link") for r in refs if r.get("link")]


def opportunity_score(domains: list[str]) -> int:
    """0-100. Lower-authority competitors → higher opportunity."""
    if not domains:
        return 90  # nobody cited — green field
    high = sum(1 for d in domains if d in HIGH_AUTHORITY)
    mid = sum(1 for d in domains if d in MID_AUTHORITY)
    low = len(domains) - high - mid
    # Heuristic: weighted average where high = 0 score, mid = 50, low = 90
    raw = (high * 5 + mid * 50 + low * 90) / max(len(domains), 1)
    return int(raw)


def main():
    if len(sys.argv) < 2:
        print("Usage: competitor-citation-gap.py <candidates.txt>")
        sys.exit(1)
    candidates = [
        l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")
    ]

    rows = []
    for q in candidates:
        all_urls = []
        all_urls += perplexity_citations(q)
        all_urls += chatgpt_citations(q)
        all_urls += aio_citations(q)
        domains = [_domain(u) for u in all_urls if u]
        domains = [d for d in domains if d]
        score = opportunity_score(domains)
        rows.append(
            {
                "query": q,
                "n_citations": len(domains),
                "domains": sorted(set(domains)),
                "opportunity": score,
            }
        )
        print(f"  {score:3d}  {q[:60]}  ({len(domains)} citations)")

    rows.sort(key=lambda r: -r["opportunity"])

    lines = [
        "# Competitor Citation Gap",
        "",
        "Higher score = better opportunity (fewer / weaker competitors currently cited).",
        "Authority tiers: high (Mayo, NIH, Healthline...), mid (VerywellHealth, Prevention...), low (everything else).",
        "",
        "| Score | Query | Citations | Top domains |",
        "|---:|---|---:|---|",
    ]
    for r in rows:
        top = ", ".join(r["domains"][:5]) or "(none)"
        lines.append(f"| {r['opportunity']} | {r['query']} | {r['n_citations']} | {top} |")

    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

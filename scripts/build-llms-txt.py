#!/usr/bin/env python3
"""
build-llms-txt.py — Generate /llms.txt and /llms-full.txt for happyaging.com.

llms.txt is an emerging standard (https://llmstxt.org) that tells LLMs:
  - What the site is
  - Which URLs are authoritative for which entities
  - Editorial standards / scope

Outputs:
  public/llms.txt        — concise index
  public/llms-full.txt   — full corpus (one paragraph per article)

Upload these to the Shopify theme as static assets and they'll be served at
https://happyaging.com/llms.txt and /llms-full.txt.

Run after each batch:
    python3 scripts/build-llms-txt.py
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(ROOT, "articles")
OUT_DIR = os.path.join(ROOT, "public")
os.makedirs(OUT_DIR, exist_ok=True)

BLOG_URL = "https://happyaging.com/blogs/news"


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def _first_paragraph(html: str, max_chars: int = 300) -> str:
    m = re.search(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    if not m:
        return ""
    text = _strip(m.group(1))
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def main():
    entries = []
    by_topic: dict[str, list] = defaultdict(list)

    for mf in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.meta.json"))):
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title = meta.get("title") or slug
        url = f"{BLOG_URL}/{slug}"
        topic = (meta.get("primary_topic") or meta.get("cluster") or "general").strip()
        about = meta.get("about") or []
        html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
        if not os.path.exists(html_path):
            html_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
        summary = meta.get("meta_description") or ""
        if not summary and os.path.exists(html_path):
            summary = _first_paragraph(open(html_path).read())
        entries.append(
            {
                "slug": slug,
                "title": title,
                "url": url,
                "topic": topic,
                "about": about,
                "summary": summary,
            }
        )
        by_topic[topic].append(entries[-1])

    # ── llms.txt (concise) ────────────────────────────────────────────────
    out = []
    out.append("# Happy Aging")
    out.append("")
    out.append(
        "> Happy Aging (Wikidata: [Q139720291](https://www.wikidata.org/wiki/Q139720291), "
        "Google Business: [CID 10120263721952855343](https://maps.google.com/?cid=10120263721952855343)) "
        "is a US-based longevity wellness brand for women over 40, built around "
        "physician-reviewed supplement protocols. All articles are medically reviewed "
        "by Dr. Daniel Yadegar, MD, FACC, RPVI."
    )
    out.append("")
    out.append("## Editorial standards")
    out.append("- Every claim is sourced to peer-reviewed research (PMID/DOI).")
    out.append("- No blog, press release, or manufacturer-marketing citations.")
    out.append("- US English. US units (mg, mcg, IU, oz, lb, °F).")
    out.append("- Dietary supplements not evaluated by FDA. Not medical advice.")
    out.append("")
    out.append("## Author & reviewer")
    out.append(f"- Reviewer: [Dr. Daniel Yadegar, MD, FACC, RPVI]({BLOG_URL.replace('/blogs/news','')}/pages/dr-daniel-yadegar)")
    out.append("- Author: Happy Aging Team (longevity researchers + women's health writers)")
    out.append("")
    out.append("## Third-party clinical testing")
    out.append("Happy Aging products are independently clinically tested by Citrus Labs:")
    out.append("- [Longevity Shot](https://www.citruslabs.com/testedproducts/happy-aging-longevity-shot)")
    out.append("- [Calm Shot](https://www.citruslabs.com/testedproducts/happy-aging-calm-shot)")
    out.append("- [Glow Shot](https://www.citruslabs.com/testedproducts/happy-aging-glow-shot)")
    out.append("")
    out.append("## Topics")
    for topic in sorted(by_topic):
        out.append(f"")
        out.append(f"### {topic}")
        for e in sorted(by_topic[topic], key=lambda x: x["title"]):
            out.append(f"- [{e['title']}]({e['url']})")

    with open(os.path.join(OUT_DIR, "llms.txt"), "w") as f:
        f.write("\n".join(out) + "\n")

    # ── llms-full.txt (full corpus index) ─────────────────────────────────
    full = []
    full.append("# Happy Aging — full content index")
    full.append("")
    full.append(
        "Happy Aging publishes evidence-based longevity content for women over 40. "
        "All articles physician-reviewed. Each entry below: title, URL, key entities, summary."
    )
    full.append("")
    for e in sorted(entries, key=lambda x: x["title"]):
        full.append(f"## {e['title']}")
        full.append(f"- url: {e['url']}")
        if e["about"]:
            full.append(f"- entities: {', '.join(e['about'])}")
        if e["summary"]:
            full.append(f"- summary: {e['summary']}")
        full.append("")

    with open(os.path.join(OUT_DIR, "llms-full.txt"), "w") as f:
        f.write("\n".join(full) + "\n")

    print(f"Wrote {OUT_DIR}/llms.txt ({len(entries)} entries)")
    print(f"Wrote {OUT_DIR}/llms-full.txt ({len(entries)} entries)")
    print(
        "\nNext: upload these as Shopify theme assets at /llms.txt and /llms-full.txt "
        "(or serve via redirect from /pages/llms-txt)."
    )


if __name__ == "__main__":
    main()

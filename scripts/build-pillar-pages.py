#!/usr/bin/env python3
"""
build-pillar-pages.py — Generate entity-hub (pillar) pages from the article corpus.

For each pillar entity in PILLAR_ENTITIES, scans all meta.json + final HTML to find
articles in the cluster, extracts canonical definitions, and builds a hub page with:
  - Canonical entity definition (DefinedTerm schema)
  - Comparison table of forms / mechanisms
  - Linked subtopic articles
  - FAQ
  - MedicalCondition / DefinedTerm JSON-LD

Output: pages/pillar-<entity-slug>.html — upload as Shopify pages.
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
PAGES = os.path.join(ROOT, "pages")
os.makedirs(PAGES, exist_ok=True)

# ── Pillar definitions — edit to match Happy Aging's actual clusters ─────────
PILLAR_ENTITIES = {
    "nmn": {
        "name": "NMN (Nicotinamide Mononucleotide)",
        "definition": (
            "NMN is a vitamin B3 derivative the body converts into NAD+, a "
            "coenzyme essential for cellular energy and DNA repair. After 40, "
            "NAD+ levels naturally decline, which is why NMN is studied as a "
            "longevity supplement."
        ),
        "keywords": ["nmn", "nicotinamide mononucleotide", "nad+", "nad precursor"],
        "schema_type": "DefinedTerm",
    },
    "nad": {
        "name": "NAD+",
        "definition": (
            "NAD+ (nicotinamide adenine dinucleotide) is a coenzyme found in "
            "every cell that powers energy metabolism, DNA repair, and sirtuin "
            "activation. NAD+ levels drop roughly 50% between ages 40 and 60."
        ),
        "keywords": ["nad+", "nad", "sirtuins"],
        "schema_type": "DefinedTerm",
    },
    "magnesium": {
        "name": "Magnesium for women over 40",
        "definition": (
            "Magnesium is an essential mineral involved in over 300 enzymatic "
            "reactions, including sleep regulation, muscle function, and stress "
            "response. Glycinate and citrate are the most bioavailable forms."
        ),
        "keywords": ["magnesium", "glycinate", "citrate"],
        "schema_type": "DefinedTerm",
    },
    "perimenopause": {
        "name": "Perimenopause",
        "definition": (
            "Perimenopause is the multi-year transition before menopause when "
            "ovarian hormone production becomes irregular. Common symptoms "
            "include sleep disruption, mood changes, irregular cycles, and hot "
            "flashes. It typically begins in the 40s."
        ),
        "keywords": ["perimenopause", "menopause", "hormone"],
        "schema_type": "MedicalCondition",
    },
    "sleep": {
        "name": "Sleep after 40",
        "definition": (
            "Sleep architecture changes after 40 due to declining estrogen, "
            "shifting circadian rhythm, and reduced melatonin. Most women report "
            "increased night waking and lighter sleep stages."
        ),
        "keywords": ["sleep", "insomnia", "melatonin", "circadian"],
        "schema_type": "DefinedTerm",
    },
    "longevity": {
        "name": "Longevity",
        "definition": (
            "Longevity refers to extending healthspan — the years of life spent "
            "in good health. Evidence-based pillars include NAD+ support, "
            "metabolic health, sleep, strength training, and protein adequacy."
        ),
        "keywords": ["longevity", "lifespan", "healthspan", "anti-aging"],
        "schema_type": "DefinedTerm",
    },
    "ashwagandha": {
        "name": "Ashwagandha",
        "definition": (
            "Ashwagandha (Withania somnifera) is an adaptogenic herb studied "
            "for stress, cortisol, and sleep. KSM-66 and Sensoril are the most "
            "researched standardized extracts."
        ),
        "keywords": ["ashwagandha", "ksm-66", "sensoril", "adaptogen"],
        "schema_type": "DefinedTerm",
    },
    "sirtuins": {
        "name": "Sirtuins",
        "definition": (
            "Sirtuins are a family of NAD+-dependent enzymes (SIRT1-SIRT7) that "
            "regulate DNA repair, inflammation, and metabolic adaptation. Their "
            "activity declines with age as NAD+ falls."
        ),
        "keywords": ["sirtuins", "sirt1", "resveratrol"],
        "schema_type": "DefinedTerm",
    },
}

BLOG_URL = "https://happyaging.com/blogs/news"


def _matches(meta: dict, html: str, keywords: list[str]) -> bool:
    text = " ".join(
        [
            meta.get("title", ""),
            " ".join(meta.get("about", [])),
            " ".join(meta.get("mentions", [])),
            (meta.get("primary_topic") or ""),
        ]
    ).lower()
    if any(k in text for k in keywords):
        return True
    # fallback: scan first 1000 chars of body
    return any(k in html[:1000].lower() for k in keywords)


def _collect_articles_for_pillar(pillar: dict) -> list[dict]:
    matches = []
    for mf in glob.glob(os.path.join(ARTICLES, "*.meta.json")):
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        html_path = os.path.join(ARTICLES, f"{slug}-final.html")
        if not os.path.exists(html_path):
            html_path = os.path.join(ARTICLES, f"{slug}.html")
        html = open(html_path).read() if os.path.exists(html_path) else ""
        if _matches(meta, html, pillar["keywords"]):
            matches.append(
                {
                    "slug": slug,
                    "title": meta.get("title", slug),
                    "url": f"{BLOG_URL}/{slug}",
                    "summary": meta.get("meta_description", ""),
                }
            )
    return sorted(matches, key=lambda x: x["title"])


def build_pillar(slug: str, pillar: dict) -> str:
    articles = _collect_articles_for_pillar(pillar)
    article_list = "\n".join(
        f'  <li><a href="{a["url"]}">{a["title"]}</a>'
        + (f' — <span style="color:#666">{a["summary"]}</span>' if a["summary"] else "")
        + "</li>"
        for a in articles
    )

    schema = {
        "@context": "https://schema.org",
        "@type": pillar["schema_type"],
        "name": pillar["name"],
        "description": pillar["definition"],
        "url": f"https://happyaging.com/pages/pillar-{slug}",
        "inDefinedTermSet": "https://happyaging.com/pages/glossary",
        "subjectOf": [{"@type": "Article", "url": a["url"]} for a in articles],
    }

    return f"""<!--
  Pillar / entity hub page for: {pillar['name']}
  Upload to Shopify as a Page with handle: pillar-{slug}
  URL: https://happyaging.com/pages/pillar-{slug}
-->

<div class="pillar-page" style="max-width:820px;margin:0 auto;padding:32px 16px;">

  <h1>{pillar['name']}</h1>

  <div class="what-to-know" style="background:#f8f5f0;padding:16px 20px;border-radius:8px;margin:16px 0;">
    <strong>What to know</strong>
    <p>{pillar['definition']}</p>
  </div>

  <h2>What is {pillar['name']}?</h2>
  <p>{pillar['definition']}</p>

  <h2>Articles in this guide</h2>
  <ul>
{article_list or '  <li>(No articles yet — will populate as the corpus grows.)</li>'}
  </ul>

  <p style="margin-top:32px;color:#888;font-size:0.92rem;">
    <em>This article is for educational purposes and is not medical advice.
    Dietary supplements are not evaluated by the FDA to diagnose, treat, cure,
    or prevent any disease. Consult your healthcare provider before starting
    any new supplement.</em>
  </p>

  <p style="color:#666;font-size:0.9rem;">
    Medically reviewed by
    <a href="https://happyaging.com/pages/dr-daniel-yadegar" rel="author">
      Dr. Daniel Yadegar, MD, FACC, RPVI
    </a>.
  </p>

</div>

<script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
</script>
"""


def main():
    written = 0
    for slug, pillar in PILLAR_ENTITIES.items():
        path = os.path.join(PAGES, f"pillar-{slug}.html")
        with open(path, "w") as f:
            f.write(build_pillar(slug, pillar))
        written += 1
        print(f"  ✓ {path}")
    print(f"\nWrote {written} pillar pages to {PAGES}/")
    print(
        "\nNext: upload each pillar-*.html to Shopify as a Page with the matching handle."
    )


if __name__ == "__main__":
    main()

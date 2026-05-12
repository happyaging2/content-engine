#!/usr/bin/env python3
"""
auto-internal-links.py — Build the internal knowledge graph by injecting
cross-article links based on shared entities (`about` + `mentions` fields).

Strategy:
  1. Build entity → [articles] index from all meta.json files.
  2. For each article, find 2-3 sibling articles that share the most entities.
  3. Inject one inline link per sibling, anchored on the first occurrence of a
     shared entity (skipping intro paragraph and existing links — same idempotent
     pattern used by patch-seo.py for product links).
  4. Always link the primary entity to its pillar page when one exists.

Output: rewrites <slug>-final.html in place. Idempotent (skips paragraphs that
already contain a happyaging.com internal link).

Run after Phase 4 / before publish:
    python3 scripts/auto-internal-links.py
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
SITE = "https://happyaging.com"
BLOG = f"{SITE}/blogs/news"

# Map entity (lowercased) → pillar page slug.
PILLAR_MAP = {
    "nmn": "pillar-nmn",
    "nicotinamide mononucleotide": "pillar-nmn",
    "nad+": "pillar-nad",
    "nad": "pillar-nad",
    "magnesium": "pillar-magnesium",
    "perimenopause": "pillar-perimenopause",
    "menopause": "pillar-perimenopause",
    "sleep": "pillar-sleep",
    "longevity": "pillar-longevity",
    "ashwagandha": "pillar-ashwagandha",
    "sirtuins": "pillar-sirtuins",
}


def _has_link_to_happyaging(para_html: str) -> bool:
    return bool(re.search(r'<a[^>]+href="[^"]*happyaging\.com', para_html))


def _inject_anchor(para_html: str, anchor_text: str, url: str) -> tuple[str, bool]:
    """Wrap first whole-word case-insensitive match of anchor_text with an <a>."""
    if _has_link_to_happyaging(para_html):
        return para_html, False
    pattern = re.compile(rf"\b({re.escape(anchor_text)})\b", re.IGNORECASE)
    out, n = pattern.subn(f'<a href="{url}">\\1</a>', para_html, count=1)
    return out, bool(n)


def _entities(meta: dict) -> list[str]:
    # Defensive against off-spec writer output where about/mentions came back
    # as schema.org Thing dicts ({"@type":..., "name":...}) instead of strings.
    out: list[str] = []
    for key in ("about", "mentions"):
        for v in meta.get(key) or []:
            if isinstance(v, dict):
                v = v.get("name") or v.get("text") or v.get("label") or ""
            v = (v or "").strip() if isinstance(v, str) else str(v).strip()
            if v:
                out.append(v)
    return out


def main():
    metas = {}
    for mf in glob.glob(os.path.join(ARTICLES, "*.meta.json")):
        m = json.load(open(mf))
        slug = m.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        metas[slug] = m

    # Entity → [slug]
    entity_index: dict[str, list[str]] = defaultdict(list)
    for slug, m in metas.items():
        for ent in _entities(m):
            entity_index[ent.lower()].append(slug)

    updated = 0
    for slug, meta in metas.items():
        html_path = os.path.join(ARTICLES, f"{slug}-final.html")
        if not os.path.exists(html_path):
            continue
        body = open(html_path).read()
        ents = [e.lower() for e in _entities(meta)]
        if not ents:
            continue

        # Find sibling articles ranked by shared entity count.
        sibling_score: dict[str, int] = defaultdict(int)
        for e in ents:
            for s in entity_index.get(e, []):
                if s != slug:
                    sibling_score[s] += 1
        siblings = sorted(sibling_score.items(), key=lambda x: -x[1])[:3]

        # Build paragraph list
        paragraphs = list(re.finditer(r"<p[^>]*>(.*?)</p>", body, re.DOTALL))
        if not paragraphs:
            continue

        # Skip intro paragraph; inject from paragraph index 2 onwards.
        eligible = paragraphs[2:]
        injected = 0

        # 1. Pillar links: for the article's primary `about` entity, if a pillar
        #    exists, inject one anchor in an eligible paragraph.
        primary_list = _entities(meta)
        primary = primary_list[0] if primary_list else None
        if primary:
            pillar = PILLAR_MAP.get(primary.lower())
            if pillar:
                pillar_url = f"{SITE}/pages/{pillar}"
                for p in eligible:
                    new, ok = _inject_anchor(p.group(0), primary, pillar_url)
                    if ok:
                        body = body.replace(p.group(0), new, 1)
                        injected += 1
                        break

        # 2. Sibling article links: anchor on the highest-overlap entity.
        for sibling_slug, _score in siblings:
            sibling_meta = metas[sibling_slug]
            sibling_ents = _entities(sibling_meta)
            shared = [e for e in sibling_ents if e.lower() in set(ents)]
            if not shared:
                continue
            anchor = shared[0]
            url = f"{BLOG}/{sibling_slug}"
            for p in eligible:
                # Re-fetch the up-to-date paragraph from current body
                if p.group(0) not in body:
                    continue
                new, ok = _inject_anchor(p.group(0), anchor, url)
                if ok:
                    body = body.replace(p.group(0), new, 1)
                    injected += 1
                    break
            if injected >= 4:
                break

        if injected:
            open(html_path, "w").write(body)
            updated += 1
            print(f"  ✓ {slug[:60]}  (+{injected} internal links)")

    print(f"\nDone. {updated} articles updated.")


if __name__ == "__main__":
    main()

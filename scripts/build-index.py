#!/usr/bin/env python3
"""Build articles/index.json: a flat map of every published article so the
Opportunity Engine (Phase 1) can dedup angles across batches.

Run after every QA + Publish cycle. Reads articles/*.meta.json and
articles/*-final.html (or *.html as fallback). Writes:

    articles/index.json
    {
      "generated_at": "2026-04-27T12:00:00Z",
      "count": 368,
      "by_slug":     { "<slug>": {...meta subset..., "h2s": [...]} },
      "by_cluster":  { "Energy": ["<slug>", ...], ... },
      "by_handle":   { "calm-tonic": ["<slug>", ...], ... },
      "h2_corpus":   ["<lowercased h2>", ...]   # for fuzzy angle dedup
    }
"""
import datetime
import glob
import json
import os
import re
import sys
from collections import defaultdict


H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s):
    return TAG_RE.sub("", s).strip()


def load_h2s(slug):
    for cand in (f"articles/{slug}-final.html", f"articles/{slug}.html"):
        if os.path.exists(cand):
            try:
                body = open(cand, encoding="utf-8").read()
            except Exception:
                return []
            return [strip_tags(m).lower() for m in H2_RE.findall(body)]
    return []


def main():
    by_slug = {}
    by_cluster = defaultdict(list)
    by_handle = defaultdict(list)
    h2_corpus = set()

    for mf in sorted(glob.glob("articles/*.meta.json")):
        try:
            meta = json.load(open(mf, encoding="utf-8"))
        except Exception as e:
            print(f"  skip {mf}: {e}", file=sys.stderr)
            continue
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        h2s = load_h2s(slug)
        h2_corpus.update(h2s)
        entry = {
            "title": meta.get("title", ""),
            "primary_keyword": meta.get("primary_keyword", ""),
            "cluster": meta.get("cluster", ""),
            "product_handle": meta.get("product_handle", ""),
            "tags": meta.get("tags", ""),
            "word_count": meta.get("word_count", 0),
            "h2s": h2s,
        }
        by_slug[slug] = entry
        if entry["cluster"]:
            by_cluster[entry["cluster"]].append(slug)
        if entry["product_handle"]:
            by_handle[entry["product_handle"]].append(slug)

    out = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(by_slug),
        "by_slug": by_slug,
        "by_cluster": {k: sorted(v) for k, v in sorted(by_cluster.items())},
        "by_handle": {k: sorted(v) for k, v in sorted(by_handle.items())},
        "h2_corpus": sorted(h2_corpus),
    }
    with open("articles/index.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"  index.json: {out['count']} articles, "
          f"{len(out['by_cluster'])} clusters, "
          f"{len(out['by_handle'])} products, "
          f"{len(out['h2_corpus'])} unique H2s")


if __name__ == "__main__":
    main()

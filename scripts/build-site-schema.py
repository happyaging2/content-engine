#!/usr/bin/env python3
"""
build-site-schema.py — Generate the site-wide @graph JSON-LD that should be
emitted ONCE in Shopify theme.liquid <head>.

Why: per-article schema only references Organization as a `publisher` field.
Google needs a top-level Organization @id to consolidate the brand into a
single Knowledge Graph entity (with sameAs to Wikidata, GBP, Instagram, etc).

Outputs:
  public/site-schema.json     — raw JSON
  public/site-schema-block.html — full <script> block ready to paste into
                                   theme.liquid (just before </head>)

Manual upload:
  Theme Editor → Edit Code → layout/theme.liquid → paste the contents of
  public/site-schema-block.html immediately above </head>.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "articles"))

from lib_medical_schema import build_site_schema_graph  # noqa: E402

OUT_DIR = os.path.join(ROOT, "public")
os.makedirs(OUT_DIR, exist_ok=True)


def main() -> None:
    graph = build_site_schema_graph()
    with open(os.path.join(OUT_DIR, "site-schema.json"), "w") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    block = (
        '<script type="application/ld+json">\n'
        + json.dumps(graph, ensure_ascii=False, indent=2)
        + "\n</script>\n"
    )
    with open(os.path.join(OUT_DIR, "site-schema-block.html"), "w") as f:
        f.write(block)

    print("Wrote public/site-schema.json + public/site-schema-block.html")
    print("Paste public/site-schema-block.html contents into theme.liquid <head>.")


if __name__ == "__main__":
    main()

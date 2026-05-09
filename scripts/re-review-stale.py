#!/usr/bin/env python3
"""
re-review-stale.py — Flag articles whose `date_reviewed` is older than 90 days
so the next batch refreshes them through Phase 4 (SEO Optimizer).

Output:
  REFRESH-QUEUE.md  — markdown list of slugs to re-process
  Updates each stale meta.json with `needs_refresh: true` and `refresh_reason`.

Run weekly (or as part of the daily orchestrator before Phase 1):
    python3 scripts/re-review-stale.py [--threshold-days 90]

Phase 1 should consume REFRESH-QUEUE.md to bias topic selection toward refreshes
when the queue gets long, and Phase 4 should re-validate citations + bump
`date_reviewed` + `date_modified` for any meta with `needs_refresh: true`.

90 days is the chosen interval because:
  - Google's freshness signal weighs YMYL content heavily on `dateModified`
  - LLMs (Perplexity, ChatGPT Search) tend to prefer content < 6 months old
  - Quarterly cadence catches new PMIDs / FDA updates without overwhelming review
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
QUEUE = os.path.join(ROOT, "REFRESH-QUEUE.md")

THRESHOLD = 90
if "--threshold-days" in sys.argv:
    i = sys.argv.index("--threshold-days")
    THRESHOLD = int(sys.argv[i + 1])


def _parse_date(s: str | None) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s[:10])
    except Exception:
        return None


def main():
    today = dt.date.today()
    cutoff = today - dt.timedelta(days=THRESHOLD)
    stale = []

    for mf in sorted(glob.glob(os.path.join(ARTICLES, "*.meta.json"))):
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")

        last = (
            _parse_date(meta.get("date_reviewed"))
            or _parse_date(meta.get("date_modified"))
            or _parse_date(meta.get("date_published"))
        )
        if not last or last <= cutoff:
            age_days = (today - last).days if last else None
            reasons = []
            if age_days is not None:
                reasons.append(f"last reviewed {age_days}d ago (>{THRESHOLD}d)")
            else:
                reasons.append("missing date_reviewed")

            # Also flag if missing critical GEO fields (defensive)
            if not meta.get("citations"):
                reasons.append("no structured citations")
            if not meta.get("about"):
                reasons.append("no `about` entities")
            if not meta.get("reviewer_url"):
                reasons.append("no reviewer_url")

            meta["needs_refresh"] = True
            meta["refresh_reason"] = "; ".join(reasons)
            meta["refresh_flagged_on"] = today.isoformat()
            json.dump(meta, open(mf, "w"), indent=2, ensure_ascii=False)
            stale.append(
                {
                    "slug": slug,
                    "title": meta.get("title", slug),
                    "age_days": age_days,
                    "reasons": reasons,
                }
            )

    # Write REFRESH-QUEUE.md
    lines = [
        f"# Refresh Queue — generated {today.isoformat()}",
        "",
        f"Threshold: articles not reviewed within **{THRESHOLD} days** "
        "are added below. Phase 4 (SEO Optimizer) reads this list and re-runs "
        "PMID validation, citation enrichment, and bumps `date_reviewed` + "
        "`date_modified` on the corresponding article.",
        "",
        f"Total flagged: **{len(stale)}**",
        "",
        "| Slug | Age (days) | Reasons |",
        "|---|---:|---|",
    ]
    for s in sorted(stale, key=lambda x: -(x["age_days"] or 0)):
        age = s["age_days"] if s["age_days"] is not None else "—"
        lines.append(f"| `{s['slug']}` | {age} | {'; '.join(s['reasons'])} |")

    with open(QUEUE, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Flagged {len(stale)} articles. Queue at {QUEUE}")


if __name__ == "__main__":
    main()

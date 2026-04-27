#!/usr/bin/env python3
"""Aggregate articles/qa-*.log into a single rollup so we can answer
"how many publishes succeeded/failed this month?" without grepping logs.

Writes articles/publish-metrics.json:
{
  "generated_at": "...",
  "totals": {"batches": N, "ok": N, "err": N, "skip_cover": N, "fake_dois_removed": N},
  "by_batch": [
    {"date": "2026-04-19", "ok": 20, "err": 0, "skip_cover": 0,
     "fake_dois_removed": 3, "total_on_shopify": 368, "errors": [...]}
  ]
}
"""
import datetime
import glob
import json
import os
import re


OK_RE = re.compile(r"^\s*OK\s+.*\(id:(\d+)\)")
ERR_RE = re.compile(r"^\s*ERR\s+(\S+):\s*(.+)$")
SKIP_COVER_RE = re.compile(r"^\s*SKIP cover\s+(\S+)")
FAKE_DOI_RE = re.compile(r"Removed (\d+) fake DOIs")
TOTAL_RE = re.compile(r"Total articles on Shopify:\s*(\d+)")
BATCH_DATE_RE = re.compile(r"qa-(\d{4}-\d{2}-\d{2})\.log$")


def parse(path):
    date = BATCH_DATE_RE.search(path).group(1)
    out = {"date": date, "ok": 0, "err": 0, "skip_cover": 0,
           "fake_dois_removed": 0, "total_on_shopify": None, "errors": []}
    for line in open(path, encoding="utf-8", errors="replace"):
        if OK_RE.match(line):
            out["ok"] += 1
        elif (m := ERR_RE.match(line)):
            out["err"] += 1
            out["errors"].append({"slug": m.group(1), "message": m.group(2)[:200]})
        elif SKIP_COVER_RE.match(line):
            out["skip_cover"] += 1
        elif (m := FAKE_DOI_RE.search(line)):
            out["fake_dois_removed"] += int(m.group(1))
        elif (m := TOTAL_RE.search(line)):
            out["total_on_shopify"] = int(m.group(1))
    return out


def main():
    logs = sorted(glob.glob("articles/qa-*.log"))
    by_batch = [parse(p) for p in logs]
    totals = {
        "batches": len(by_batch),
        "ok": sum(b["ok"] for b in by_batch),
        "err": sum(b["err"] for b in by_batch),
        "skip_cover": sum(b["skip_cover"] for b in by_batch),
        "fake_dois_removed": sum(b["fake_dois_removed"] for b in by_batch),
    }
    out = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": totals,
        "by_batch": by_batch,
    }
    with open("articles/publish-metrics.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"  publish-metrics.json: {totals['batches']} batches | "
          f"OK={totals['ok']} ERR={totals['err']} "
          f"skip_cover={totals['skip_cover']} fake_dois={totals['fake_dois_removed']}")
    if totals["err"]:
        recent = [b for b in by_batch if b["err"]][-3:]
        for b in recent:
            print(f"    {b['date']}: {b['err']} error(s)")
            for e in b["errors"][:3]:
                print(f"      - {e['slug']}: {e['message'][:80]}")


if __name__ == "__main__":
    main()

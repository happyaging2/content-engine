#!/usr/bin/env bash
# indexnow-submit.sh — Notify Bing/Yandex/Seznam when new articles are published.
# ChatGPT Search uses Bing's index — IndexNow shortens the discovery loop.
#
# One-time setup:
#   1. Generate a UUID-style key (32 hex chars).
#   2. Upload the file <KEY>.txt containing just <KEY> to:
#        https://happyaging.com/<KEY>.txt
#   3. Export it: export INDEXNOW_KEY=<KEY>
#
# Usage:
#   bash scripts/indexnow-submit.sh                # submits all article URLs
#   bash scripts/indexnow-submit.sh url1 url2 ...  # submits specific URLs

set -euo pipefail

HOST="happyaging.com"
KEY="${INDEXNOW_KEY:-}"

if [ -z "$KEY" ]; then
  echo "ERROR: set INDEXNOW_KEY (and ensure https://${HOST}/${KEY}.txt is reachable)"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$#" -gt 0 ]; then
  URLS=("$@")
else
  # Build URL list from articles/*.meta.json
  mapfile -t URLS < <(
    python3 - <<'PY'
import glob, json, os
articles = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'articles') if False else 'articles'
for mf in sorted(glob.glob('articles/*.meta.json')):
    m = json.load(open(mf))
    slug = m.get('slug') or os.path.basename(mf).replace('.meta.json','')
    print(f"https://happyaging.com/blogs/news/{slug}")
PY
  )
fi

# Chunk into batches of 100 (IndexNow limit is 10,000 per request, but smaller
# batches are friendlier).
BATCH_SIZE=100
TOTAL=${#URLS[@]}
echo "Submitting ${TOTAL} URLs to IndexNow (host=${HOST})..."

for ((i=0; i<TOTAL; i+=BATCH_SIZE)); do
  batch=("${URLS[@]:i:BATCH_SIZE}")
  json_urls=$(printf '"%s",' "${batch[@]}" | sed 's/,$//')
  body=$(cat <<EOF
{
  "host": "${HOST}",
  "key": "${KEY}",
  "keyLocation": "https://${HOST}/${KEY}.txt",
  "urlList": [${json_urls}]
}
EOF
)
  echo "  Batch $((i / BATCH_SIZE + 1)): ${#batch[@]} URLs"
  curl -sS -X POST "https://api.indexnow.org/IndexNow" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "$body" -o /tmp/indexnow.out -w "    HTTP %{http_code}\n" || true
done

echo "Done."

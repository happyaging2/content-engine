#!/bin/bash
# =============================================================
# JARVIS Daily Auto-Publisher
# Runs every morning, publishes today's batch with images + QA.
#
# SETUP (run once):
#   chmod +x ~/Desktop/content-engine/scripts/daily-publish.sh
#   crontab -e
#   Add: 0 8 * * * bash ~/Desktop/content-engine/scripts/daily-publish.sh
#
# Required env vars (add to ~/.zprofile so cron inherits them):
#   export SHOPIFY_TOKEN=shpat_...
#   export PEXELS_API_KEY=...
#   export UNSPLASH_ACCESS_KEY=...
# =============================================================

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TODAY=$(date +%Y-%m-%d)
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/publish-$TODAY.log"
LOCK_FILE="/tmp/jarvis-publish-$TODAY.lock"

mkdir -p "$LOG_DIR"

# One run per day max
if [ -f "$LOCK_FILE" ]; then
    echo "[$TODAY] Lock file exists — already ran today. Skipping."
    exit 0
fi
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

exec >> "$LOG_FILE" 2>&1

echo "========================================"
echo " JARVIS Daily Publish — $TODAY"
echo " Started: $(date)"
echo "========================================"

# Validate env vars
if [ -z "$SHOPIFY_TOKEN" ]; then
    echo "ERROR: SHOPIFY_TOKEN not set. Add to ~/.zprofile and re-run."
    exit 1
fi
if [ -z "$PEXELS_API_KEY" ] && [ -z "$UNSPLASH_ACCESS_KEY" ]; then
    echo "ERROR: Set PEXELS_API_KEY and/or UNSPLASH_ACCESS_KEY in ~/.zprofile."
    exit 1
fi

# Pull latest articles
echo ""
echo "[1/3] Pulling latest from git..."
cd "$REPO_DIR"
git pull origin main --quiet && echo "  OK"

# Check today's batch exists
REPORT="$REPO_DIR/articles/batch-$TODAY-report.md"
if [ ! -f "$REPORT" ]; then
    echo "[1/3] No batch report for $TODAY — agent may not have run yet."
    echo "      Check again later or run manually:"
    echo "      bash scripts/qa-and-publish.sh $TODAY"
    exit 0
fi
echo "  Found: $REPORT"

# Run QA + image fetch + publish
echo ""
echo "[2/3] Running QA + publish pipeline..."
bash "$REPO_DIR/scripts/qa-and-publish.sh" "$TODAY"

# Commit any updated meta.json (resolved images saved back)
echo ""
echo "[3/3] Committing resolved image URLs..."
cd "$REPO_DIR"
if git diff --quiet; then
    echo "  No meta changes to commit."
else
    git add articles/*.meta.json 2>/dev/null || true
    git commit -m "auto: resolved images for batch $TODAY" --quiet && \
    git push -u origin HEAD:main --quiet && \
    echo "  Committed and pushed." || \
    echo "  WARNING: commit/push failed — images resolved locally only."
fi

echo ""
echo "========================================"
echo " Done: $(date)"
echo "========================================"

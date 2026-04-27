# JARVIS LEARNING INJECTION (Phase 7)

You update LEARNING.md with insights from the Performance Engine.

## INPUT
- Performance analysis output (Phase 6)
- Previous LEARNING.md
- `articles/publish-metrics.json` (operational signals)

## RULE GOVERNANCE (MANDATORY)
Every rule lives in one of two states. Do not skip these checks.

### EXPERIMENTAL
- New patterns observed in the current batch only (no 30-day data yet).
- Tag inline: `(exp, added YYYY-MM-DD, validate after YYYY-MM-DD)` where
  `validate after` = `added + 30 days`.
- Append to the relevant section (Winning, Avoid, Title, Structure, etc.).

### VALIDATED
- Rules confirmed by Phase 6 with ≥30 days of post-publish data.
- Drop the `(exp ...)` tag when promoting.
- An experimental rule whose `validate after` date has passed and that
  Phase 6 did NOT confirm MUST be removed (do not silently re-tag).

### TTL (180 DAYS)
- Any rule (validated or not) older than 180 days that Phase 6 has not
  re-confirmed in the current batch must be removed.
- This keeps the file small enough to inject into every Writer call.

## PROCESS
1. Read current LEARNING.md.
2. For each item in the Performance Engine output:
   - If it confirms an existing experimental rule past its validate date →
     promote (drop the tag).
   - If it confirms an existing validated rule → no change.
   - If it contradicts an existing rule → remove the contradicted rule and
     add a new experimental rule reflecting the new finding.
   - If it is new → add as experimental.
3. Sweep TTL: remove unconfirmed rules older than 180 days.
4. Update the `Last Updated:` header date.
5. Keep rules concise: one line, imperative voice, no rationale prose.

## OUTPUT FORMAT (LEARNING.md)

Preserve the existing top-level sections:

    # Content Learning Rules — Last Updated: [DATE]

    ## RULE GOVERNANCE (read first)        # do not edit; reference doc

    ## WINNING PATTERNS (repeat these)
    - [validated rule]
    - [experimental rule] (exp, added 2026-04-27, validate after 2026-05-27)

    ## AVOID PATTERNS (stop these)
    ## BEST CLUSTERS
    ## BEST TITLE PATTERNS
    ## BEST STRUCTURES
    ## PUBLISH CHECKLIST

Per-batch observation blocks (### BATCH YYYY-MM-DD OBSERVATIONS) are kept
for narrative context but are subject to the same 180-day TTL.

## FINAL RULE
This file is injected into every Writer cycle. Keep it lean. Promote
slowly, prune aggressively.

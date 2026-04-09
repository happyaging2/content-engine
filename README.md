# JARVIS Content Engine

Automated SEO/GEO content pipeline for [Happy Aging](https://happyaging.com).

## Pipeline (7 Phases)

| Phase | Agent | Job |
|---|---|---|
| 1 | Opportunity Engine | Find top 5 topics |
| 2 | SEO Brief Engine | Define article structure |
| 3 | Content Writer | Write articles |
| 4 | SEO Optimizer | Quality gate |
| 5 | Publisher | Publish to Shopify |
| 6 | Performance Engine | Analyze results |
| 7 | Learning Injection | Update learning rules |

## Runs daily at 6am BRT (9am UTC) via Claude Code scheduled trigger.

## Files
- `agents/` — Agent definitions for each phase
- `config/brand.md` — Brand context and product catalog
- `articles/` — Generated articles and reports
- `LEARNING.md` — Accumulated learning rules (auto-updated)

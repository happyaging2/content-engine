# JARVIS Content Engine

Automated SEO/GEO content pipeline for Happy Aging (happyaging.com).

## Agent System

| Agent | File | Purpose |
|---|---|---|
| Orchestrator | agents/jarvis-orchestrator.md | Coordinates full pipeline |
| Content Engine | agents/jarvis-content-engine.md | Phase 1: Find opportunities |
| Content Writer | agents/jarvis-content-writer.md | Phase 2: Write articles |
| SEO Optimizer | agents/jarvis-seo-optimizer.md | Phase 2.5: Quality gate |
| Performance | agents/jarvis-content-performance.md | Phase 3: Analyze + feedback |

## Pipeline Flow
```
Phase 1 (Find 20 topics) → Phase 2 (Write articles) → Phase 2.5 (SEO QA) → Publish → Phase 3 (Analyze)
```

## Configuration
- Brand context: config/brand.md
- Published articles: articles/
- Performance data: CONTENT-PERFORMANCE.md

## Publishing
Articles are published via Shopify Admin API (REST):
```bash
curl -X POST "https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"article": {"title": "...", "body_html": "...", "author": "Dr. Daniel Yadegar, MD", "tags": "...", "published": true, "template_suffix": "timeline"}}'
```

## Rules
- All text in English (US)
- No medical claims without citations
- No invented statistics
- Max 20 articles per batch
- Template suffix: timeline

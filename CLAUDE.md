# JARVIS Content Engine

Automated SEO/GEO content pipeline for Happy Aging (happyaging.com).
Daily run, 20 articles per cycle.

## Agent System

| Phase | Agent | File |
|---|---|---|
| — | Orchestrator | agents/orchestrator.md |
| 1 | Opportunity Engine | agents/01-opportunity-engine.md |
| 2 | SEO Brief Engine | agents/02-seo-brief-engine.md |
| 3 | Content Writer | agents/03-content-writer.md |
| 4 | SEO Optimizer (quality gate) | agents/04-seo-optimizer.md |
| 5 | Publisher | agents/05-publisher.md |
| 6 | Performance Engine | agents/06-performance-engine.md |
| 7 | Learning Injection | agents/07-learning-injection.md |

## Pipeline Flow
```
1. Opportunity Engine   → find top 20 topics
2. SEO Brief Engine     → deterministic brief per topic
3. Content Writer       → write article (injects LEARNING.md)
4. SEO Optimizer        → quality gate each article
5. Publisher            → push to Shopify
6. Performance Engine   → analyze patterns
7. Learning Injection   → update LEARNING.md (feeds back into Phase 3)
```

## Configuration
- Brand context: config/brand.md
- Learning rules (feedback loop): LEARNING.md
- Published articles: articles/
- Performance data: CONTENT-PERFORMANCE.md
- QA + publish script: scripts/qa-and-publish.sh

## Publishing
Published via Shopify Admin API (REST). Prefer the script over raw curl:
```bash
cd /path/to/content-engine && bash scripts/qa-and-publish.sh [YYYY-MM-DD]
```

Required env vars: `SHOPIFY_TOKEN`, `OPENAI_API_KEY`.

Raw endpoint (parametrize in shell):
```bash
SHOPIFY_STORE="shop-happy-aging.myshopify.com"
BLOG_ID="109440303424"
curl -X POST "https://${SHOPIFY_STORE}/admin/api/2024-01/blogs/${BLOG_ID}/articles.json" \
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

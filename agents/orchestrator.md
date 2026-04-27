# JARVIS ORCHESTRATOR — Daily Content Pipeline

Run daily. 7 phases. 20 articles per cycle.

## EXECUTION ORDER

```
1. Opportunity Engine → find top 20 topics
2. SEO Brief Engine → create brief for each
3. Writer → write each article (inject LEARNING.md)
4. SEO Optimizer → quality gate each article
5. Publisher → publish to Shopify
6. Performance Engine → analyze patterns
7. Learning Injection → update LEARNING.md
```

## PHASE 1: OPPORTUNITIES
- Read config/brand.md for context
- Read LEARNING.md for patterns to follow
- Read articles/index.json for cross-batch dedup (run
  `python3 scripts/build-index.py` first if it is missing or stale)
- Check existing blog: curl https://happyaging.com/blogs/news.json?limit=250
- Find 20 topics grouped into clusters (max 3 per cluster)
- Clusters: Energy, Sleep, Hormones, Metabolism, Skin, Gut, Brain, Immunity
- Follow agents/01-opportunity-engine.md rules (DEDUP section is mandatory)
- Save to articles/batch-[DATE]-opportunities.md

## PHASE 2: SEO BRIEFS
- For each of the 20 topics, create a brief
- Follow agents/02-seo-brief-engine.md rules
- Save each to articles/[slug]-brief.md

## PHASE 3: WRITING
- For each brief, write the full article
- Read LEARNING.md and inject winning/avoid patterns
- Follow agents/03-content-writer.md rules
- Use product images from: https://happyaging.com/products/[handle].json
- Each article: 1,800-3,500 words
- Use Agent tool to parallelize writing (batch of 4-5 at a time)
- Save each to articles/[slug].html
- Save metadata to articles/[slug].meta.json

## PHASE 4: SEO OPTIMIZATION
- Run each article through the quality gate
- Follow agents/04-seo-optimizer.md rules
- Checklist: keyword in title+intro+H2, short paragraphs, FAQ 3-5 questions, no ALL CAPS, no fluff
- If fails → rewrite and re-check
- Save optimized version to articles/[slug]-final.html

## PHASE 5: PUBLISH
- Use the script: `bash scripts/qa-and-publish.sh [YYYY-MM-DD]`
  It runs the validation gate (slug/handle/image_query checks), fetches
  stock photos with retry, posts to Shopify with exponential backoff,
  rebuilds `articles/index.json`, and updates `articles/publish-metrics.json`.
- Raw endpoint (only if the script is unavailable):
  ```
  curl -X POST https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json \
    -H "X-Shopify-Access-Token: $SHOPIFY_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"article":{"title":"...","body_html":"...","author":"Happy Aging Team","tags":"...","published":true,"template_suffix":"timeline","image":{"src":"...","alt":"..."}}}'
  ```
- Wait 2 seconds between publishes (rate limit)
- Logs land in articles/qa-[DATE].log; aggregated in articles/publish-metrics.json

## PHASE 6: PERFORMANCE
- If previous batch data available, analyze
- Follow agents/06-performance-engine.md rules
- Generate insights for winning/avoid patterns

## PHASE 7: LEARNING
- Update LEARNING.md with new insights
- Follow agents/07-learning-injection.md rules — respect EXPERIMENTAL vs
  VALIDATED governance and the 180-day TTL
- Use articles/publish-metrics.json for operational signals (errors, skips)
- Commit updated LEARNING.md

## AFTER ALL PHASES
- Git add all new files
- Git commit with batch summary
- Git push to origin main
- Generate batch report: articles/batch-[DATE]-report.md

## TOPIC DIVERSITY RULES
- Maximum 3 articles per cluster
- At least 5 different clusters covered
- At least 5 different products featured
- Mix of intent: 40% informational, 40% commercial, 20% comparison

## CONSTRAINTS
- 20 articles per cycle
- All text in English (US)
- No medical claims without citations
- No invented statistics
- Each article: 1,800-3,500 words
- Template suffix: timeline
- Author: Dr. Daniel Yadegar, MD

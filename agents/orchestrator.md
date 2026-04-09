# JARVIS ORCHESTRATOR — Daily Content Pipeline

Run daily. 7 phases. 5 articles per cycle.

## EXECUTION ORDER

```
1. Opportunity Engine → find top 5 topics
2. SEO Brief Engine → create brief for each
3. Content Writer → write each article (inject LEARNING.md)
4. SEO Optimizer → quality gate each article
5. Publisher → publish to Shopify
6. Performance Engine → analyze (if data available)
7. Learning Injection → update LEARNING.md
```

## PHASE 1: OPPORTUNITIES
- Read config/brand.md for context
- Read LEARNING.md for patterns to follow
- Check existing blog: curl https://happyaging.com/blogs/news.json?limit=250
- Find 5 topics (not 20 — quality over quantity)
- Follow agents/01-opportunity-engine.md rules
- Save to articles/batch-[DATE]-opportunities.md

## PHASE 2: SEO BRIEFS
- For each of the 5 topics, create a brief
- Follow agents/02-seo-brief-engine.md rules
- Save each to articles/[slug]-brief.md

## PHASE 3: WRITING
- For each brief, write the full article
- Read LEARNING.md and inject winning/avoid patterns
- Follow agents/03-content-writer.md rules
- Use product images from: https://happyaging.com/products/[handle].json
- Save each to articles/[slug].html
- Save metadata to articles/[slug].meta.json

## PHASE 4: SEO OPTIMIZATION
- Run each article through the quality gate
- Follow agents/04-seo-optimizer.md rules
- If fails → rewrite and re-check
- Save optimized version to articles/[slug]-final.html

## PHASE 5: PUBLISH
- Follow agents/05-publisher.md rules
- Use Shopify Admin REST API with token from environment
- Template suffix: timeline
- Author: Dr. Daniel Yadegar, MD
- Log results to articles/published.log

## PHASE 6: PERFORMANCE
- If previous batch data available, analyze
- Follow agents/06-performance-engine.md rules
- Generate insights

## PHASE 7: LEARNING
- Update LEARNING.md with new insights
- Follow agents/07-learning-injection.md rules
- Commit updated LEARNING.md

## AFTER ALL PHASES
- Git commit all new files
- Git push to origin main
- Generate batch report: articles/batch-[DATE]-report.md

## CONSTRAINTS
- Max 5 articles per cycle
- All text in English
- No invented claims
- No medical advice without citations
- Each article: 1,800-3,500 words

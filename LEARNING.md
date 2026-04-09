# Content Learning Rules — Last Updated: 2026-04-09

## WINNING PATTERNS (repeat these)
- Question-based titles get higher CTR ("Why do I..." / "What causes..." / "Is X normal?")
- "What to Know" box at top increases time on page
- FAQ sections with direct 1-2 sentence answers get featured snippets
- Articles with 5+ H2 sections and clear structure perform better
- Product bridges work best when they solve the problem discussed, not just promote
- Opening paragraph must include primary keyword in first 100 words — always
- Evening/morning routine sections increase save and share behavior significantly
- Reassurance + solution structure (validate → explain → fix) reduces bounce for symptom queries
- Authority hooks in titles ("A Hormone Expert Explains", "What Science Says") improve trust + CTR
- Single product card inline per article — multiple product links dilute conversion

## AVOID PATTERNS (stop these)
- ALL CAPS headings reduce trust
- Long introductions (>150 words before value) increase bounce
- Generic conclusions with no actionable takeaway
- Keyword stuffing in first paragraph sounds robotic
- Articles without citations feel untrustworthy for health content
- Multiple CTAs or product links in one article — pick one hero product per article
- Assumed CDN image paths — always verify product image URLs via products/[handle].json before publishing
- Metabolism/multi-benefit articles with 3+ product links — always narrow to single CTA

## BEST CLUSTERS
- Energy: highest conversion (connects to NAD+, CoQ10) — prioritize in every batch
- Sleep: high search volume, strong product fit (Sleep Blend, Magnesium)
- Hormones: emotional resonance with audience, high engagement — not yet covered, add next batch
- Brain: underserved in competitor content, high GEO/featured snippet potential — expanding
- Gut: emerging interest 40+ women, strong Happiest Gut product fit — schedule next

## BEST TITLE PATTERNS
- Problem + Age + Curiosity: "Why Do I Feel So Tired After 40? (The Real Reason Nobody Tells You)"
- Question + Authority: "Why Can't I Sleep Like I Used To After 40? (A Hormone Expert Explains)"
- Question + Solution Promise: "Is Brain Fog After 40 Normal? What Causes It and How to Clear It"
- Empowerment: "What Happens to Your Metabolism After 40 (And How to Actually Fight Back)"
- Science Authority: "Why Your Skin Ages Faster After 40 (And What Science Says About Collagen)"

## BEST STRUCTURES
- Hook (pain point) → What it is → Why it happens → What helps → Tips/Routine → FAQ → Soft CTA
- Keep sections 150-250 words each
- One product card inline, max 1 text link to product (not 2-3)
- Routine sections (evening/morning/daily) are high-engagement — add to relevant articles
- DOI citations in references section are non-negotiable for health content trust

## PUBLISH CHECKLIST (new — added 2026-04-09)
- Verify product image CDN paths via https://happyaging.com/products/[handle].json before publishing
- Primary keyword must appear verbatim in first 100 words
- What-to-know box must be first element after opening paragraph
- FAQ must have minimum 4 questions, each answered in 1-2 sentences
- References must include DOI or PMID for every citation
- Template suffix must be "timeline" — never leave blank

## BATCH 2026-04-09 OBSERVATIONS (20-article batch)

### Production Patterns
- Parallel 4-agent writing achieves 20 articles in one session efficiently
- What-to-know box + 6-8 H2s is the right structural density for this audience
- "After 40" suffix in title increases specificity and resonance
- FAQ answers of 1-2 sentences are optimal for featured snippet targeting
- Product cards placed after the "what helps" section feel natural, not promotional

### GEO / AI Citation Optimization
- "What to Know" box bullet points are highly extractable by AI systems
- FAQ h3+p pairs are the #1 format for AI answer extraction
- Sections framed as definitions ("What Is X?") work well for AI context windows
- Avoid metaphors and idioms in direct answer sections — AI prefers literal language

### Cluster Predictions (validate in 30 days)
- Energy: highest predicted conversion — NAD+ products have clear CTA
- Sleep 3am-wake article: likely featured snippet candidate (very specific query)
- "Estrogen decline symptoms" article: strong list format for GEO extraction
- "Blood sugar belly fat" angle: differentiated vs. generic weight loss content

### Next Batch Priorities
- Track which cluster generates first organic traffic
- If Energy cluster converts: add 3 more Energy articles next batch
- Consider "What Is NAD+?" explainer hub page (higher-volume informational)
- "Perimenopause checklist" format could drive very high engagement + shares

## STRICT RULES (added 2026-04-09 — mandatory for all future batches)

### NO DASHES IN TEXT
- NEVER use em dashes (—) or en dashes (–) in article text
- Use commas, periods, or colons instead
- Example: "NAD+ levels drop after 40, and the effects are real" NOT "NAD+ levels drop after 40 — and the effects are real"

### AUTHOR
- Author for ALL articles: "Happy Aging Team" (not Dr. Daniel Yadegar)
- Written By: Happy Aging Team

### IMAGES (CRITICAL)
- Featured image (top): NEVER use a product image. Use a lifestyle/wellness image.
- Product card inline: Use real product image from products/[handle].json API
- Body images: Use AI-generated realistic lifestyle images related to the content
- For AI images, use Unsplash as source: https://source.unsplash.com/800x450/?[keyword]
- Alternative: Use Pexels API or Pixabay for free stock images
- Every article must have 3-4 images throughout the text
- Images must be relevant to the section they appear in

### PRODUCT CARD FIX
- The product-card-inline must use this exact HTML structure:
```html
<div class="product-card-inline">
<a href="https://happyaging.com/products/[handle]">
<img src="[REAL_IMAGE_FROM_API]" alt="[Product Name]">
</a>
<div>
<h4><a href="https://happyaging.com/products/[handle]">[Product Name]</a></h4>
<p>[Short description]</p>
<p><strong>$XX/month</strong> with subscription</p>
<a href="https://happyaging.com/products/[handle]">Shop Now</a>
</div>
</div>
```
- ALWAYS verify the image URL works before publishing

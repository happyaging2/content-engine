#!/usr/bin/env python3
"""
Batch 2026-05-04 Publish Script
Publishes 20 articles to Shopify blog 109440303424
Run from an environment with network access to shop-happy-aging.myshopify.com

Usage:
    SHOPIFY_TOKEN=shpat_xxx python3 scripts/batch-2026-05-04-publish.py

Requirements:
    - SHOPIFY_TOKEN env var set
    - Run from the content-engine repo root
    - -final.html files present in articles/
"""

import json
import os
import time
import urllib.request
import urllib.error

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
API_URL = f"https://{STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
AUTHOR = "Happy Aging Team"
TEMPLATE = "timeline"

ARTICLES = [
    {
        "slug": "collagen-hair-growth-after-40",
        "title": "Collagen and Hair Growth After 40: What the Research Shows",
        "tags": "collagen, hair growth, hair loss, women over 40, perimenopause, supplements, keratin",
    },
    {
        "slug": "probiotics-mental-health-anxiety-after-40",
        "title": "Probiotics for Mental Health and Anxiety After 40: The Gut-Brain Connection",
        "tags": "probiotics, mental health, anxiety, gut-brain axis, women over 40, microbiome, perimenopause",
    },
    {
        "slug": "retinol-vs-bakuchiol-skin-after-40",
        "title": "Retinol vs Bakuchiol for Women Over 40: Which Is Right for Your Skin?",
        "tags": "retinol, bakuchiol, anti-aging, skin care, women over 40, collagen, wrinkles",
    },
    {
        "slug": "does-berberine-help-weight-loss-after-40",
        "title": "Does Berberine Help with Weight Loss After 40? What the Evidence Says",
        "tags": "berberine, weight loss, metabolism, insulin resistance, women over 40, AMPK, blood sugar",
    },
    {
        "slug": "phosphatidylserine-does-it-work-memory-after-40",
        "title": "Phosphatidylserine for Memory After 40: Does It Actually Work?",
        "tags": "phosphatidylserine, memory, cognitive function, brain health, women over 40, cortisol, nootropics",
    },
    {
        "slug": "ampk-activators-natural-after-40",
        "title": "Natural AMPK Activators After 40: Turning On the Metabolic Switch",
        "tags": "AMPK, metabolism, longevity, berberine, exercise, women over 40, fat loss, energy",
    },
    {
        "slug": "what-is-nad-vs-nmn-difference-after-40",
        "title": "NAD+ vs NMN: What Is the Difference and Which Should Women Over 40 Take?",
        "tags": "NAD+, NMN, nicotinamide, supplements, longevity, women over 40, cellular energy, mitochondria",
    },
    {
        "slug": "myo-inositol-d-chiro-inositol-ratio-after-40",
        "title": "Myo-Inositol and D-Chiro-Inositol: The Ratio That Matters for Women Over 40",
        "tags": "myo-inositol, D-chiro-inositol, PCOS, hormones, insulin resistance, women over 40, fertility",
    },
    {
        "slug": "signs-estrogen-dominance-after-40",
        "title": "Signs of Estrogen Dominance After 40: Symptoms, Causes, and Solutions",
        "tags": "estrogen dominance, progesterone, hormones, women over 40, perimenopause, PMS, breast tenderness",
    },
    {
        "slug": "how-to-use-retinol-vitamin-c-together-after-40",
        "title": "How to Use Retinol and Vitamin C Together After 40 Without Irritation",
        "tags": "retinol, vitamin C, skincare routine, anti-aging, women over 40, collagen, skin care",
    },
    {
        "slug": "taurine-exercise-performance-after-40",
        "title": "Taurine and Exercise Performance After 40: What the Research Shows for Women",
        "tags": "taurine, exercise, muscle, endurance, women over 40, recovery, amino acids",
    },
    {
        "slug": "what-is-conjugated-linoleic-acid-cla-after-40",
        "title": "What Is CLA (Conjugated Linoleic Acid)? Benefits for Women Over 40",
        "tags": "CLA, conjugated linoleic acid, body composition, fat loss, muscle, women over 40, metabolism",
    },
    {
        "slug": "how-to-test-nad-levels-at-home-after-40",
        "title": "How to Test Your NAD+ Levels at Home After 40: A Practical Guide",
        "tags": "NAD+ testing, NAD levels, home test, longevity, women over 40, NMN, NR, cellular health, biohacking",
    },
    {
        "slug": "best-supplements-menopause-weight-gain-after-40",
        "title": "Best Supplements for Menopause Weight Gain After 40: What Actually Works",
        "tags": "menopause weight gain, weight loss supplements, women over 40, metabolism, hormones, perimenopause, belly fat, best supplements",
    },
    {
        "slug": "rem-sleep-benefits-after-40",
        "title": "REM Sleep After 40: Why It Declines and How to Get More of It",
        "tags": "REM sleep, sleep stages, women over 40, memory consolidation, emotional processing, sleep quality, perimenopause, dreaming",
    },
    {
        "slug": "vitamin-d-immunity-after-40",
        "title": "Vitamin D and Immunity After 40: Why Most Women Are Deficient and What to Do",
        "tags": "vitamin D, immunity, immune health, women over 40, deficiency, autoimmune, supplements, inflammation",
    },
    {
        "slug": "best-time-to-take-magnesium-women-after-40",
        "title": "Best Time to Take Magnesium for Women Over 40: Morning vs Night",
        "tags": "magnesium, magnesium glycinate, sleep, women over 40, timing, anxiety, muscle cramps, perimenopause",
    },
    {
        "slug": "how-to-lower-blood-pressure-naturally-after-40",
        "title": "How to Lower Blood Pressure Naturally After 40: Evidence-Based Strategies for Women",
        "tags": "blood pressure, hypertension, women over 40, natural remedies, heart health, magnesium, diet, exercise",
    },
    {
        "slug": "fatty-liver-after-40-women",
        "title": "Fatty Liver After 40 in Women: Signs, Causes, and How to Reverse It",
        "tags": "fatty liver, NAFLD, women over 40, liver health, metabolic health, perimenopause, diet, supplements",
    },
    {
        "slug": "coq10-heart-health-research-women-after-40",
        "title": "CoQ10 and Heart Health in Women After 40: What the Research Actually Shows",
        "tags": "CoQ10, coenzyme Q10, heart health, women over 40, cardiovascular, energy, statins, mitochondria",
    },
]


def publish_article(slug, title, tags, body_html):
    payload = {
        "article": {
            "title": title,
            "body_html": body_html,
            "author": AUTHOR,
            "tags": tags,
            "published": True,
            "template_suffix": TEMPLATE,
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            article_id = result.get("article", {}).get("id", "?")
            handle = result.get("article", {}).get("handle", "?")
            return True, article_id, handle
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, e.code, body
    except Exception as e:
        return False, 0, str(e)


def main():
    if not SHOPIFY_TOKEN:
        print("ERROR: SHOPIFY_TOKEN environment variable not set.")
        return

    print(f"Publishing batch 2026-05-04 ({len(ARTICLES)} articles)")
    print(f"Store: {STORE} | Blog: {BLOG_ID}")
    print()

    results = []
    for i, article in enumerate(ARTICLES, 1):
        slug = article["slug"]
        final_path = f"articles/{slug}-final.html"
        if not os.path.exists(final_path):
            print(f"[{i:02d}] SKIP (no final file): {slug}")
            results.append({"slug": slug, "status": "skipped"})
            continue

        body_html = open(final_path).read()
        print(f"[{i:02d}] Publishing: {article['title'][:60]}...", end=" ", flush=True)

        ok, id_or_code, detail = publish_article(
            slug, article["title"], article["tags"], body_html
        )

        if ok:
            print(f"OK (id={id_or_code}, handle={detail})")
            results.append({"slug": slug, "status": "published", "id": id_or_code, "handle": detail})
        else:
            print(f"FAIL ({id_or_code}): {str(detail)[:120]}")
            results.append({"slug": slug, "status": "failed", "code": id_or_code, "error": str(detail)[:200]})

        # Rate limit: Shopify allows 2 req/s on REST; 0.6s interval is safe
        if i < len(ARTICLES):
            time.sleep(0.6)

    print()
    published = sum(1 for r in results if r["status"] == "published")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"Done: {published} published, {failed} failed, {skipped} skipped")

    # Write results log
    log_path = "articles/publish-2026-05-04.json"
    with open(log_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {log_path}")


if __name__ == "__main__":
    main()

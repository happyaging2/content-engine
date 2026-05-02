#!/usr/bin/env python3
"""
Batch 2026-04-30 Publish Script
Publishes 20 articles to Shopify blog 109440303424
Run from an environment with network access to shop-happy-aging.myshopify.com

Usage:
    SHOPIFY_TOKEN=shpat_xxx python3 scripts/batch-2026-04-30-publish.py

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
        "slug": "testosterone-libido-after-40-women",
        "title": "Testosterone and Libido After 40: What Women Need to Know",
        "tags": "testosterone, libido, hormones, women over 40, perimenopause, sexual health",
    },
    {
        "slug": "adrenal-recovery-protocol-after-40",
        "title": "Adrenal Recovery Protocol After 40: A Step-by-Step Guide for Women",
        "tags": "adrenal fatigue, cortisol, HPA axis, stress, women over 40, adaptogens",
    },
    {
        "slug": "bone-health-protocol-after-40",
        "title": "Bone Health Protocol After 40: The Complete Guide for Women",
        "tags": "bone health, osteoporosis, calcium, vitamin D, women over 40, resistance training",
    },
    {
        "slug": "glycine-vs-gaba-sleep-after-40",
        "title": "Glycine vs GABA for Sleep After 40: Which Works Better?",
        "tags": "glycine, GABA, sleep, insomnia, women over 40, perimenopause, sleep supplements",
    },
    {
        "slug": "best-foods-bone-health-after-40",
        "title": "Best Foods for Bone Health After 40: Beyond Calcium and Dairy",
        "tags": "bone health, diet, calcium, vitamin K2, collagen, women over 40, nutrition",
    },
    {
        "slug": "estrogen-heart-health-after-menopause",
        "title": "Estrogen and Heart Health After Menopause: What Every Woman Should Know",
        "tags": "estrogen, heart health, menopause, cardiovascular, women over 40, cholesterol",
    },
    {
        "slug": "senolytic-foods-after-40",
        "title": "Senolytic Foods After 40: Eating to Clear Zombie Cells",
        "tags": "senolytics, fisetin, quercetin, senescent cells, longevity, women over 40, anti-aging foods",
    },
    {
        "slug": "nmn-brain-cognitive-benefits-after-40",
        "title": "NMN and Brain Health: Cognitive Benefits After 40",
        "tags": "NMN, brain health, cognitive function, NAD+, women over 40, nootropics, memory",
    },
    {
        "slug": "what-is-trimethylglycine-tmg-after-40",
        "title": "What Is TMG (Trimethylglycine)? Benefits After 40 for Women",
        "tags": "TMG, trimethylglycine, betaine, methylation, homocysteine, women over 40, NMN",
    },
    {
        "slug": "sleep-apnea-women-over-40",
        "title": "Sleep Apnea in Women Over 40: The Overlooked Epidemic",
        "tags": "sleep apnea, women, menopause, sleep disorders, fatigue, women over 40",
    },
    {
        "slug": "collagen-for-tendons-ligaments-after-40",
        "title": "Collagen for Tendons and Ligaments After 40: The Research",
        "tags": "collagen, tendons, ligaments, joint health, women over 40, connective tissue, exercise",
    },
    {
        "slug": "insulin-resistance-hormones-connection-after-40",
        "title": "Insulin Resistance and Hormones After 40: The Hidden Connection",
        "tags": "insulin resistance, hormones, perimenopause, blood sugar, women over 40, metabolic health",
    },
    {
        "slug": "l-carnitine-energy-after-40",
        "title": "L-Carnitine and Energy After 40: Benefits for Women",
        "tags": "L-carnitine, energy, fatigue, mitochondria, women over 40, fat metabolism",
    },
    {
        "slug": "l-glutamine-gut-healing-after-40",
        "title": "L-Glutamine and Gut Healing After 40: What the Research Shows",
        "tags": "L-glutamine, gut health, leaky gut, gut lining, women over 40, intestinal health",
    },
    {
        "slug": "vitamin-e-skin-after-40",
        "title": "Vitamin E and Skin Health After 40: Beyond the Basics",
        "tags": "vitamin E, skin health, anti-aging, antioxidants, women over 40, collagen, skin care",
    },
    {
        "slug": "what-is-alpha-ketoglutarate-aging-after-40",
        "title": "What Is Alpha-Ketoglutarate (AKG)? Longevity Benefits After 40",
        "tags": "alpha-ketoglutarate, AKG, longevity, epigenetics, TET enzymes, women over 40, aging",
    },
    {
        "slug": "how-blood-sugar-disrupts-sleep-after-40",
        "title": "How Blood Sugar Disrupts Sleep After 40 (And What to Do)",
        "tags": "blood sugar, sleep, insulin, glucose, women over 40, perimenopause, night waking",
    },
    {
        "slug": "adaptogens-guide-women-over-40",
        "title": "Adaptogens Guide for Women Over 40: Which Ones Actually Work",
        "tags": "adaptogens, ashwagandha, rhodiola, maca, holy basil, women over 40, stress, cortisol",
    },
    {
        "slug": "what-is-phosphatidylcholine-brain-after-40",
        "title": "What Is Phosphatidylcholine? Brain and Liver Benefits After 40",
        "tags": "phosphatidylcholine, choline, brain health, liver health, acetylcholine, women over 40, memory",
    },
    {
        "slug": "gut-immune-connection-after-40",
        "title": "The Gut-Immune Connection After 40: Why Your Microbiome Drives Immunity",
        "tags": "gut health, immune system, microbiome, leaky gut, women over 40, inflammation, probiotics",
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

    print(f"Publishing batch 2026-04-30 ({len(ARTICLES)} articles)")
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
    log_path = "articles/publish-2026-04-30.json"
    with open(log_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {log_path}")


if __name__ == "__main__":
    main()

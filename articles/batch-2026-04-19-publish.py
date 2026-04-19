#!/usr/bin/env python3
"""
Batch 2026-04-19 Shopify Publisher
Publishes 20 articles to Happy Aging Shopify blog.
Run from: /home/user/content-engine/articles/
"""

import json
import os
import time
import urllib.request
import urllib.error

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "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")
BLOG_ID = "109440303424"
API_URL = f"https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
AUTHOR = "Happy Aging Team"

ARTICLES = [
    {
        "slug": "vitamin-d-menopause-research-women",
        "title": "Vitamin D and Menopause: What the Research Actually Shows for Women Over 40",
        "tags": "menopause, vitamin d, bone health, hormones, women over 40",
    },
    {
        "slug": "how-to-know-nad-supplement-is-working-after-40",
        "title": "How to Know If Your NAD+ Supplement Is Working After 40",
        "tags": "NAD+, NMN, energy, anti-aging, women over 40",
    },
    {
        "slug": "how-to-know-sleep-supplement-is-working-after-40",
        "title": "How to Know If Your Sleep Supplement Is Working After 40",
        "tags": "sleep, supplements, magnesium, perimenopause, women over 40",
    },
    {
        "slug": "what-happens-sleep-after-menopause",
        "title": "What Happens to Your Sleep After Menopause? (And What Helps)",
        "tags": "sleep, menopause, hormones, insomnia, women over 40",
    },
    {
        "slug": "what-is-estrobolome-menopause",
        "title": "What Is the Estrobolome? (And Why It Matters for Menopause)",
        "tags": "estrobolome, gut health, hormones, menopause, microbiome",
    },
    {
        "slug": "estrogen-after-menopause-complete-guide",
        "title": "What Happens to Estrogen After Menopause? A Complete Guide",
        "tags": "estrogen, menopause, hormones, postmenopause, women over 40",
    },
    {
        "slug": "progesterone-anxiety-connection-after-40",
        "title": "Progesterone and Anxiety After 40: The Connection Explained",
        "tags": "progesterone, anxiety, perimenopause, GABA, hormones",
    },
    {
        "slug": "can-you-take-creatine-and-protein-together-after-40",
        "title": "Can You Take Creatine and Protein Together After 40? What the Research Shows",
        "tags": "creatine, protein, muscle, metabolism, women over 40",
    },
    {
        "slug": "signs-metabolism-improving-after-40",
        "title": "7 Signs Your Metabolism Is Actually Improving After 40",
        "tags": "metabolism, energy, weight, mitochondria, women over 40",
    },
    {
        "slug": "how-long-does-glutathione-take-to-work-skin",
        "title": "How Long Does Glutathione Take to Work for Skin? A Realistic Timeline",
        "tags": "glutathione, skin, brightening, antioxidant, women over 40",
    },
    {
        "slug": "collagen-peptides-vs-marine-collagen-after-40",
        "title": "Collagen Peptides vs Marine Collagen: Which Is Better for Women Over 40?",
        "tags": "collagen, marine collagen, skin, joints, women over 40",
    },
    {
        "slug": "signs-gut-bacteria-imbalanced-after-40",
        "title": "Signs Your Gut Bacteria Are Out of Balance After 40 (And What to Do)",
        "tags": "gut health, microbiome, dysbiosis, digestion, women over 40",
    },
    {
        "slug": "what-happens-gut-health-after-menopause",
        "title": "What Happens to Your Gut Health After Menopause? (And How to Protect It)",
        "tags": "gut health, menopause, microbiome, digestion, postmenopause",
    },
    {
        "slug": "how-to-know-brain-supplement-is-working-after-40",
        "title": "How to Know if Your Brain Supplement Is Working After 40",
        "tags": "brain health, nootropics, cognitive, focus, women over 40",
    },
    {
        "slug": "ashwagandha-vs-rhodiola-stress-fatigue-after-40",
        "title": "Ashwagandha vs Rhodiola for Stress and Fatigue After 40: Which Works Better?",
        "tags": "ashwagandha, rhodiola, adaptogens, stress, fatigue, women over 40",
    },
    {
        "slug": "signs-immune-system-getting-stronger-after-40",
        "title": "Signs Your Immune System Is Getting Stronger After 40",
        "tags": "immune system, immunity, supplements, women over 40, inflammation",
    },
    {
        "slug": "liposomal-quercetin-vs-regular-quercetin-after-40",
        "title": "Liposomal Quercetin vs Regular Quercetin After 40: What Is the Difference?",
        "tags": "quercetin, liposomal, immunity, inflammation, bioavailability, women over 40",
    },
    {
        "slug": "how-long-does-collagen-take-to-work-joints",
        "title": "How Long Does Collagen Take to Work for Joints? A Realistic Timeline",
        "tags": "collagen, joints, cartilage, joint pain, women over 40",
    },
    {
        "slug": "omega-3-heart-health-women-over-40",
        "title": "Omega-3 and Heart Health: What Women Over 40 Need to Know",
        "tags": "omega-3, heart health, cardiovascular, fish oil, menopause, women over 40",
    },
    {
        "slug": "does-molecular-hydrogen-work-for-aging-women",
        "title": "Does Molecular Hydrogen Actually Work for Aging? An Honest Review for Women Over 40",
        "tags": "molecular hydrogen, antioxidant, anti-aging, mitochondria, women over 40",
    },
]


def read_html(slug):
    path = f"{slug}-final.html"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def publish_article(article):
    body_html = read_html(article["slug"])
    payload = json.dumps({
        "article": {
            "title": article["title"],
            "author": AUTHOR,
            "body_html": body_html,
            "tags": article["tags"],
            "published": True,
            "template_suffix": "timeline",
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                art_id = result["article"]["id"]
                handle = result["article"]["handle"]
                print(f"  [OK] {article['slug']} -> id:{art_id} handle:{handle}")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  [ERR] {article['slug']} HTTP {e.code}: {body[:200]}")
            if e.code == 429:
                wait = 2 ** attempt
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                return False
        except Exception as e:
            print(f"  [ERR] {article['slug']} {e} (attempt {attempt})")
            time.sleep(2 ** attempt)

    return False


def main():
    print(f"Publishing {len(ARTICLES)} articles to Shopify blog {BLOG_ID}...")
    success = 0
    failed = []

    for i, article in enumerate(ARTICLES, 1):
        print(f"\n[{i}/{len(ARTICLES)}] {article['slug']}")
        ok = publish_article(article)
        if ok:
            success += 1
        else:
            failed.append(article["slug"])
        # Respect Shopify rate limits (2 req/sec)
        time.sleep(0.6)

    print(f"\n{'='*60}")
    print(f"Published: {success}/{len(ARTICLES)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print("Done.")


if __name__ == "__main__":
    main()

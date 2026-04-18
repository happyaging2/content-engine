#!/usr/bin/env python3
"""
Batch 2026-04-18 Publish Script
Run from an environment with network access to shop-happy-aging.myshopify.com
"""

import json
import os
import time
import requests

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "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")
ENDPOINT = "https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    "Content-Type": "application/json"
}

ARTICLES = [
    {
        "slug": "signs-you-are-low-in-vitamin-d-after-40",
        "title": "Signs You Are Low in Vitamin D After 40 (And What to Do About It)",
        "tags": "vitamin d deficiency, vitamin d after 40, signs of vitamin d deficiency, energy, bone health, immunity",
        "product_handle": "longevity-shots",
        "excerpt": "Vitamin D deficiency is one of the most common nutritional shortfalls in women over 40. Learn the 7 key signs your levels may be low and exactly what to do about it."
    },
    {
        "slug": "b12-deficiency-signs-after-40",
        "title": "Signs You Need More B12 After 40 (And Why It Matters)",
        "tags": "b12 deficiency, vitamin b12 after 40, b12 signs, energy, brain health, fatigue women",
        "product_handle": "longevity-shots",
        "excerpt": "B12 deficiency becomes more common after 40 as stomach acid declines. Here are the signs to watch for and why acting early protects your brain and energy."
    },
    {
        "slug": "nad-plus-exercise-performance-after-40",
        "title": "NAD+ and Exercise Performance After 40: What the Research Shows",
        "tags": "nad+ exercise, nad+ performance, nmn exercise, energy after 40, mitochondria fitness, nad+ women",
        "product_handle": "nmn-cell-renew-tonic",
        "excerpt": "Your workouts feel harder because NAD+ levels have fallen. Here is what the research shows about NAD+ precursors and exercise recovery in women over 40."
    },
    {
        "slug": "menopause-and-heart-disease-women",
        "title": "Menopause and Heart Disease: What Every Woman Over 40 Needs to Know",
        "tags": "menopause heart disease, cardiovascular health women, heart health after 40, menopause risk, estrogen heart",
        "product_handle": "nad-women-longevity-formula",
        "excerpt": "Heart disease is the leading cause of death in women, and menopause dramatically accelerates the risk. What every woman over 40 needs to understand."
    },
    {
        "slug": "collagen-for-joint-health-after-40",
        "title": "Collagen for Joint Health After 40: What the Research Actually Shows",
        "tags": "collagen for joints, joint health after 40, collagen supplement joints, cartilage support, joint pain women",
        "product_handle": "glow-shot",
        "excerpt": "Collagen makes up 70% of cartilage. Here is what clinical trials actually show about collagen supplementation for joint pain and function after 40."
    },
    {
        "slug": "bone-broth-for-joints-after-40",
        "title": "What Is Bone Broth and Does It Help Your Joints After 40?",
        "tags": "bone broth joints, bone broth after 40, collagen bone broth, joint health, bone broth benefits",
        "product_handle": "glow-shot",
        "excerpt": "Bone broth provides collagen-building amino acids for joint health, but how does it compare to supplements? An honest look at what it can and cannot do."
    },
    {
        "slug": "signs-you-are-low-in-magnesium-after-40",
        "title": "Signs You Are Low in Magnesium After 40 (And What It Means)",
        "tags": "magnesium deficiency, signs low magnesium, magnesium after 40, sleep magnesium, muscle cramps magnesium",
        "product_handle": "calm-tonic",
        "excerpt": "Nearly half of American adults are low in magnesium, and after 40 the risk grows. Here are the 6 key signs of magnesium deficiency and what to do about them."
    },
    {
        "slug": "sleep-deprivation-weight-gain-after-40",
        "title": "Sleep Deprivation and Weight Gain After 40: The Connection Explained",
        "tags": "sleep deprivation weight gain, sleep and weight after 40, sleep metabolism, insomnia weight, sleep hormones",
        "product_handle": "sleep-tonic",
        "excerpt": "Poor sleep directly drives weight gain through ghrelin, leptin, cortisol, and decision-making. Here is exactly how sleep deprivation is working against you after 40."
    },
    {
        "slug": "how-to-build-supplement-stack-women-over-40",
        "title": "How to Build Your Supplement Stack for Women Over 40 (A Step-by-Step Guide)",
        "tags": "supplement stack women over 40, best supplements women over 40, supplement guide menopause, longevity supplements women",
        "product_handle": "nad-advanced-longevity-formula",
        "excerpt": "A step-by-step guide to building a supplement routine that addresses the specific nutritional and hormonal needs of women over 40, based on current evidence."
    },
    {
        "slug": "menopause-weight-management-guide",
        "title": "Menopause Weight Management: A Complete Guide for Women Over 40",
        "tags": "menopause weight management, weight gain menopause, menopause metabolism, belly fat menopause, weight loss menopause",
        "product_handle": "nad-women-longevity-formula",
        "excerpt": "Menopausal weight gain is hormonal, not moral. A complete, science-backed guide to the strategies that actually work for women navigating this transition."
    },
    {
        "slug": "creatine-vs-protein-women-over-40",
        "title": "Creatine vs Protein for Women Over 40: Which Is Better?",
        "tags": "creatine vs protein women, creatine for women over 40, protein supplement women, muscle mass women 40s, strength training supplements",
        "product_handle": "lean-muscle-formula",
        "excerpt": "Creatine and protein work through completely different mechanisms. Here is how to use both effectively for muscle preservation and body composition after 40."
    },
    {
        "slug": "why-do-you-lose-muscle-after-40",
        "title": "Why Do You Lose Muscle After 40? (And How to Actually Fight Back)",
        "tags": "muscle loss after 40, sarcopenia women, losing muscle menopause, maintain muscle over 40, muscle mass decline",
        "product_handle": "lean-muscle-formula",
        "excerpt": "Women lose 1 to 2% of muscle per year after 40, and menopause accelerates it. Here is exactly why it happens and the most evidence-backed ways to stop it."
    },
    {
        "slug": "omega-3-deficiency-signs-after-40",
        "title": "Signs You Are Low in Omega-3 After 40 (And Why It Matters More Than You Think)",
        "tags": "omega-3 deficiency signs, omega-3 after 40, fish oil deficiency, DHA EPA women, omega-3 benefits women over 40",
        "product_handle": "relief-tonic",
        "excerpt": "Most women consume far less omega-3 than optimal. After 40, the consequences for joints, brain, skin, and heart health are more significant than ever."
    },
    {
        "slug": "anti-inflammatory-foods-women-over-40",
        "title": "Anti-Inflammatory Foods for Women Over 40 (A Practical Guide)",
        "tags": "anti-inflammatory foods women, anti-inflammatory diet over 40, reduce inflammation naturally, foods fight inflammation, menopause inflammation",
        "product_handle": "liver-tonic",
        "excerpt": "What you eat every day either fuels inflammation or helps resolve it. A practical guide to the most effective anti-inflammatory foods for women over 40."
    },
    {
        "slug": "liposomal-vitamin-c-after-40",
        "title": "Liposomal Vitamin C After 40: What It Is and Why Absorption Matters",
        "tags": "liposomal vitamin c, vitamin c after 40, liposomal supplements, vitamin c absorption, immunity vitamin c",
        "product_handle": "longevity-shots",
        "excerpt": "Standard vitamin C hits an absorption ceiling that limits its effectiveness. Liposomal delivery bypasses this, and after 40 the difference matters more than ever."
    },
    {
        "slug": "dhea-for-women-over-40-guide",
        "title": "DHEA for Women Over 40: What It Is, What It Does, and Whether It Helps",
        "tags": "DHEA for women, DHEA after 40, DHEA menopause, dehydroepiandrosterone women, DHEA hormones",
        "product_handle": "nad-women-longevity-formula",
        "excerpt": "DHEA is the body's most abundant hormone, and it falls by 80% between your 20s and 70s. Here is what the research actually shows about DHEA for women over 40."
    },
    {
        "slug": "hair-thinning-after-menopause",
        "title": "Why Does Hair Thin After Menopause? (And What Actually Helps)",
        "tags": "hair thinning menopause, hair loss after 40, menopausal hair thinning, hair loss women, female hair loss causes",
        "product_handle": "nmn-cell-renew-tonic",
        "excerpt": "Hair thinning after menopause is driven by falling estrogen, nutritional deficiencies, and thyroid changes. Here is how to identify your specific cause and what actually helps."
    },
    {
        "slug": "how-to-lower-cortisol-naturally-after-40",
        "title": "How to Lower Cortisol Naturally After 40: A Practical Guide",
        "tags": "lower cortisol naturally, cortisol after 40, reduce stress hormones, high cortisol women, cortisol management menopause",
        "product_handle": "calm-tonic",
        "excerpt": "Chronically high cortisol drives abdominal fat, broken sleep, and anxiety in women over 40. A practical guide to lowering it naturally through sleep, diet, exercise, and targeted supplements."
    },
    {
        "slug": "gut-bacteria-weight-loss-after-40",
        "title": "Gut Bacteria and Weight Loss After 40: What the Research Shows",
        "tags": "gut bacteria weight loss, gut microbiome weight, gut health weight loss women, microbiome after 40, probiotic weight loss",
        "product_handle": "happiest-gut",
        "excerpt": "Your gut bacteria influence how many calories you extract from food, how insulin-sensitive you are, and how hungry you feel. Here is what the research shows for women over 40."
    },
    {
        "slug": "how-inflammation-affects-brain-after-40",
        "title": "How Inflammation Affects Brain Function After 40 (And What to Do About It)",
        "tags": "inflammation brain function, neuroinflammation after 40, brain fog inflammation, cognitive health women, brain health menopause",
        "product_handle": "neuro-creamer",
        "excerpt": "Neuroinflammation is a major but underrecognized driver of brain fog, memory issues, and cognitive decline in women over 40. Here is what to do about it."
    },
]

def get_product_image(handle):
    """Fetch real product image from Shopify storefront."""
    try:
        url = f"https://happyaging.com/products/{handle}.json"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            images = data.get("product", {}).get("images", [])
            if images:
                return images[0]["src"], images[0].get("alt", handle)
    except Exception as e:
        print(f"  Could not fetch image for {handle}: {e}")
    return None, None

def get_article_html(slug):
    path = f"/home/user/content-engine/articles/{slug}-final.html"
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None

def publish_article(article):
    slug = article["slug"]
    html = get_article_html(slug)
    if not html:
        print(f"  SKIP {slug}: no HTML file found")
        return None

    img_src, img_alt = get_product_image(article["product_handle"])
    if not img_src:
        print(f"  WARNING: No product image fetched for {article['product_handle']}, publishing without image")

    payload = {
        "article": {
            "title": article["title"],
            "body_html": html,
            "author": "Happy Aging Team",
            "tags": article["tags"],
            "summary_html": article["excerpt"],
            "published": True,
            "template_suffix": "timeline",
        }
    }

    if img_src:
        payload["article"]["image"] = {
            "src": img_src,
            "alt": img_alt or article["title"]
        }

    try:
        r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=30)
        if r.status_code in (200, 201):
            data = r.json()
            article_id = data["article"]["id"]
            print(f"  PUBLISHED {slug}: id={article_id}")
            return {"slug": slug, "id": article_id, "status": "published"}
        else:
            print(f"  FAILED {slug}: HTTP {r.status_code} - {r.text[:200]}")
            return {"slug": slug, "status": "failed", "error": r.text[:200]}
    except Exception as e:
        print(f"  ERROR {slug}: {e}")
        return {"slug": slug, "status": "error", "error": str(e)}

results = []
for i, article in enumerate(ARTICLES):
    print(f"[{i+1}/20] Publishing: {article['slug']}")
    result = publish_article(article)
    if result:
        results.append(result)
    time.sleep(2)  # Rate limit

output_path = "/home/user/content-engine/articles/batch-2026-04-18-publish-results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

published = sum(1 for r in results if r.get("status") == "published")
failed = sum(1 for r in results if r.get("status") in ("failed", "error"))
print(f"\nDone: {published}/20 published, {failed} failed")
print(f"Results saved to {output_path}")

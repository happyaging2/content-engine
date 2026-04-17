#!/usr/bin/env python3
"""
Batch 2026-04-17 Shopify publish script.
Run from unrestricted network environment:
  SHOPIFY_TOKEN=shpat_xxx python3 batch-2026-04-17-publish.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

SHOP = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
API_VERSION = "2024-01"
TOKEN = os.environ.get("SHOPIFY_TOKEN", "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")
BASE_URL = f"https://{SHOP}/admin/api/{API_VERSION}/blogs/{BLOG_ID}/articles.json"
ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))

ARTICLES = [
    {
        "slug": "does-nad-women-formula-work-honest-review",
        "title": "Does Happy Aging's NAD+ Women's Formula Actually Work? An Honest Review",
        "tags": "NAD+, womens health, longevity, hormones, honest review, perimenopause, energy",
    },
    {
        "slug": "does-sleep-blend-actually-work-honest-review",
        "title": "Does Happy Aging's Liposomal Sleep Blend Actually Work? An Honest Review",
        "tags": "sleep, sleep supplements, honest review, magnesium, liposomal, insomnia, women over 40",
    },
    {
        "slug": "does-neuro-creamer-work-brain-fog",
        "title": "Does Happy Aging Neuro Creamer Actually Help Brain Fog? An Honest Review",
        "tags": "brain fog, nootropics, neuro creamer, coffee creamer, focus, memory, women over 40, honest review",
    },
    {
        "slug": "does-glow-shot-collagen-actually-work",
        "title": "Does Happy Aging Glow Shot Marine Collagen Actually Work? An Honest Review",
        "tags": "marine collagen, collagen supplement, glow shot, skin, honest review, women over 40, anti-aging",
    },
    {
        "slug": "does-happiest-gut-actually-work",
        "title": "Does Happy Aging Happiest Gut Actually Work? An Honest Review",
        "tags": "gut health, probiotics, prebiotics, happiest gut, honest review, bloating, women over 40",
    },
    {
        "slug": "bone-loss-after-40-women",
        "title": "Bone Loss After 40: What Every Woman Needs to Know",
        "tags": "bone loss, osteoporosis, bone density, women over 40, menopause, calcium, vitamin D",
    },
    {
        "slug": "best-supplements-bone-health-after-40",
        "title": "Best Supplements for Bone Health After 40 (What Science Actually Supports)",
        "tags": "bone health supplements, calcium, vitamin D, vitamin K2, magnesium, collagen, women over 40, osteoporosis prevention",
    },
    {
        "slug": "resistance-training-bone-density-women-over-40",
        "title": "Resistance Training and Bone Density After 40: How to Build Stronger Bones",
        "tags": "resistance training, bone density, strength training, women over 40, osteoporosis, exercise, bone health",
    },
    {
        "slug": "heart-health-women-after-40",
        "title": "Heart Health After 40: What Changes in Women and What Actually Helps",
        "tags": "heart health, cardiovascular, women over 40, menopause, heart disease prevention, cholesterol, blood pressure",
    },
    {
        "slug": "coq10-heart-health-after-40",
        "title": "CoQ10 and Heart Health After 40: What the Research Actually Shows",
        "tags": "CoQ10, heart health, cardiovascular, women over 40, coenzyme Q10, cholesterol, energy, longevity",
    },
    {
        "slug": "nad-plus-before-and-after-women",
        "title": "NAD+ Before and After: Real Changes Women Over 40 Actually Notice",
        "tags": "NAD+, before and after, energy, women over 40, cellular health, longevity, transformation",
    },
    {
        "slug": "how-to-boost-nad-levels-naturally-after-40",
        "title": "How to Naturally Boost NAD+ Levels After 40 (A Complete Guide)",
        "tags": "NAD+, how to boost NAD+, natural energy, women over 40, cellular health, NMN, longevity, lifestyle",
    },
    {
        "slug": "gaining-weight-without-eating-more-after-40",
        "title": "Why Am I Gaining Weight Without Eating More After 40? The Real Reason",
        "tags": "weight gain after 40, metabolism, hormones, menopause, women over 40, belly fat, why am I gaining weight",
    },
    {
        "slug": "creatine-for-women-over-40",
        "title": "Creatine for Women Over 40: What It Is and Whether You Should Take It",
        "tags": "creatine, women over 40, muscle, strength training, supplement, lean muscle, menopause",
    },
    {
        "slug": "natural-estrogen-support-after-menopause",
        "title": "Natural Ways to Support Estrogen After Menopause (Without HRT)",
        "tags": "estrogen, menopause, natural HRT alternative, phytoestrogens, hormones, women over 40, perimenopause",
    },
    {
        "slug": "testosterone-decline-women-over-40",
        "title": "Testosterone Decline in Women Over 40: What It Means and What Helps",
        "tags": "testosterone women, women over 40, hormones, low testosterone, libido, muscle, energy, NMN",
    },
    {
        "slug": "signs-your-body-is-inflamed-after-40",
        "title": "Signs Your Body Is Chronically Inflamed After 40 (And What to Do About It)",
        "tags": "chronic inflammation, inflammation signs, women over 40, inflammaging, immune health, quercetin",
    },
    {
        "slug": "how-to-strengthen-immune-system-after-40",
        "title": "How to Strengthen Your Immune System After 40 (A Science-Backed Guide)",
        "tags": "immune system, women over 40, immunity, quercetin, vitamin C, gut health, lifestyle, how to boost immunity",
    },
    {
        "slug": "inside-out-beauty-supplements-after-40",
        "title": "Inside-Out Beauty: The Best Supplements for Glowing Skin After 40",
        "tags": "skin supplements, glowing skin, women over 40, collagen, glutathione, vitamin C, omega-3, inside out beauty",
    },
    {
        "slug": "how-to-improve-memory-naturally-after-40",
        "title": "How to Improve Memory Naturally After 40 (A Science-Backed Guide)",
        "tags": "memory, brain health, women over 40, cognitive decline, focus, nootropics, natural memory improvement, neuro creamer",
    },
]


def publish_article(article_meta):
    slug = article_meta["slug"]
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")

    if not os.path.exists(html_path):
        print(f"  ERROR: File not found: {html_path}")
        return None

    with open(html_path, "r", encoding="utf-8") as f:
        body_html = f.read()

    payload = json.dumps({
        "article": {
            "title": article_meta["title"],
            "body_html": body_html,
            "author": "Happy Aging Team",
            "tags": article_meta["tags"],
            "published": True,
            "template_suffix": "timeline",
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        BASE_URL,
        data=payload,
        headers={
            "X-Shopify-Access-Token": TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            article_id = result["article"]["id"]
            print(f"  OK: {article_meta['title'][:60]} => article_id={article_id}")
            return article_id
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  FAIL [{e.code}]: {article_meta['title'][:60]}")
        print(f"    {body[:200]}")
        return None
    except Exception as e:
        print(f"  ERROR: {article_meta['title'][:60]} => {e}")
        return None


def main():
    print(f"Publishing {len(ARTICLES)} articles to {SHOP}...")
    print(f"Blog ID: {BLOG_ID}")
    print()

    results = {"ok": [], "fail": []}

    for i, meta in enumerate(ARTICLES, 1):
        print(f"[{i:02d}/{len(ARTICLES)}] {meta['slug']}")
        article_id = publish_article(meta)
        if article_id:
            results["ok"].append({"slug": meta["slug"], "id": article_id})
        else:
            results["fail"].append(meta["slug"])

        if i < len(ARTICLES):
            time.sleep(0.5)

    print()
    print(f"Done: {len(results['ok'])} published, {len(results['fail'])} failed")

    if results["fail"]:
        print("Failed slugs:")
        for slug in results["fail"]:
            print(f"  - {slug}")

    results_path = os.path.join(ARTICLES_DIR, "batch-2026-04-17-publish-results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()

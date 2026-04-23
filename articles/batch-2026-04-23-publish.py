#!/usr/bin/env python3
"""
Batch publisher for 2026-04-23 content batch.
POST 20 articles to Shopify blog 109440303424.
Run from /home/user/content-engine/articles/ directory.
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime

SHOPIFY_TOKEN = "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"
API_URL = "https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
AUTHOR = "Happy Aging Team"
TEMPLATE_SUFFIX = "timeline"
LOG_FILE = "published.log"

ARTICLES = [
    {
        "slug": "liver-health-signs-after-40",
        "title": "Signs Your Liver Needs Support After 40",
        "tags": "liver health, detox, women over 40, liver function, hormonal health",
        "html_file": "liver-health-signs-after-40-final.html",
    },
    {
        "slug": "what-is-berberine-blood-sugar-after-40",
        "title": "What Is Berberine and Does It Help Blood Sugar After 40?",
        "tags": "berberine, blood sugar, insulin resistance, women over 40, metabolic health",
        "html_file": "what-is-berberine-blood-sugar-after-40-final.html",
    },
    {
        "slug": "how-to-detox-liver-naturally-after-40",
        "title": "How to Support Liver Detox After 40: What Actually Works",
        "tags": "liver detox, women over 40, liver health, natural detox, cruciferous vegetables",
        "html_file": "how-to-detox-liver-naturally-after-40-final.html",
    },
    {
        "slug": "insulin-resistance-after-40-women",
        "title": "Insulin Resistance After 40: Signs, Causes, and What Helps",
        "tags": "insulin resistance, women over 40, blood sugar, metabolic health, perimenopause",
        "html_file": "insulin-resistance-after-40-women-final.html",
    },
    {
        "slug": "why-diets-stop-working-after-40",
        "title": "Why Diets Stop Working After 40 (And What Does Instead)",
        "tags": "diets after 40, metabolism, women over 40, muscle loss, weight management",
        "html_file": "why-diets-stop-working-after-40-final.html",
    },
    {
        "slug": "what-are-sirtuins-aging-after-40",
        "title": "What Are Sirtuins and How Do They Affect Aging After 40?",
        "tags": "sirtuins, NAD+, aging, women over 40, longevity, cellular health",
        "html_file": "what-are-sirtuins-aging-after-40-final.html",
    },
    {
        "slug": "what-is-fisetin-aging-after-40",
        "title": "What Is Fisetin and Can It Slow Aging After 40?",
        "tags": "fisetin, senolytic, cellular senescence, aging, women over 40, longevity",
        "html_file": "what-is-fisetin-aging-after-40-final.html",
    },
    {
        "slug": "how-to-support-mitochondrial-health-after-40",
        "title": "How to Support Mitochondrial Health After 40 (The Science-Backed Approach)",
        "tags": "mitochondria, energy, NAD+, CoQ10, women over 40, fatigue",
        "html_file": "how-to-support-mitochondrial-health-after-40-final.html",
    },
    {
        "slug": "what-is-phosphatidylserine-memory-after-40",
        "title": "What Is Phosphatidylserine and Can It Help Memory After 40?",
        "tags": "phosphatidylserine, memory, brain health, women over 40, cognitive decline",
        "html_file": "what-is-phosphatidylserine-memory-after-40-final.html",
    },
    {
        "slug": "lions-mane-mushroom-brain-health-after-40",
        "title": "Lion's Mane Mushroom for Brain Health After 40: What the Research Shows",
        "tags": "lion's mane, mushroom, brain health, memory, women over 40, NGF",
        "html_file": "lions-mane-mushroom-brain-health-after-40-final.html",
    },
    {
        "slug": "what-is-gut-brain-axis-after-40",
        "title": "What Is the Gut-Brain Axis and Why Does It Matter After 40?",
        "tags": "gut-brain axis, microbiome, mood, women over 40, gut health, serotonin",
        "html_file": "what-is-gut-brain-axis-after-40-final.html",
    },
    {
        "slug": "leaky-gut-hormones-after-40",
        "title": "How Leaky Gut Affects Hormones After 40",
        "tags": "leaky gut, hormones, estrogen, women over 40, gut health, intestinal permeability",
        "html_file": "leaky-gut-hormones-after-40-final.html",
    },
    {
        "slug": "menopause-cardiovascular-risk-women-after-40",
        "title": "Menopause and Cardiovascular Risk: What Women Over 40 Need to Know",
        "tags": "menopause, cardiovascular risk, heart health, women over 40, estrogen, cholesterol",
        "html_file": "menopause-cardiovascular-risk-women-after-40-final.html",
    },
    {
        "slug": "best-heart-healthy-supplements-women-over-40",
        "title": "Best Heart-Healthy Supplements for Women Over 40",
        "tags": "heart health, supplements, women over 40, omega-3, CoQ10, cardiovascular",
        "html_file": "best-heart-healthy-supplements-women-over-40-final.html",
    },
    {
        "slug": "vitamin-c-collagen-skin-after-40",
        "title": "Vitamin C and Collagen: Why This Combination Matters for Skin After 40",
        "tags": "vitamin C, collagen, skin health, women over 40, anti-aging, glow",
        "html_file": "vitamin-c-collagen-skin-after-40-final.html",
    },
    {
        "slug": "what-is-astaxanthin-skin-after-40",
        "title": "What Is Astaxanthin and Can It Improve Skin After 40?",
        "tags": "astaxanthin, skin health, antioxidant, women over 40, anti-aging, photoprotection",
        "html_file": "what-is-astaxanthin-skin-after-40-final.html",
    },
    {
        "slug": "perimenopause-brain-fog-hormone-connection",
        "title": "Perimenopause Brain Fog: The Hormone Connection Explained",
        "tags": "perimenopause, brain fog, hormones, estrogen, women over 40, cognitive health",
        "html_file": "perimenopause-brain-fog-hormone-connection-final.html",
    },
    {
        "slug": "estrogen-and-weight-gain-after-40",
        "title": "Estrogen and Weight Gain After 40: What's Really Happening",
        "tags": "estrogen, weight gain, women over 40, perimenopause, belly fat, metabolism",
        "html_file": "estrogen-and-weight-gain-after-40-final.html",
    },
    {
        "slug": "ubiquinol-vs-ubiquinone-coq10-after-40",
        "title": "Ubiquinol vs. Ubiquinone: Which Form of CoQ10 Is Best After 40?",
        "tags": "ubiquinol, ubiquinone, CoQ10, women over 40, energy, heart health",
        "html_file": "ubiquinol-vs-ubiquinone-coq10-after-40-final.html",
    },
    {
        "slug": "best-supplements-menopause-fatigue",
        "title": "Best Supplements for Menopause Fatigue: What Actually Works",
        "tags": "menopause fatigue, supplements, women over 40, NAD+, energy, perimenopause",
        "html_file": "best-supplements-menopause-fatigue-final.html",
    },
]


def read_html(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def publish_article(article):
    html_path = article["html_file"]
    if not os.path.exists(html_path):
        log(f"ERROR: File not found: {html_path}")
        return False

    body_html = read_html(html_path)
    title = article["title"]
    tags = article["tags"]

    payload = json.dumps({
        "article": {
            "title": title,
            "body_html": body_html,
            "author": AUTHOR,
            "tags": tags,
            "published": True,
            "template_suffix": TEMPLATE_SUFFIX,
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

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_body = resp.read().decode("utf-8")
            data = json.loads(response_body)
            article_id = data.get("article", {}).get("id", "unknown")
            handle = data.get("article", {}).get("handle", article["slug"])
            log(f"SUCCESS: '{title}' -> id={article_id} handle={handle}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        log(f"HTTP_ERROR {e.code}: '{title}' -> {error_body[:300]}")
        return False
    except Exception as e:
        log(f"ERROR: '{title}' -> {str(e)}")
        return False


def main():
    log(f"=== Batch 2026-04-23 Publish Start ({len(ARTICLES)} articles) ===")
    success_count = 0
    fail_count = 0

    for i, article in enumerate(ARTICLES, 1):
        log(f"[{i}/{len(ARTICLES)}] Publishing: {article['title']}")
        ok = publish_article(article)
        if ok:
            success_count += 1
        else:
            fail_count += 1

        if i < len(ARTICLES):
            time.sleep(2)

    log(f"=== Batch Complete: {success_count} published, {fail_count} failed ===")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()

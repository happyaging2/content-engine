#!/usr/bin/env python3
"""
Batch publish script: 2026-04-24
Publishes 20 articles to Shopify blog ID 109440303424.
Run from content-engine root with SHOPIFY_TOKEN env var set.
UNSPLASH_ACCESS_KEY is used for cover images (optional).
PEXELS_API_KEY is the fallback if Unsplash returns no result.
"""

import os
import re
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SHOPIFY_STORE  = "shop-happy-aging.myshopify.com"
BLOG_ID        = "109440303424"
API_VERSION    = "2024-01"
SHOPIFY_TOKEN  = os.environ.get("SHOPIFY_TOKEN", "")
UNSPLASH_KEY   = os.environ.get("UNSPLASH_ACCESS_KEY", "")
PEXELS_KEY     = os.environ.get("PEXELS_API_KEY", "")
ARTICLES_DIR   = os.path.join(os.path.dirname(__file__))
LOG_FILE       = os.path.join(ARTICLES_DIR, "published.log")

# ---------------------------------------------------------------------------
# Article manifest
# ---------------------------------------------------------------------------
ARTICLES = [
    {
        "slug": "what-is-coq10-women-over-40",
        "title": "What Is CoQ10 and Why Do Women Over 40 Need It?",
        "tags": "Energy, CoQ10, Brain Health, Anti-Aging, Supplements, Mitochondria",
        "product_handle": "brain-tonic",
        "image_query": "woman over 40 energy vitality wellness",
    },
    {
        "slug": "coq10-dosage-guide-women-over-40",
        "title": "CoQ10 Dosage for Women Over 40: How Much Do You Actually Need?",
        "tags": "Energy, CoQ10, Supplements, Dosage, Heart Health, Mitochondria",
        "product_handle": "brain-tonic",
        "image_query": "woman taking supplement morning routine over 40",
    },
    {
        "slug": "berberine-vs-metformin-women-over-40",
        "title": "Berberine vs Metformin for Women Over 40: What the Research Shows",
        "tags": "Metabolism, Blood Sugar, Berberine, Insulin Resistance, Supplements, Women Over 40",
        "product_handle": "nad-advanced-longevity-formula",
        "image_query": "woman over 40 healthy lifestyle blood sugar wellness",
    },
    {
        "slug": "berberine-weight-loss-menopause",
        "title": "Can Berberine Help With Weight Loss After Menopause? What Research Shows",
        "tags": "Metabolism, Weight Loss, Berberine, Menopause, Blood Sugar, Gut Health",
        "product_handle": "happiest-gut",
        "image_query": "woman menopause healthy body weight wellness over 40",
    },
    {
        "slug": "mitochondria-weight-loss-after-40",
        "title": "Mitochondria and Weight Loss After 40: The Connection You Are Missing",
        "tags": "Metabolism, Weight Loss, Mitochondria, NAD+, Energy, Longevity",
        "product_handle": "longevity-shots",
        "image_query": "woman over 40 exercise energy cellular health",
    },
    {
        "slug": "astaxanthin-vs-vitamin-c-skin-after-40",
        "title": "Astaxanthin vs Vitamin C: Which Antioxidant Is Better for Skin After 40?",
        "tags": "Skin, Antioxidants, Astaxanthin, Vitamin C, Anti-Aging, Collagen",
        "product_handle": "radiance-tonic",
        "image_query": "woman over 40 glowing skin natural beauty antioxidant",
    },
    {
        "slug": "how-to-improve-skin-elasticity-after-40",
        "title": "How to Improve Skin Elasticity After 40 (What Science Actually Supports)",
        "tags": "Skin, Collagen, Elasticity, Anti-Aging, Marine Collagen, Supplements",
        "product_handle": "glow-shot",
        "image_query": "woman over 40 skin care collagen natural beauty",
    },
    {
        "slug": "collagen-and-bone-density-after-40",
        "title": "Can Collagen Actually Support Bone Density After 40? What Studies Show",
        "tags": "Bone Health, Collagen, Osteoporosis, Anti-Aging, Supplements, Women Over 40",
        "product_handle": "glow-shot",
        "image_query": "woman over 40 strong bones active outdoor lifestyle",
    },
    {
        "slug": "lions-mane-vs-other-brain-supplements-after-40",
        "title": "Lion's Mane vs Other Brain Supplements After 40: A Detailed Comparison",
        "tags": "Brain Health, Lion's Mane, Nootropics, Memory, Brain Fog, Supplements",
        "product_handle": "neuro-creamer",
        "image_query": "woman over 40 focus clarity brain health wellness",
    },
    {
        "slug": "phosphatidylserine-vs-lions-mane-memory-after-40",
        "title": "Phosphatidylserine vs Lion's Mane for Memory After 40: Which Works Better?",
        "tags": "Brain Health, Memory, Phosphatidylserine, Lion's Mane, Cognitive Health, Supplements",
        "product_handle": "neuro-creamer",
        "image_query": "woman over 40 reading memory focus mental clarity",
    },
    {
        "slug": "best-foods-liver-health-after-40",
        "title": "Best Foods for Liver Health After 40 (A Science-Backed Guide)",
        "tags": "Liver Health, Gut Health, Detox, Anti-Aging, Nutrition, Hormones",
        "product_handle": "liver-tonic",
        "image_query": "woman over 40 healthy eating vegetables liver health",
    },
    {
        "slug": "signs-of-leaky-gut-after-40",
        "title": "Signs You Have Leaky Gut After 40 (And What to Do About It)",
        "tags": "Gut Health, Leaky Gut, Digestion, Inflammation, Probiotics, Women Over 40",
        "product_handle": "happiest-gut",
        "image_query": "woman over 40 digestive health gut wellness nutrition",
    },
    {
        "slug": "what-is-l-theanine-women-over-40",
        "title": "What Is L-Theanine and Does It Help Women Over 40 Sleep and Focus?",
        "tags": "Sleep, Focus, L-Theanine, Stress, Brain Health, Supplements",
        "product_handle": "sleep-tonic",
        "image_query": "woman over 40 calm relaxed focus sleep wellness",
    },
    {
        "slug": "blood-sugar-hormones-connection-after-40",
        "title": "The Blood Sugar and Hormone Connection After 40: What You Need to Know",
        "tags": "Hormones, Blood Sugar, Insulin Resistance, Perimenopause, Metabolism, Cortisol",
        "product_handle": "nad-women-longevity-formula",
        "image_query": "woman over 40 hormones health wellness balanced lifestyle",
    },
    {
        "slug": "omega-3-hormone-balance-after-40",
        "title": "Omega-3 and Hormone Balance After 40: What the Research Actually Shows",
        "tags": "Hormones, Omega-3, Fish Oil, Perimenopause, Inflammation, Supplements",
        "product_handle": "nad-women-longevity-formula",
        "image_query": "woman over 40 omega-3 healthy eating fish nutrition",
    },
    {
        "slug": "how-poor-sleep-affects-hormones-after-40",
        "title": "How Poor Sleep Affects Your Hormones After 40 (And What to Do About It)",
        "tags": "Sleep, Hormones, Cortisol, Perimenopause, Magnesium, Women Over 40",
        "product_handle": "calm-tonic",
        "image_query": "woman over 40 restful sleep bedroom morning wellness",
    },
    {
        "slug": "does-fisetin-actually-work-after-40",
        "title": "Does Fisetin Actually Work for Aging? An Honest Review of the Human Evidence",
        "tags": "Longevity, Fisetin, Senolytics, Anti-Aging, Supplements, Cellular Health",
        "product_handle": "nad-advanced-longevity-formula",
        "image_query": "woman over 40 longevity aging well active lifestyle",
    },
    {
        "slug": "what-is-quercetin-women-over-40",
        "title": "What Is Quercetin and Why Women Over 40 Are Taking It",
        "tags": "Immunity, Quercetin, Anti-Aging, Inflammation, Supplements, Longevity",
        "product_handle": "relief-tonic",
        "image_query": "woman over 40 immune health anti-inflammatory wellness foods",
    },
    {
        "slug": "signs-your-body-is-detoxing-after-40",
        "title": "Signs Your Body Is Detoxing After 40 (What They Mean and What Helps)",
        "tags": "Detox, Liver Health, Immunity, Gut Health, Supplements, Women Over 40",
        "product_handle": "liver-tonic",
        "image_query": "woman over 40 detox healthy lifestyle liver health",
    },
    {
        "slug": "how-long-does-nmn-take-to-work",
        "title": "How Long Does NMN Take to Work? A Realistic Week-by-Week Timeline",
        "tags": "NMN, NAD+, Energy, Longevity, Supplements, Timeline",
        "product_handle": "nmn-cell-renew-tonic",
        "image_query": "woman over 40 energy NAD+ cellular health longevity",
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shopify_get(path):
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/{path}"
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return None


def shopify_post(path, payload):
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": body}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def fetch_product_image(handle):
    """Return first product image src for given handle, or None."""
    data = shopify_get(f"products.json?handle={handle}&fields=id,images")
    if not data or "products" not in data or not data["products"]:
        return None
    images = data["products"][0].get("images", [])
    return images[0]["src"] if images else None


def fetch_cover_image(query):
    """Try Unsplash then Pexels; return (url, credit_html) or (None, '')."""
    # Unsplash
    if UNSPLASH_KEY:
        q = urllib.parse.quote(query)
        url = (
            f"https://api.unsplash.com/search/photos"
            f"?query={q}&per_page=1&orientation=landscape"
            f"&client_id={UNSPLASH_KEY}"
        )
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.loads(r.read())
            results = d.get("results", [])
            if results:
                photo = results[0]
                img_url = photo["urls"]["regular"]
                name = photo["user"]["name"]
                link = photo["links"]["html"] + "?utm_source=happy_aging&utm_medium=referral"
                credit = (
                    f'Photo by <a href="{photo["user"]["links"]["html"]}'
                    f'?utm_source=happy_aging&utm_medium=referral">{name}</a>'
                    f' on <a href="{link}">Unsplash</a>'
                )
                return img_url, credit
        except Exception:
            pass

    # Pexels fallback
    if PEXELS_KEY:
        q = urllib.parse.quote(query)
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=1&orientation=landscape"
        req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                d = json.loads(r.read())
            photos = d.get("photos", [])
            if photos:
                photo = photos[0]
                img_url = photo["src"]["large"]
                name = photo["photographer"]
                link = photo["url"]
                credit = f'Photo by <a href="{link}">{name}</a> on Pexels'
                return img_url, credit
        except Exception:
            pass

    return None, ""


def read_html(slug):
    path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not SHOPIFY_TOKEN:
        print("ERROR: SHOPIFY_TOKEN env var not set.")
        sys.exit(1)

    log(f"=== Batch 2026-04-24 publish started ({len(ARTICLES)} articles) ===")

    success_count = 0
    fail_count = 0

    for i, article in enumerate(ARTICLES, 1):
        slug = article["slug"]
        log(f"[{i:02d}/{len(ARTICLES)}] Processing: {slug}")

        # 1. Read HTML
        try:
            body_html = read_html(slug)
        except FileNotFoundError:
            log(f"  ERROR: HTML file not found for {slug}")
            fail_count += 1
            continue

        # 2. Fetch product image and replace placeholder
        product_img = fetch_product_image(article["product_handle"])
        if product_img:
            body_html = body_html.replace("FETCH_FROM_API", product_img)
            log(f"  Product image fetched: {product_img[:60]}...")
        else:
            log(f"  WARNING: Could not fetch product image for {article['product_handle']}")
            body_html = body_html.replace('src="FETCH_FROM_API"', 'src=""')

        # 3. Fetch cover image
        cover_url, cover_credit = fetch_cover_image(article["image_query"])
        if cover_url:
            log(f"  Cover image fetched: {cover_url[:60]}...")
        else:
            log(f"  WARNING: No cover image found for query: {article['image_query']}")

        # 4. Build payload
        payload = {
            "article": {
                "title": article["title"],
                "author": "Happy Aging Team",
                "body_html": body_html,
                "tags": article["tags"],
                "published": True,
                "template_suffix": "timeline",
            }
        }
        if cover_url:
            payload["article"]["image"] = {"src": cover_url, "alt": article["title"]}

        # 5. POST to Shopify
        result, status = shopify_post(f"blogs/{BLOG_ID}/articles.json", payload)

        if status in (200, 201) and "article" in result:
            article_id = result["article"]["id"]
            handle = result["article"].get("handle", slug)
            url = f"https://happyaging.com/blogs/news/{handle}"
            log(f"  SUCCESS: id={article_id} url={url}")
            success_count += 1
        else:
            log(f"  FAILED: status={status} error={str(result)[:200]}")
            fail_count += 1

        # Shopify rate limit: 2 calls/sec sustained; 1 article = 1 POST + up to 2 GETs
        time.sleep(2)

    log(
        f"=== Batch complete: {success_count} published, {fail_count} failed ==="
    )


if __name__ == "__main__":
    main()

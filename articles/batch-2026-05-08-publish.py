#!/usr/bin/env python3
"""
Batch 2026-05-08 Publisher — 20 articles
Publishes all batch-27 articles to Shopify via REST API.
Usage: SHOPIFY_TOKEN=shpat_... python3 batch-2026-05-08-publish.py
"""
import os, json, time, requests

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "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")
STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
API_URL = f"https://{STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))

ARTICLES = [
    {"slug": "nmn-timing-guide-after-40",           "title": "Best Time to Take NMN After 40: Morning, Night, and With Food"},
    {"slug": "how-long-nmn-works-after-40",          "title": "How Long Until NMN Works? A Week-by-Week Timeline for Women Over 40"},
    {"slug": "nad-decline-pathways-after-40",        "title": "NAD+ Decline After 40: The 5 Key Pathways Science Has Confirmed"},
    {"slug": "sirtuins-nad-after-40",                "title": "Sirtuins After 40: What They Are and Why They Matter for Aging"},
    {"slug": "why-sleep-worsens-after-40",           "title": "Why Sleep Gets Harder Every Decade After 40 (And What to Do)"},
    {"slug": "magnesium-glycinate-sleep-after-40",   "title": "Magnesium Glycinate for Sleep After 40: The Complete Guide"},
    {"slug": "autophagy-after-40-guide",             "title": "Autophagy After 40: How to Trigger Your Body's Cellular Cleanup System"},
    {"slug": "telomere-length-after-40",             "title": "Telomere Length After 40: What Shortens Them and How to Slow the Decline"},
    {"slug": "urolithin-a-after-40",                 "title": "Urolithin A After 40: The Mitochondria Compound Getting Scientists Excited"},
    {"slug": "cortisol-reset-protocol-after-40",     "title": "Cortisol Reset Protocol for Women Over 40: A Daily Plan"},
    {"slug": "glycine-sleep-hormones-after-40",      "title": "Glycine for Sleep and Hormones After 40: What the Research Shows"},
    {"slug": "thyroid-health-after-40",              "title": "Thyroid Health After 40: Why It Changes and What Supports It"},
    {"slug": "best-nootropics-women-over-40",        "title": "Best Nootropics for Women Over 40: Ranked by Evidence"},
    {"slug": "improve-concentration-after-40",       "title": "How to Improve Focus and Concentration After 40: What Really Works"},
    {"slug": "best-prebiotic-foods-after-40",        "title": "Best Prebiotic Foods for Gut Health After 40: A Complete Guide"},
    {"slug": "reduce-bloating-after-40",             "title": "How to Reduce Bloating After 40: Root Causes and Evidence-Based Solutions"},
    {"slug": "supplements-hair-thinning-after-40",   "title": "Best Supplements for Hair Thinning After 40: Ranked by Evidence"},
    {"slug": "morning-energy-routine-after-40",      "title": "Morning Energy Routine for Women Over 40: What Science Recommends"},
    {"slug": "creatine-women-over-40",               "title": "Creatine for Women Over 40: The Unexpected Benefits Beyond Muscle"},
    {"slug": "blood-sugar-timing-after-40",          "title": "Blood Sugar Balance After 40: The Meal Timing Strategy That Works"},
]

results = []
headers = {
    "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    "Content-Type": "application/json"
}

for i, art in enumerate(ARTICLES):
    slug = art["slug"]
    title = art["title"]
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")

    if not os.path.exists(html_path):
        print(f"[{i+1}/20] SKIP (no html): {slug}")
        results.append({"slug": slug, "status": "SKIP", "reason": "no html"})
        continue

    body_html = open(html_path).read()
    meta = {}
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path))

    tags = meta.get("tags", "longevity, women over 40, wellness, happy aging")
    summary = meta.get("summary_html", "")

    payload = {
        "article": {
            "title": title,
            "body_html": body_html,
            "author": "Happy Aging Team",
            "tags": tags,
            "published": True,
            "template_suffix": "timeline",
        }
    }
    if summary:
        payload["article"]["summary_html"] = summary

    print(f"[{i+1}/20] Publishing: {slug} ...", end="", flush=True)
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 201:
            art_id = resp.json()["article"]["id"]
            print(f" OK (id={art_id})")
            results.append({"slug": slug, "status": "OK", "article_id": art_id, "title": title})
        else:
            print(f" FAIL ({resp.status_code}): {resp.text[:120]}")
            results.append({"slug": slug, "status": "FAIL", "code": resp.status_code, "error": resp.text[:200]})
    except Exception as e:
        print(f" ERROR: {e}")
        results.append({"slug": slug, "status": "ERROR", "error": str(e)})

    time.sleep(2)  # Rate limit

# Save results
results_path = os.path.join(ARTICLES_DIR, "batch-2026-05-08-publish-results.json")
with open(results_path, "w") as f:
    json.dump(results, f, indent=2)

ok = sum(1 for r in results if r["status"] == "OK")
fail = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
skip = sum(1 for r in results if r["status"] == "SKIP")
print(f"\n=== PUBLISH COMPLETE: {ok} OK | {fail} FAIL | {skip} SKIP ===")
print(f"Results saved to: {results_path}")

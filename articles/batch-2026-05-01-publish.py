#!/usr/bin/env python3
"""
Batch publish script for 2026-05-01 articles to Shopify.
Run in an environment with network access:
  SHOPIFY_TOKEN=shpat_xxx PEXELS_API_KEY=xxx python3 batch-2026-05-01-publish.py
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID = "109440303424"
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
AUTHOR = "Happy Aging Team"

ARTICLES_DIR = os.path.dirname(os.path.abspath(__file__))

BATCH = [
    "does-spermidine-work-after-40",
    "dhea-aging-women-research-after-40",
    "black-cohosh-menopause-symptoms-after-40",
    "cortisol-belly-fat-after-40",
    "how-to-boost-bdnf-naturally-after-40",
    "best-foods-brain-health-after-40",
    "creatine-brain-health-women-after-40",
    "butyrate-gut-brain-axis-after-40",
    "serotonin-gut-mood-connection-after-40",
    "how-stress-disrupts-digestion-after-40",
    "signs-strength-training-working-after-40",
    "acetyl-l-carnitine-vs-l-carnitine-after-40",
    "nitric-oxide-cardiovascular-health-after-40",
    "magnesium-migraines-after-40",
    "low-histamine-diet-perimenopause-after-40",
    "pcos-perimenopause-changes-after-40",
    "what-is-pea-pain-inflammation-after-40",
    "nad-plus-dna-repair-after-40",
    "melatonin-vs-l-theanine-sleep-after-40",
    "what-is-nac-glutathione-after-40",
]

BLOCKED_TERMS = [
    "supplement", "bottle", "product", "vitamin", "pill", "capsule", "tablet",
    "medication", "drug", "medicine", "injection", "syringe", "doctor", "hospital",
    "tattoo", "nude", "naked", "topless", "man ", "men ", "male ", "boy ",
]

COMPETITOR_BRANDS = [
    "thorne", "jarrow", "gnc", "osh wellness", "vigorvault", "missha",
    "life extension", "pure encapsulations", "designs for health",
]


def is_safe_image(url, alt=""):
    text = (url + " " + alt).lower()
    for term in BLOCKED_TERMS + COMPETITOR_BRANDS:
        if term in text:
            return False
    return True


def fetch_pexels_image(query, orientation="landscape"):
    if not PEXELS_API_KEY:
        return None, None
    safe_query = re.sub(r'[^\w\s]', '', query)[:100]
    url = f"https://api.pexels.com/v1/search?query={urllib.request.quote(safe_query)}&per_page=15&orientation={orientation}"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for photo in data.get("photos", []):
            img_url = photo["src"]["large2x"]
            alt = photo.get("alt", "")
            photographer = photo.get("photographer", "")
            if is_safe_image(img_url, alt + " " + photographer):
                return img_url, alt
    except Exception as e:
        print(f"  Pexels error for '{query}': {e}")
    return None, None


def fetch_unsplash_image(query):
    if not UNSPLASH_KEY:
        return None, None
    safe_query = re.sub(r'[^\w\s]', '', query)[:100]
    url = f"https://api.unsplash.com/search/photos?query={urllib.request.quote(safe_query)}&per_page=10&orientation=landscape"
    req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for photo in data.get("results", []):
            img_url = photo["urls"]["regular"]
            alt = photo.get("alt_description", "") or ""
            if is_safe_image(img_url, alt):
                return img_url, alt
    except Exception as e:
        print(f"  Unsplash error for '{query}': {e}")
    return None, None


def get_image(query):
    img_url, alt = fetch_pexels_image(query)
    if img_url:
        return img_url, alt
    img_url, alt = fetch_unsplash_image(query)
    if img_url:
        return img_url, alt
    return None, None


def inject_faq_schema(html, title):
    faq_pairs = re.findall(r'<h3>(.*?)</h3>\s*<p>(.*?)</p>', html, re.DOTALL)
    if not faq_pairs:
        return html
    items = []
    for q, a in faq_pairs:
        q_clean = re.sub(r'<[^>]+>', '', q).strip()
        a_clean = re.sub(r'<[^>]+>', '', a).replace('"', '\\"').strip()
        a_clean = a_clean.replace('\n', ' ').replace('\r', '')
        items.append(f'    {{"@type": "Question", "name": "{q_clean}", "acceptedAnswer": {{"@type": "Answer", "text": "{a_clean}"}}}}')
    schema = '{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [\n' + ',\n'.join(items) + '\n]}'
    script_tag = f'<script type="application/ld+json">\n{schema}\n</script>\n'
    faq_h2 = '<h2>Frequently Asked Questions</h2>'
    if faq_h2 in html:
        html = html.replace(faq_h2, script_tag + faq_h2)
    return html


def inject_meta_description(html, body_html):
    first_p = re.search(r'<p>(.*?)</p>', body_html, re.DOTALL)
    if not first_p:
        return html
    text = re.sub(r'<[^>]+>', '', first_p.group(1)).strip()
    text = ' '.join(text.split())
    if len(text) > 155:
        text = text[:152] + '...'
    return html


def inject_section_images(body_html, meta):
    h2s = re.findall(r'<h2>(.*?)</h2>', body_html)
    skipped = {"Frequently Asked Questions", "References"}
    eligible = [h for h in h2s if h not in skipped and h != h2s[0]]
    image_queries = []
    for h in eligible[:3]:
        keyword = re.sub(r'[^\w\s]', '', h).strip().lower()
        image_queries.append(keyword + " women health lifestyle")
    injected = body_html
    for i, query in enumerate(image_queries[:3]):
        if i >= len(eligible):
            break
        h2_text = eligible[i]
        img_url, alt = get_image(query)
        if not img_url:
            continue
        safe_alt = re.sub(r'[^\w\s\-,]', '', alt or h2_text)[:120]
        img_tag = f'<img src="{img_url}" alt="{safe_alt}" style="width:100%;border-radius:8px;margin:16px 0;">\n'
        target = f'<h2>{h2_text}</h2>'
        injected = injected.replace(target, f'{target}\n{img_tag}', 1)
    return injected


def publish_article(slug):
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")

    if not os.path.exists(meta_path):
        print(f"  ERROR: missing {meta_path}")
        return None
    if not os.path.exists(html_path):
        html_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
    if not os.path.exists(html_path):
        print(f"  ERROR: missing HTML for {slug}")
        return None

    with open(meta_path) as f:
        meta = json.load(f)
    with open(html_path) as f:
        body_html = f.read()

    title = meta.get("title", slug)
    tags = meta.get("tags", "")

    # Fetch cover image
    cover_query = meta.get("image_query", "woman health wellness lifestyle")
    image_prompt = meta.get("image_prompt", "")
    if image_prompt:
        cover_query = "woman in her 40s wellness healthy lifestyle"
    cover_url, cover_alt = get_image(cover_query)

    # Inject FAQ schema
    body_html = inject_faq_schema(body_html, title)

    # Inject section images
    body_html = inject_section_images(body_html, meta)

    payload = {
        "article": {
            "title": title,
            "author": AUTHOR,
            "body_html": body_html,
            "tags": tags,
            "published": True,
            "template_suffix": "timeline",
        }
    }

    if cover_url:
        payload["article"]["image"] = {
            "src": cover_url,
            "alt": (cover_alt or title)[:512],
        }

    url = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "X-Shopify-Access-Token": SHOPIFY_TOKEN,
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            article_id = result["article"]["id"]
            handle = result["article"]["handle"]
            print(f"  PUBLISHED: {title}")
            print(f"    ID={article_id} | handle={handle}")
            return {"slug": slug, "id": article_id, "handle": handle, "title": title}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP ERROR {e.code} for {slug}: {body[:300]}")
        return None
    except Exception as e:
        print(f"  ERROR publishing {slug}: {e}")
        return None


def main():
    if not SHOPIFY_TOKEN:
        print("ERROR: SHOPIFY_TOKEN not set")
        sys.exit(1)

    print(f"Publishing batch 2026-05-01 ({len(BATCH)} articles)")
    print(f"Store: {SHOPIFY_STORE} | Blog: {BLOG_ID}")
    print("-" * 60)

    results = []
    for i, slug in enumerate(BATCH, 1):
        print(f"\n[{i}/{len(BATCH)}] {slug}")
        result = publish_article(slug)
        if result:
            results.append(result)
        # Respect Shopify rate limit (2 req/sec for REST)
        time.sleep(0.6)

    print("\n" + "=" * 60)
    print(f"DONE: {len(results)}/{len(BATCH)} articles published successfully")
    if len(results) < len(BATCH):
        published_slugs = {r["slug"] for r in results}
        failed = [s for s in BATCH if s not in published_slugs]
        print(f"FAILED: {failed}")

    # Save results
    results_path = os.path.join(ARTICLES_DIR, "batch-2026-05-01-results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_path}")


if __name__ == "__main__":
    main()

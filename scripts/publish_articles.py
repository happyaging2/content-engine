#!/usr/bin/env python3
"""
JARVIS Publisher - Phase 5
Publishes articles to Shopify as DRAFT posts.
"""

import json
import re
import os
import time
import subprocess
import tempfile
from datetime import datetime, timezone

ARTICLES_DIR = "/home/user/content-engine/articles"
SHOPIFY_ENDPOINT = "https://shop-happy-aging.myshopify.com/admin/api/2024-01/blogs/109440303424/articles.json"
SHOPIFY_TOKEN = "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"
LOG_FILE = "/home/user/content-engine/articles/published.log"

CDN_FALLBACK = {
    "nad-advanced-longevity-formula": "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/nad-advanced-protocol.jpg",
    "sleep-tonic": "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/sleep-tonic.jpg",
    "happiest-gut": "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/happiest-gut.jpg",
    "calm-tonic": "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/calm-tonic.jpg",
}
DEFAULT_IMAGE = "https://cdn.shopify.com/s/files/1/0869/3704/3264/files/nad-advanced-protocol.jpg"

SLUGS = [
    "nmnh-reduced-nmn-supplement-women-over-40",
    "nad-precursors-compared-nr-nmn-nmnh-niacin-women-40",
    "sauna-therapy-longevity-women-over-40",
    "vo2-max-longevity-women-over-40",
    "zone-2-cardio-nad-aging-women-over-40",
    "hrv-heart-rate-variability-biological-aging-women-40",
    "bloating-after-40-step-by-step-guide-women",
    "hot-flash-supplements-compared-women-over-40",
    "cold-therapy-women-over-40-ice-bath-benefits",
    "nad-muscle-loss-menopause-women-over-40",
    "epigenetic-age-testing-biological-age-women-over-40",
    "nad-plus-skin-aging-complexion-women-over-40",
    "glp-1-foods-supplements-satiety-women-over-40",
    "night-sweats-after-40-natural-solutions-women",
    "estrogen-sleep-architecture-after-40-women",
    "supplement-timing-guide-women-over-40",
    "gut-microbiome-immunity-after-menopause-women",
    "30-day-longevity-reset-plan-women-over-40",
    "zinc-hormonal-health-women-over-40",
    "heart-health-supplements-women-over-40",
]


def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(message)


def read_meta(slug):
    meta_path = os.path.join(ARTICLES_DIR, f"{slug}.meta.json")
    with open(meta_path, "r") as f:
        return json.load(f)


def read_body_html(slug):
    html_path = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    if content.lstrip().startswith("<!DOCTYPE html") or content.lstrip().startswith("<html"):
        match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            # Try to return everything after <body if no closing tag
            match2 = re.search(r'<body[^>]*>(.*)', content, re.DOTALL)
            if match2:
                return match2.group(1).strip()
    return content


def get_image_url(meta):
    # Try product_image_url from meta first
    if meta.get("product_image_url"):
        return meta["product_image_url"]
    # Try to match hero_product in meta
    hero = meta.get("hero_product", "")
    for key, url in CDN_FALLBACK.items():
        if key in hero:
            return url
    # Default fallback
    return DEFAULT_IMAGE


def publish_article(slug, index, total):
    print(f"\n[{index}/{total}] Processing: {slug}")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        meta = read_meta(slug)
    except Exception as e:
        msg = f"{timestamp} | {slug} | ERROR: Failed to read meta.json: {e}"
        log(msg)
        return None, False

    try:
        body_html = read_body_html(slug)
    except Exception as e:
        msg = f"{timestamp} | {slug} | ERROR: Failed to read final.html: {e}"
        log(msg)
        return None, False

    title = meta.get("title", slug)
    tags = meta.get("tags", "")
    if isinstance(tags, list):
        tags = ", ".join(tags)
    image_url = get_image_url(meta)

    print(f"  Title: {title}")
    print(f"  Image: {image_url}")
    print(f"  Body size: {len(body_html)} chars")
    print(f"  Tags: {tags[:80]}...")

    payload = {
        "article": {
            "title": title,
            "body_html": body_html,
            "author": "Happy Aging Team",
            "tags": tags,
            "published": False,
            "template_suffix": "timeline",
            "image": {
                "src": image_url,
                "alt": title
            }
        }
    }

    # Write payload to temp file to avoid shell escaping issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tf:
        json.dump(payload, tf, ensure_ascii=False)
        temp_path = tf.name

    try:
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                SHOPIFY_ENDPOINT,
                "-H", f"X-Shopify-Access-Token: {SHOPIFY_TOKEN}",
                "-H", "Content-Type: application/json",
                "--data", f"@{temp_path}",
                "--max-time", "60",
                "-w", "\n__HTTP_STATUS__:%{http_code}"
            ],
            capture_output=True, text=True, timeout=90
        )

        output = result.stdout
        # Extract HTTP status code appended at end
        http_status = None
        if "__HTTP_STATUS__:" in output:
            parts = output.rsplit("\n__HTTP_STATUS__:", 1)
            output = parts[0]
            http_status = parts[1].strip()

        print(f"  HTTP Status: {http_status}")

        # Handle rate limiting
        if http_status == "429":
            print("  Rate limited! Sleeping 2 seconds and retrying...")
            time.sleep(2)
            result2 = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    SHOPIFY_ENDPOINT,
                    "-H", f"X-Shopify-Access-Token: {SHOPIFY_TOKEN}",
                    "-H", "Content-Type: application/json",
                    "--data", f"@{temp_path}",
                    "--max-time", "60",
                    "-w", "\n__HTTP_STATUS__:%{http_code}"
                ],
                capture_output=True, text=True, timeout=90
            )
            output = result2.stdout
            if "__HTTP_STATUS__:" in output:
                parts = output.rsplit("\n__HTTP_STATUS__:", 1)
                output = parts[0]
                http_status = parts[1].strip()
            print(f"  Retry HTTP Status: {http_status}")

        try:
            response_data = json.loads(output)
        except json.JSONDecodeError as e:
            msg = f"{timestamp} | {slug} | ERROR: Invalid JSON response (HTTP {http_status}): {output[:200]}"
            log(msg)
            return None, False

        if "article" in response_data:
            article_id = response_data["article"]["id"]
            msg = f"{timestamp} | {slug} | id={article_id} | status=draft"
            log(msg)
            print(f"  SUCCESS: Shopify article id={article_id}")
            return article_id, True
        else:
            errors = response_data.get("errors", response_data)
            msg = f"{timestamp} | {slug} | ERROR: {json.dumps(errors)[:300]}"
            log(msg)
            print(f"  FAILED: {errors}")
            return None, False

    except subprocess.TimeoutExpired:
        msg = f"{timestamp} | {slug} | ERROR: curl timeout"
        log(msg)
        return None, False
    except Exception as e:
        msg = f"{timestamp} | {slug} | ERROR: {e}"
        log(msg)
        return None, False
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass


def main():
    print("=" * 60)
    print("JARVIS Publisher - Phase 5")
    print(f"Publishing {len(SLUGS)} articles to Shopify as DRAFT")
    print("=" * 60)

    log(f"\n{'='*60}")
    log(f"JARVIS Publisher run started at {datetime.now(timezone.utc).isoformat()}")
    log(f"{'='*60}")

    succeeded = []
    failed = []

    for i, slug in enumerate(SLUGS, 1):
        article_id, success = publish_article(slug, i, len(SLUGS))
        if success:
            succeeded.append((slug, article_id))
        else:
            failed.append(slug)

        # Small delay between articles to be respectful of rate limits
        if i < len(SLUGS):
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print("PUBLISH SUMMARY")
    print("=" * 60)
    print(f"Succeeded: {len(succeeded)}/{len(SLUGS)}")
    print(f"Failed:    {len(failed)}/{len(SLUGS)}")

    if succeeded:
        print("\nSuccessful articles:")
        for slug, aid in succeeded:
            print(f"  id={aid} | {slug}")

    if failed:
        print("\nFailed articles:")
        for slug in failed:
            print(f"  {slug}")

    summary = f"\nSUMMARY: {len(succeeded)} succeeded, {len(failed)} failed"
    log(summary)
    if succeeded:
        for slug, aid in succeeded:
            log(f"  OK  id={aid} | {slug}")
    if failed:
        for slug in failed:
            log(f"  FAIL | {slug}")


if __name__ == "__main__":
    main()

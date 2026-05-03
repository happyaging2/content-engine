#!/usr/bin/env python3
"""Add image_query and body_image_queries to batch 2026-05-02 meta.json files.

These fields are required by qa-and-publish.sh and update-images.py.
Queries are short lifestyle phrases suitable for Pexels/Unsplash searches.
NO supplement/bottle/product/pill/vitamin language per brand safety rules.
"""

import json
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent.parent / "articles"

QUERIES = {
    "vitamin-d-bone-health-women-after-40": {
        "image_query": "woman hiking outdoors sunlight",
        "body_image_queries": [
            "woman yoga morning light",
            "healthy salad greens meal",
            "woman walking beach sunset",
        ],
    },
    "calcium-absorption-after-40-women": {
        "image_query": "woman eating yogurt bright kitchen",
        "body_image_queries": [
            "leafy greens plate healthy food",
            "woman jogging park morning",
            "woman cooking vegetables kitchen",
        ],
    },
    "omega-3-joint-health-after-40": {
        "image_query": "woman swimming pool morning exercise",
        "body_image_queries": [
            "salmon vegetables dinner plate",
            "woman doing yoga stretching",
            "woman walking nature trail",
        ],
    },
    "berberine-vs-inositol-insulin-resistance-after-40": {
        "image_query": "woman healthy breakfast table morning",
        "body_image_queries": [
            "woman outdoor morning walk",
            "balanced meal vegetables grains",
            "woman relaxing home wellness",
        ],
    },
    "berberine-gut-health-microbiome-after-40": {
        "image_query": "woman eating fermented food kitchen",
        "body_image_queries": [
            "yogurt berries breakfast bowl",
            "woman garden morning walk",
            "woman preparing healthy meal",
        ],
    },
    "stress-eating-after-40-women": {
        "image_query": "woman relaxing garden mindful afternoon",
        "body_image_queries": [
            "woman meditation outdoor morning",
            "healthy snacks fruit colorful plate",
            "woman journaling quiet home",
        ],
    },
    "magnesium-glycinate-vs-malate-women-over-40": {
        "image_query": "woman peaceful sleep bedroom morning",
        "body_image_queries": [
            "woman relaxing evening home cozy",
            "green vegetables nuts healthy meal",
            "woman morning routine kitchen calm",
        ],
    },
    "does-coq10-help-energy-honest-review-after-40": {
        "image_query": "woman energized morning outdoor workout",
        "body_image_queries": [
            "woman running park trail",
            "healthy breakfast eggs avocado",
            "woman working desk focused",
        ],
    },
    "signs-you-need-more-copper-after-40": {
        "image_query": "woman outdoor lifestyle wellness portrait",
        "body_image_queries": [
            "nuts seeds healthy food bowl",
            "woman cooking dark leafy greens",
            "woman confident portrait natural light",
        ],
    },
    "signs-you-need-more-b6-after-40": {
        "image_query": "woman confident morning routine kitchen",
        "body_image_queries": [
            "healthy foods chickpeas fish meal",
            "woman journaling morning sunlight",
            "woman outdoor walk energized",
        ],
    },
    "what-is-ampk-longevity-after-40": {
        "image_query": "woman hiking mountain trail nature",
        "body_image_queries": [
            "woman exercising outdoor morning",
            "healthy colorful vegetables plate",
            "woman meditating sunrise outdoor",
        ],
    },
    "what-are-telomeres-aging-after-40": {
        "image_query": "woman running outdoor healthy lifestyle",
        "body_image_queries": [
            "woman yoga peaceful garden",
            "healthy breakfast morning meal",
            "woman walking nature path",
        ],
    },
    "does-nmn-actually-work-honest-review-after-40": {
        "image_query": "woman vibrant outdoor morning energy",
        "body_image_queries": [
            "woman cycling park morning",
            "healthy colorful food bowl",
            "woman relaxing garden afternoon",
        ],
    },
    "how-to-improve-focus-concentration-after-40": {
        "image_query": "woman focused working home office",
        "body_image_queries": [
            "woman reading book sunlit room",
            "healthy brain food walnuts berries",
            "woman meditation morning quiet",
        ],
    },
    "what-is-alpha-gpc-memory-after-40": {
        "image_query": "woman writing journal morning light",
        "body_image_queries": [
            "woman reading studying natural light",
            "healthy brain foods eggs greens",
            "woman outdoor walking focused",
        ],
    },
    "retinol-after-40-women-guide": {
        "image_query": "woman skincare morning bathroom portrait",
        "body_image_queries": [
            "woman applying moisturizer bathroom mirror",
            "natural skincare oils ingredients",
            "woman outdoor portrait glowing skin",
        ],
    },
    "what-is-inositol-women-over-40": {
        "image_query": "woman meditation indoor morning light",
        "body_image_queries": [
            "healthy grains beans colorful meal",
            "woman journaling wellness routine",
            "woman evening stroll neighborhood",
        ],
    },
    "exercise-heart-health-women-after-40": {
        "image_query": "woman jogging park morning fitness",
        "body_image_queries": [
            "woman cycling outdoor trail",
            "heart healthy meal vegetables colorful",
            "woman yoga outdoor balance",
        ],
    },
    "alcohol-liver-health-after-40-women": {
        "image_query": "woman outdoor morning tea wellness",
        "body_image_queries": [
            "woman drinking water healthy lifestyle",
            "healthy food vegetables fruits colorful",
            "woman walking park sunset",
        ],
    },
    "what-is-pqq-brain-energy-after-40": {
        "image_query": "woman home office focused productive",
        "body_image_queries": [
            "woman eating berries healthy breakfast",
            "woman jogging residential morning",
            "woman creative work desk plants",
        ],
    },
}


def main():
    updated = 0
    skipped = 0
    errors = 0

    for slug, queries in QUERIES.items():
        meta_path = ARTICLES_DIR / f"{slug}.meta.json"
        if not meta_path.exists():
            print(f"MISSING: {slug}.meta.json")
            errors += 1
            continue

        data = json.loads(meta_path.read_text())

        if "image_query" in data and "body_image_queries" in data:
            print(f"SKIP (already has queries): {slug}")
            skipped += 1
            continue

        data["image_query"] = queries["image_query"]
        data["body_image_queries"] = queries["body_image_queries"]

        meta_path.write_text(json.dumps(data, indent=2) + "\n")
        print(f"UPDATED: {slug}")
        updated += 1

    print(f"\nDone — updated: {updated}, skipped: {skipped}, errors: {errors}")


if __name__ == "__main__":
    main()

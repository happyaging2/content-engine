#!/usr/bin/env python3
"""Remove brand-unsafe terms from image_query / body_image_queries in all meta.json files.

Rules (from CLAUDE.md and brand guidelines):
  - NO supplement, vitamin, pill, capsule, bottle, vial, jar, tube, container,
    product, serum, medicine, pharmacy, clinic, hospital
  - NO "holding" (hands holding anything)
  - NO tattoo, nude, naked, topless, bikini, lingerie, scar, wound, surgery

When a query is unsafe, replace it with a safe fallback derived from the slug.
"""

import json
import re
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent.parent / "articles"

# Single-word blocked terms: matched as whole words (avoids "productive" → "product" false positive)
BLOCKED_WORDS = {
    "supplement", "vitamin", "pill", "capsule", "tablet", "dose", "bottle",
    "vial", "jar", "tube", "container", "packaging", "product", "serum",
    "medicine", "pharmacy", "clinic", "hospital", "holding", "surgery",
    "scar", "wound", "tattoo", "nude", "naked", "topless", "bikini",
    "lingerie", "advertisement",
}

# Multi-word phrases: still matched as substrings
BLOCKED_PHRASES = {
    "holding bottle", "holding supplement", "holding vial", "holding product",
    "holding jar", "holding tube", "with supplement", "with bottle",
    "supplement bottle", "serum bottle", "pill box", "medical office",
    "fast food", "junk food",
}

# Build a combined regex for fast whole-word checking
_BLOCKED_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(BLOCKED_WORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def is_unsafe(query: str) -> bool:
    if _BLOCKED_RE.search(query):
        return True
    q = query.lower()
    return any(p in q for p in BLOCKED_PHRASES)


# Safe replacement queries by article topic keyword (slug match)
# These are the fallback when the extracted query is unsafe.
SAFE_FALLBACKS = {
    "supplement": "woman healthy morning routine outdoor",
    "bone": "woman hiking outdoors sunshine",
    "collagen": "woman glowing skin portrait natural light",
    "skin": "woman skincare morning bathroom portrait",
    "serum": "woman skincare morning portrait light",
    "joint": "woman yoga flexibility outdoor morning",
    "vitamin-d": "woman hiking outdoors sunlight",
    "vitamin-c": "woman eating citrus fruit healthy kitchen",
    "vitamin-k": "woman eating dark leafy greens kitchen",
    "vitamin-e": "woman outdoor morning walk healthy",
    "calcium": "woman eating dairy yogurt healthy kitchen",
    "magnesium": "woman peaceful sleep bedroom morning",
    "iron": "woman energized outdoor morning active",
    "zinc": "woman cooking healthy kitchen vegetables",
    "selenium": "woman eating Brazil nuts healthy snack",
    "copper": "woman outdoor lifestyle wellness portrait",
    "b12": "woman energized morning kitchen routine",
    "omega": "woman eating salmon grilled healthy meal",
    "coq10": "woman energized morning outdoor walk",
    "nad": "woman vibrant outdoor morning energy",
    "nmn": "woman cycling park morning",
    "berberine": "woman healthy breakfast table morning",
    "curcumin": "woman outdoor morning lifestyle wellness",
    "quercetin": "woman eating colorful berries fruit",
    "resveratrol": "woman outdoor active healthy lifestyle",
    "ashwagandha": "woman hiking peaceful mountain trail",
    "probiotics": "woman eating yogurt bowl kitchen",
    "glutathione": "woman outdoor morning healthy lifestyle",
    "creatine": "woman exercising gym outdoor active",
    "collagen": "woman glowing skin portrait natural light",
    "melatonin": "woman sleeping peacefully bedroom evening",
    "l-theanine": "woman calm focused indoor morning",
    "gaba": "woman sleeping peacefully bedroom night",
    "inositol": "woman meditation indoor morning light",
    "liver": "woman outdoor morning healthy lifestyle",
    "heart": "woman jogging park morning fitness",
    "brain": "woman focused reading home office",
    "memory": "woman writing journal morning light",
    "focus": "woman focused home office working",
    "energy": "woman energized outdoor morning active",
    "sleep": "woman sleeping peaceful bedroom morning",
    "stress": "woman calm outdoor garden afternoon",
    "gut": "woman eating healthy fermented food",
    "hormone": "woman outdoor morning confident wellness",
    "metabolism": "woman outdoor morning exercise active",
    "immune": "woman outdoor nature fresh air smiling",
    "inflammation": "woman eating colorful vegetables kitchen",
    "detox": "woman drinking water lemon morning",
    "fasting": "woman healthy morning routine kitchen",
    "weight": "woman outdoor morning walk confident",
    "muscle": "woman strength training outdoor morning",
    "thyroid": "woman healthy morning routine outdoor",
    "estrogen": "woman outdoor morning confident walk",
    "progesterone": "woman relaxing peaceful home evening",
    "cortisol": "woman calm outdoor garden afternoon",
    "perimenopause": "woman midlife portrait smiling outdoor",
    "menopause": "woman outdoor morning confident active",
    "aging": "woman vibrant outdoor active healthy",
    "longevity": "woman hiking mountain trail nature",
    "elderberry": "woman outdoor garden picking berries",
    "protein": "woman healthy meal kitchen eating",
    "fish-oil": "woman eating salmon healthy meal",
    "liposomal": "woman healthy morning routine kitchen",
    "retinol": "woman skincare morning bathroom portrait",
    "nootropics": "woman focused creative work morning",
    "senolytics": "woman outdoor active healthy aging",
    "spermidine": "woman outdoor healthy lifestyle garden",
    "nad-iv": "woman wellness outdoor morning confident",
    "phase-1": "woman cooking fresh vegetables kitchen",
    "phase-2": "woman outdoor morning walk fresh",
    "histamine": "woman healthy low histamine meal",
}


def safe_fallback_for_slug(slug: str) -> str:
    slug_lower = slug.lower()
    for kw, query in SAFE_FALLBACKS.items():
        if kw in slug_lower:
            return query
    # Generic ultra-safe fallback
    topic_words = re.sub(
        r"-(after-40|women-over-40|women-after-40|after-40-women|over-40)$", "", slug
    )
    topic_words = re.sub(
        r"^(what-is-|what-are-|does-|how-to-|why-|signs-you-need-more-|best-)", "", topic_words
    )
    topic_words = topic_words.replace("-", " ")
    return f"woman {topic_words[:30].strip()} healthy lifestyle outdoor"


def sanitize_query(query: str, slug: str) -> str:
    if not is_unsafe(query):
        return query
    return safe_fallback_for_slug(slug)


def process_meta(meta_path: Path) -> bool:
    data = json.loads(meta_path.read_text())
    slug = data.get("slug", meta_path.stem)
    changed = False

    iq = data.get("image_query", "")
    if is_unsafe(iq):
        safe = safe_fallback_for_slug(slug)
        print(f"  FIX cover  [{slug[:45]}]: '{iq[:60]}' -> '{safe}'")
        data["image_query"] = safe
        changed = True

    bqs = data.get("body_image_queries", [])
    new_bqs = []
    for q in bqs:
        if is_unsafe(q):
            safe = safe_fallback_for_slug(slug)
            print(f"  FIX body   [{slug[:45]}]: '{q[:60]}' -> '{safe}'")
            new_bqs.append(safe)
            changed = True
        else:
            new_bqs.append(q)

    if changed:
        if new_bqs:
            data["body_image_queries"] = new_bqs
        meta_path.write_text(json.dumps(data, indent=2) + "\n")

    return changed


def main():
    fixed = 0
    clean = 0
    for meta_path in sorted(ARTICLES_DIR.glob("*.meta.json")):
        if process_meta(meta_path):
            fixed += 1
        else:
            clean += 1

    print(f"\nDone — {fixed} articles had unsafe queries (fixed), {clean} were already clean.")


if __name__ == "__main__":
    main()

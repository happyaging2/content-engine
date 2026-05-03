#!/usr/bin/env python3
"""Bulk-add image_query and body_image_queries to all meta.json files that lack them.

Strategy:
  - Articles with image_prompt: extract activity/setting words from DALL-E text
  - Articles with no image fields at all: derive from slug keywords
Skips files that already have image_query.
"""

import json
import re
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent.parent / "articles"

# Words to drop when building search queries
STOP = {
    "a", "an", "the", "in", "on", "at", "of", "with", "and", "her", "his",
    "their", "is", "are", "was", "were", "be", "been", "being", "to", "from",
    "by", "for", "as", "or", "but", "not", "so", "up", "out", "into",
    "8k", "resolution", "no", "watermark", "text", "cgi", "photograph",
    "photo", "shot", "editorial", "photography", "wearing", "dressed",
}

# Slug fragment → terse lifestyle query
SLUG_KEYWORD_QUERIES = {
    "5-htp": ("woman relaxing peaceful home reading", ["woman meditating indoor calm", "woman sleeping peacefully bedroom", "woman journaling morning"]),
    "acetyl-l-carnitine": ("woman focused home office laptop", ["woman cycling outdoor trail", "woman working desk alert", "healthy meal vegetables plate"]),
    "acetylcholine": ("woman reading book sunlit room", ["woman working laptop focused", "woman outdoor morning walk", "healthy brain food eggs greens"]),
    "adaptogens": ("woman practicing yoga outdoor garden", ["woman meditating calm indoor", "woman hiking trail nature", "herbal tea morning table"]),
    "adrenal-fatigue-vs": ("woman resting couch tired home", ["woman sleeping peacefully bedroom", "woman journal writing morning", "woman outdoor walk gentle"]),
    "adrenal-fatigue": ("woman relaxing peaceful home afternoon", ["woman yoga mat morning", "woman sleeping soundly bedroom", "woman gentle walk nature"]),
    "adrenal-recovery": ("woman meditating peaceful garden", ["woman sleeping deeply bedroom", "woman gentle yoga indoor", "woman reading calm sunlit"]),
    "afternoon-energy": ("woman tired desk afternoon office", ["woman drinking tea afternoon", "woman stretching break office", "woman energized outdoor walk"]),
    "anti-inflammatory": ("woman cooking colorful vegetables kitchen", ["healthy anti-inflammatory meal bowl", "woman eating salad fresh food", "woman outdoor morning jog"]),
    "ashwagandha": ("woman calm outdoor nature sitting", ["woman yoga outdoor morning", "healthy herbal tea relaxing", "woman walking forest trail"]),
    "b12": ("woman energized morning kitchen routine", ["woman outdoor walk morning", "healthy food eggs meat greens", "woman focused working desk"]),
    "berberine-blood-sugar": ("woman healthy meal kitchen table", ["woman outdoor morning walk", "healthy balanced meal vegetables", "woman checking health morning"]),
    "berberine-gut": ("woman eating fermented food kitchen", ["yogurt berries breakfast bowl", "woman garden morning walk", "woman preparing healthy meal"]),
    "berberine-vs": ("woman healthy breakfast table morning", ["woman outdoor morning walk", "balanced meal vegetables grains", "woman relaxing home wellness"]),
    "best-heart": ("woman confident healthy outdoor morning", ["woman cycling park trail", "healthy heart food colorful", "woman yoga outdoor morning"]),
    "best-supplements-menopause": ("woman energized morning outdoor", ["woman yoga mat garden", "breakfast eggs avocado plate", "woman standing desk office"]),
    "best-supplements": ("woman vibrant outdoor morning lifestyle", ["woman healthy meal colorful", "woman exercising outdoor", "woman calm relaxed home"]),
    "biotin": ("woman healthy glowing portrait outdoor", ["woman eating nuts seeds food", "woman outdoor morning light", "healthy food eggs avocado"]),
    "black-cohosh": ("woman relaxing garden afternoon calm", ["woman meditation outdoor calm", "woman reading home peaceful", "woman gentle walk park"]),
    "bone": ("woman hiking outdoor sunlight nature", ["woman yoga morning light", "healthy calcium food greens dairy", "woman walking beach outdoor"]),
    "brain-fog": ("woman focused working home office", ["woman reading book calm light", "healthy brain food greens eggs", "woman outdoor morning walk energized"]),
    "cardiovascular": ("woman jogging park morning fitness", ["woman cycling outdoor trail", "heart healthy colorful meal", "woman outdoor stretching morning"]),
    "chromium": ("woman healthy balanced meal kitchen", ["woman outdoor walk morning", "healthy whole food vegetables", "woman cooking kitchen healthy"]),
    "circadian": ("woman sleeping peacefully bedroom morning", ["woman morning sunlight routine", "woman outdoor walk sunrise", "woman relaxing evening calm home"]),
    "coenzyme": ("woman energized morning workout outdoor", ["woman running park trail", "healthy breakfast eggs avocado", "woman focused desk productive"]),
    "collagen": ("woman glowing skin portrait natural light", ["woman eating healthy food collagen", "woman outdoor morning skincare", "woman confident smile portrait"]),
    "copper": ("woman outdoor lifestyle wellness portrait", ["nuts seeds healthy food bowl", "woman cooking dark leafy greens", "woman confident portrait light"]),
    "cortisol": ("woman calm peaceful garden outdoor", ["woman meditating indoor morning", "woman outdoor walk nature", "woman sleeping peaceful bedroom"]),
    "creatine": ("woman exercising gym outdoor active", ["woman lifting light weights gym", "woman outdoor running trail", "healthy protein meal food"]),
    "curcumin": ("woman outdoor morning lifestyle wellness", ["turmeric golden latte kitchen", "woman cooking healthy anti-inflammatory", "woman walking nature trail"]),
    "detox": ("woman drinking water healthy morning", ["woman outdoor walk fresh air", "healthy green food vegetables", "woman yoga morning stretch"]),
    "dhea": ("woman vibrant outdoor active lifestyle", ["woman exercising morning outdoor", "woman confident healthy portrait", "healthy balanced meal table"]),
    "digestive": ("woman eating healthy balanced meal", ["woman drinking tea digestion", "healthy probiotic yogurt food", "woman outdoor walk after meal"]),
    "energy": ("woman energized outdoor morning active", ["woman running park morning", "healthy breakfast colorful food", "woman working focused alert"]),
    "estrogen": ("woman outdoor morning walk confident", ["healthy hormone-supporting food meal", "woman exercising outdoor fitness", "woman calm home balanced"]),
    "evening-primrose": ("woman relaxing peaceful home evening", ["woman meditating indoor calm", "woman outdoor gentle walk", "healthy omega food fish"]),
    "fasting": ("woman healthy morning routine kitchen", ["woman outdoor walk morning calm", "healthy balanced meal colorful", "woman journaling morning routine"]),
    "ferritin": ("woman energized outdoor morning", ["healthy iron-rich food spinach meal", "woman outdoor walk energized", "woman cooking healthy greens"]),
    "fiber": ("woman eating healthy fiber food", ["whole grain vegetables colorful meal", "woman outdoor morning walk", "healthy gut food probiotic"]),
    "fisetin": ("woman vibrant outdoor lifestyle active", ["healthy colorful berries fruit food", "woman outdoor morning walk", "woman yoga garden calm"]),
    "folate": ("woman healthy balanced diet kitchen", ["healthy green leafy food meal", "woman cooking vegetables kitchen", "woman outdoor morning sunlight"]),
    "gaba": ("woman sleeping peacefully bedroom night", ["woman calm meditating indoor", "woman relaxing evening cozy home", "healthy sleep routine evening"]),
    "gut-brain": ("woman meditating calm focused indoor", ["healthy probiotic fermented food", "woman outdoor morning walk gut", "woman journaling calm morning"]),
    "gut": ("woman eating healthy meal kitchen", ["healthy gut fermented food probiotic", "woman outdoor walk morning", "colorful healthy vegetables meal"]),
    "hashimoto": ("woman healthy thyroid wellness lifestyle", ["woman outdoor gentle walk morning", "healthy thyroid food selenium", "woman journaling health routine"]),
    "heart": ("woman outdoor morning active fitness", ["woman jogging park trail fitness", "heart healthy colorful vegetables meal", "woman yoga outdoor balance"]),
    "hormone": ("woman outdoor morning confident wellness", ["healthy hormone food balanced meal", "woman yoga calm indoor", "woman walking nature peaceful"]),
    "how-to-detox": ("woman drinking water lemon morning", ["healthy green detox food vegetables", "woman outdoor walk morning fresh", "woman cooking healthy kitchen"]),
    "how-to-improve-focus": ("woman focused home office working", ["woman reading book sunlit room", "healthy brain food walnuts berries", "woman meditation morning quiet"]),
    "how-to-support-mitochondrial": ("woman energized outdoor morning exercise", ["woman cycling park morning", "healthy colorful food bowl", "woman yoga outdoor peaceful"]),
    "inflammation": ("woman outdoor morning walk peaceful", ["healthy anti-inflammatory food colorful", "woman yoga calm indoor morning", "woman cooking healthy kitchen"]),
    "insulin": ("woman healthy balanced meal kitchen", ["woman outdoor morning walk", "healthy low glycemic food meal", "woman cooking vegetables kitchen"]),
    "iodine": ("woman healthy thyroid lifestyle outdoor", ["healthy thyroid food seaweed meal", "woman outdoor morning sunlight", "woman confident healthy portrait"]),
    "iron": ("woman energized outdoor active morning", ["healthy iron food spinach meat meal", "woman outdoor exercise morning", "woman cooking healthy kitchen"]),
    "joints": ("woman walking outdoor gentle morning", ["woman swimming pool exercise", "healthy omega food fish meal", "woman outdoor gentle stretch yoga"]),
    "l-theanine": ("woman calm focused indoor morning", ["woman meditating indoor peaceful", "healthy herbal tea morning", "woman reading calm home"]),
    "leaky-gut": ("woman cooking healthy food kitchen", ["healthy gut probiotic food meal", "woman outdoor walk morning", "woman drinking herbal tea"]),
    "lions-mane": ("woman focused creative writing home office", ["healthy brain food mushrooms greens", "woman outdoor morning walk", "woman reading book calm light"]),
    "liver": ("woman outdoor morning healthy lifestyle", ["healthy liver food greens lemon", "woman drinking water morning", "woman outdoor walk fresh air"]),
    "lutein": ("woman healthy eyes outdoor sunlight", ["healthy colorful food berries greens", "woman outdoor morning light", "woman reading book bright light"]),
    "maca": ("woman energized outdoor morning active", ["healthy balanced meal colorful food", "woman outdoor walk confident", "woman exercising morning fitness"]),
    "magnesium": ("woman peaceful sleep bedroom morning", ["woman relaxing evening home cozy", "healthy magnesium food greens nuts", "woman morning routine kitchen calm"]),
    "melatonin": ("woman sleeping peacefully bedroom evening", ["woman calm evening routine home", "woman reading bed evening", "woman outdoor sunset walk"]),
    "memory": ("woman reading focused home library", ["woman outdoor walk morning focused", "healthy brain food omega greens", "woman writing journal morning"]),
    "menopause": ("woman outdoor morning confident active", ["woman yoga calm indoor morning", "healthy hormone food balanced meal", "woman walking nature trail"]),
    "metabolism": ("woman outdoor morning exercise active", ["healthy metabolism food colorful meal", "woman exercising gym morning", "woman cooking healthy kitchen"]),
    "methylation": ("woman healthy morning routine kitchen", ["healthy B vitamin food greens", "woman outdoor morning sunlight", "woman journaling health routine"]),
    "mitochondrial": ("woman energized outdoor morning exercise", ["healthy mitochondria food meal greens", "woman cycling morning trail", "woman yoga outdoor peaceful"]),
    "mood": ("woman smiling peaceful outdoor garden", ["woman relaxing reading indoor calm", "healthy serotonin food colorful", "woman outdoor morning walk"]),
    "mushroom": ("woman outdoor nature forest walk", ["healthy mushroom food meal", "woman outdoor morning walk nature", "woman calm meditating indoor"]),
    "nad": ("woman vibrant outdoor morning energy", ["woman exercising outdoor morning", "healthy colorful food bowl", "woman confident active lifestyle"]),
    "nmn": ("woman energized outdoor morning active", ["woman cycling park morning", "healthy colorful food bowl", "woman relaxing garden afternoon"]),
    "omega": ("woman outdoor active fitness morning", ["healthy fish omega food meal", "woman exercising outdoor", "woman stretching outdoor morning"]),
    "osteoporosis": ("woman hiking outdoor sunshine nature", ["woman gentle exercise outdoor", "healthy calcium food dairy greens", "woman walking beach morning"]),
    "perimenopause": ("woman outdoor morning confident calm", ["woman yoga indoor calm morning", "healthy balanced meal hormone", "woman walking nature trail peaceful"]),
    "phosphatidylserine": ("woman writing journal morning light", ["woman reading studying natural light", "healthy brain foods eggs greens", "woman outdoor walking focused"]),
    "pqq": ("woman home office focused productive", ["woman eating berries healthy breakfast", "woman jogging residential morning", "woman creative work desk plants"]),
    "probiotics": ("woman eating fermented healthy food", ["healthy probiotic yogurt food", "woman outdoor walk morning", "healthy gut food fermented"]),
    "progesterone": ("woman relaxing peaceful home evening", ["woman calm outdoor morning walk", "woman meditating indoor peaceful", "woman healthy balanced meal"]),
    "protein": ("woman healthy meal kitchen eating", ["healthy protein food eggs fish", "woman exercising outdoor morning", "woman cooking healthy kitchen"]),
    "resveratrol": ("woman outdoor active healthy lifestyle", ["healthy colorful berries food", "woman outdoor morning walk", "woman vibrant confident portrait"]),
    "rhodiola": ("woman hiking mountain trail nature", ["woman meditating outdoor calm", "healthy adaptogen herbal tea", "woman outdoor walk focused"]),
    "selenium": ("woman healthy thyroid wellness lifestyle", ["healthy selenium food nuts fish", "woman outdoor morning walk", "woman cooking healthy kitchen"]),
    "serotonin": ("woman happy smiling outdoor morning", ["woman relaxing peaceful indoor calm", "healthy serotonin food colorful", "woman outdoor walk joyful"]),
    "sirtuins": ("woman vibrant outdoor active healthy", ["healthy antioxidant food colorful berries", "woman outdoor morning exercise", "woman confident portrait natural"]),
    "skin": ("woman glowing skin portrait natural light", ["woman applying skincare bathroom mirror", "healthy skin food colorful", "woman outdoor portrait confident"]),
    "sleep": ("woman sleeping peacefully bedroom morning", ["woman calm evening routine home", "woman reading bed evening light", "woman outdoor sunset walk"]),
    "stress-eating": ("woman relaxing garden mindful afternoon", ["woman meditation outdoor morning", "healthy snacks fruit colorful plate", "woman journaling quiet home"]),
    "stress": ("woman calm outdoor garden afternoon", ["woman meditating indoor peaceful", "healthy stress relief food", "woman outdoor walk nature calm"]),
    "sugar": ("woman healthy meal balanced kitchen", ["healthy low sugar food colorful", "woman outdoor morning walk", "woman cooking vegetables kitchen"]),
    "telomere": ("woman running outdoor healthy lifestyle", ["woman yoga peaceful garden", "healthy breakfast morning meal", "woman walking nature path"]),
    "testosterone": ("woman active outdoor morning fitness", ["woman exercising outdoor morning", "healthy balanced meal food", "woman confident active portrait"]),
    "thyroid": ("woman healthy morning routine outdoor", ["healthy thyroid food meal", "woman outdoor gentle walk morning", "woman journaling health routine"]),
    "turmeric": ("woman outdoor morning lifestyle wellness", ["turmeric golden latte kitchen table", "woman cooking healthy anti-inflammatory", "woman walking nature trail"]),
    "ubiquinol": ("woman energized outdoor morning", ["woman cycling trail outdoor", "healthy colorful food vegetables", "woman focused desk morning"]),
    "vitamin-b": ("woman energized morning kitchen", ["healthy B vitamin food greens", "woman outdoor walk morning", "woman cooking healthy kitchen"]),
    "vitamin-c": ("woman glowing outdoor morning", ["healthy vitamin C food citrus", "woman outdoor sunlight morning", "woman cooking colorful food"]),
    "vitamin-d": ("woman hiking outdoors sunlight", ["woman yoga morning light", "healthy salad greens meal", "woman walking beach sunset"]),
    "vitamin-e": ("woman outdoor healthy lifestyle active", ["healthy vitamin E food nuts", "woman outdoor morning walk", "woman cooking healthy kitchen"]),
    "vitamin-k": ("woman active outdoor healthy morning", ["healthy dark greens food meal", "woman outdoor gentle walk", "woman cooking greens kitchen"]),
    "weight": ("woman outdoor morning walk confident", ["woman exercising outdoor morning", "healthy balanced meal colorful", "woman yoga indoor calm"]),
    "zinc": ("woman healthy immunity outdoor morning", ["healthy zinc food pumpkin seeds", "woman outdoor morning walk", "woman cooking healthy kitchen"]),
}


def extract_from_prompt(prompt: str, max_words: int = 5) -> str:
    """Extract a short lifestyle query from a DALL-E style prompt."""
    # Match woman activity description
    patterns = [
        r"woman\s+(.+?)(?:\s*,|\s+wearing|\s+shot on|\s+editorial|\s+in a bright|\s+8K)",
        r"40s?\s+(.+?)(?:\s*,|\s+wearing|\s+in a|\s+shot on|\s+8K)",
    ]
    for pat in patterns:
        m = re.search(pat, prompt, re.I)
        if m:
            text = m.group(1).strip()
            words = [w.strip(".,;()") for w in text.split()]
            # Filter stop words, numbers, "40s", single chars
            clean = [
                w for w in words
                if w.lower() not in STOP
                and len(w) > 2
                and not re.match(r"^\d", w)  # no "40s", "45-year-old" etc.
            ][:max_words]
            if len(clean) >= 2:
                return "woman " + " ".join(clean)
    return ""


def slug_to_query(slug: str) -> tuple[str, list[str]]:
    """Derive image_query + body_image_queries from slug keyword matching."""
    for kw, (cover, body) in SLUG_KEYWORD_QUERIES.items():
        if kw in slug:
            return cover, list(body)

    # Generic fallback: slug → readable phrase
    topic = re.sub(r"-(after-40|women-over-40|women-after-40|after-40-women|over-40)$", "", slug)
    topic = re.sub(r"^(what-is-|what-are-|does-|how-to-|why-|signs-you-need-more-|best-)", "", topic)
    topic = topic.replace("-", " ")
    words = [w for w in topic.split() if w.lower() not in STOP][:4]
    cover = "woman " + " ".join(words) + " healthy lifestyle"
    body = [
        "woman outdoor morning walk",
        "healthy colorful food meal",
        "woman relaxed confident indoor",
    ]
    return cover, body


def process_meta(meta_path: Path) -> bool:
    data = json.loads(meta_path.read_text())

    if "image_query" in data:
        return False  # already has it

    image_prompt = data.get("image_prompt", "")
    body_prompts = data.get("body_image_prompts", [])

    # Derive cover query
    if image_prompt:
        cover_q = extract_from_prompt(image_prompt)
        if not cover_q:
            cover_q, _ = slug_to_query(data.get("slug", meta_path.stem))
    else:
        cover_q, _ = slug_to_query(data.get("slug", meta_path.stem))

    # Derive body queries
    body_qs = []
    for bp in body_prompts[:3]:
        q = extract_from_prompt(bp, max_words=4)
        if q:
            body_qs.append(q)

    # If we couldn't extract body queries, use slug-based fallbacks
    if len(body_qs) < 3:
        _, fallback_body = slug_to_query(data.get("slug", meta_path.stem))
        while len(body_qs) < 3 and fallback_body:
            body_qs.append(fallback_body.pop(0))

    data["image_query"] = cover_q
    data["body_image_queries"] = body_qs[:3]

    meta_path.write_text(json.dumps(data, indent=2) + "\n")
    return True


def main():
    updated = 0
    skipped = 0

    for meta_path in sorted(ARTICLES_DIR.glob("*.meta.json")):
        if process_meta(meta_path):
            print(f"UPDATED {meta_path.name}")
            updated += 1
        else:
            skipped += 1

    print(f"\nDone — updated: {updated}, skipped (already had queries): {skipped}")


if __name__ == "__main__":
    main()

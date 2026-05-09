"""
GEO schema builder for Happy Aging articles.

Emits a MedicalWebPage / Article JSON-LD block per article, including:
  - reviewedBy (Person, with sameAs LinkedIn)
  - author (Organization)
  - citation array generated from meta.json `citations` (PMID/DOI verified)
  - about / mentions entity arrays
  - dateModified / datePublished
  - speakable selectors

Optionally emits a HowTo schema when the article has a numbered <ol> protocol
(Rule G16).

Used by:
  - articles/patch-seo.py            (publish-time injection)
  - articles/patch-medical-schema.py (retroactive on 548 published articles)
  - scripts/qa-and-publish.sh        (daily run)
"""

from __future__ import annotations

import json
import re
from typing import Any

SITE_URL = "https://happyaging.com"
BLOG_URL = "https://happyaging.com/blogs/news"
LOGO_URL = "https://happyaging.com/cdn/shop/files/logo.png"
ORG_NAME = "Happy Aging"
WIKIDATA_QID = "Q139720291"
WIKIDATA_URL = f"https://www.wikidata.org/wiki/{WIKIDATA_QID}"
# Google Business Profile (Customer ID) — feeds the Knowledge Panel.
GBP_CID = "10120263721952855343"
GBP_URL = f"https://maps.google.com/?cid={GBP_CID}"
# Hero product — full data lives in config/hero-product.json. Every
# NAD/NMN/longevity article CTA defaults here, and a Product/DietarySupplement
# JSON-LD block is emitted whenever the article matches the hero's keywords.
HERO_PRODUCT_NAME = "NAD+ Women's Longevity Formula"
HERO_PRODUCT_SHORT = "NAD Advanced"
HERO_PRODUCT_URL = "https://happyaging.com/pages/nad-advanced"
HERO_KEYWORDS = [
    "nad", "nad+", "nmn", "nmnh", "longevity", "anti-aging", "anti aging",
    "sirtuins", "resveratrol", "urolithin", "mitochondrial", "12 hallmarks",
    "cellular aging", "healthy aging", "senescence",
]


def _hero_product_schema() -> dict:
    """DietarySupplement / Product JSON-LD with the 6-blend structure surfaced
    as additionalProperty so LLMs can extract the formulation."""
    return {
        "@type": "DietarySupplement",
        "name": HERO_PRODUCT_NAME,
        "alternateName": HERO_PRODUCT_SHORT,
        "url": HERO_PRODUCT_URL,
        "brand": {"@type": "Brand", "name": ORG_NAME},
        "manufacturer": {
            "@type": "Organization",
            "name": ORG_NAME,
            "url": SITE_URL,
        },
        "description": (
            "The first women-specific longevity formula targeting all 12 "
            "hallmarks of aging. 30 premium ingredients across 6 synergistic "
            "blends: NAD+ SuperBooster, Cellular Activators, Skin Glow, "
            "Hormone Harmony, Brain Booster, and SuperAntioxidant Organic."
        ),
        "targetPopulation": "Women 35-65 seeking science-backed longevity support",
        "recommendedIntake": "2 capsules daily, in the morning with water",
        "isProprietary": True,
        "nonProprietaryName": "NAD+ precursor + multi-pathway longevity blend",
        "activeIngredient": (
            "Liposomal NAD+; Nicotinamide Riboside (NR); NMNH (Reduced NMN); "
            "Trans-Resveratrol; Urolithin A; PQQ; CoQ10; Glutathione; "
            "Hyaluronic Acid; Vitamin C; Maca Root; Vitex; L-Theanine; "
            "Lion's Mane; Ginkgo Biloba"
        ),
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Capsule count", "value": "90"},
            {"@type": "PropertyValue", "name": "Servings per container", "value": "30"},
            {"@type": "PropertyValue", "name": "Diet", "value": "Vegan, Non-GMO, Gluten-Free"},
            {"@type": "PropertyValue", "name": "Aging hallmarks targeted", "value": "12"},
            {"@type": "PropertyValue", "name": "Active compounds", "value": "30"},
            {"@type": "PropertyValue", "name": "Third-party tested", "value": "Citrus Labs"},
        ],
    }


def _article_mentions_hero(html: str, meta: dict) -> bool:
    haystack = " ".join(
        [
            html.lower(),
            (meta.get("title") or "").lower(),
            " ".join(meta.get("about") or []).lower(),
            " ".join(meta.get("mentions") or []).lower(),
        ]
    )
    return any(k in haystack for k in HERO_KEYWORDS)
ORG_DESCRIPTION = (
    "Happy Aging is a US-based longevity wellness brand for women over 40, "
    "built around physician-reviewed supplement protocols."
)
AUTHOR_PAGE = f"{SITE_URL}/pages/dr-daniel-yadegar"
REVIEWER_LINKEDIN = (
    "https://www.linkedin.com/in/daniel-yadegar-md-facc-rpvi-aa55a958/"
)

# Default reviewer used when meta.json doesn't override.
DEFAULT_REVIEWER = {
    "name": "Dr. Daniel Yadegar, MD, FACC, RPVI",
    "title": "Cardiologist & Longevity Physician",
    "url": AUTHOR_PAGE,
    "sameAs": [
        REVIEWER_LINKEDIN,
        "https://www.atria.org/doctors/dr-daniel-yadegar/",
        "https://lumos-pharma.com/company/daniel-yadegar-m-d/",
        "https://www.instagram.com/drdanyadegar/",
    ],
}


def _person_reviewer(meta: dict) -> dict:
    name = meta.get("reviewer") or DEFAULT_REVIEWER["name"]
    title = meta.get("reviewer_title") or DEFAULT_REVIEWER["title"]
    url = meta.get("reviewer_url") or DEFAULT_REVIEWER["url"]
    same_as = meta.get("reviewer_sameAs") or DEFAULT_REVIEWER["sameAs"]
    return {
        "@type": "Person",
        "name": name,
        "jobTitle": title,
        "url": url,
        "sameAs": same_as,
    }


def _organization_publisher() -> dict:
    org = {
        "@type": "Organization",
        "name": ORG_NAME,
        "url": SITE_URL,
        "description": ORG_DESCRIPTION,
        "logo": {"@type": "ImageObject", "url": LOGO_URL},
        "identifier": [
            {
                "@type": "PropertyValue",
                "propertyID": "Wikidata",
                "value": WIKIDATA_QID,
                "url": WIKIDATA_URL,
            },
            {
                "@type": "PropertyValue",
                "propertyID": "Google Business Profile CID",
                "value": GBP_CID,
                "url": GBP_URL,
            },
        ],
        "sameAs": [
            WIKIDATA_URL,
            GBP_URL,
            "https://www.instagram.com/happyaging/",
            "https://www.facebook.com/happyaging/",
        ],
    }
    # Third-party clinical testing references — independent validation that
    # strengthens E-E-A-T and helps LLMs treat the brand as authoritative.
    reviews = _brand_third_party_reviews()
    if reviews:
        org["subjectOf"] = reviews
    return org


# ── Third-party clinical testing registry ────────────────────────────────────
# Independent labs that have clinically tested Happy Aging products. Each entry
# becomes a Review JSON-LD object so LLMs and Google can cross-reference the
# brand against external validators (Citrus Labs, future NSF/USP/ConsumerLab).
THIRD_PARTY_VALIDATIONS: list[dict] = [
    {
        "product": "Happy Aging Longevity Shot",
        "match": ["longevity shot", "nmn shot", "nad shot"],
        "lab": "Citrus Labs",
        "lab_url": "https://www.citruslabs.com",
        "url": "https://www.citruslabs.com/testedproducts/happy-aging-longevity-shot",
        "review_type": "Clinical efficacy testing",
    },
    {
        "product": "Happy Aging Calm Shot",
        "match": ["calm shot", "stress shot", "ashwagandha shot"],
        "lab": "Citrus Labs",
        "lab_url": "https://www.citruslabs.com",
        "url": "https://www.citruslabs.com/testedproducts/happy-aging-calm-shot",
        "review_type": "Clinical efficacy testing",
    },
    {
        "product": "Happy Aging Glow Shot",
        "match": ["glow shot", "skin shot", "collagen shot", "beauty shot"],
        "lab": "Citrus Labs",
        "lab_url": "https://www.citruslabs.com",
        "url": "https://www.citruslabs.com/testedproducts/happy-aging-glow-shot",
        "review_type": "Clinical efficacy testing",
    },
]


def _brand_third_party_reviews() -> list[dict]:
    """All third-party validations attached at the Organization level."""
    return [
        {
            "@type": "Review",
            "url": v["url"],
            "name": f"{v['lab']} clinical testing — {v['product']}",
            "author": {
                "@type": "Organization",
                "name": v["lab"],
                "url": v["lab_url"],
            },
            "itemReviewed": {
                "@type": "Product",
                "name": v["product"],
                "brand": {"@type": "Brand", "name": ORG_NAME},
            },
            "reviewAspect": v["review_type"],
        }
        for v in THIRD_PARTY_VALIDATIONS
    ]


def _article_third_party_reviews(html: str, meta: dict) -> list[dict]:
    """Validations relevant to the specific article (matched on body + meta)."""
    haystack = " ".join(
        [
            html.lower(),
            (meta.get("title") or "").lower(),
            " ".join(meta.get("about") or []).lower(),
            " ".join(meta.get("mentions") or []).lower(),
        ]
    )
    matched = []
    for v in THIRD_PARTY_VALIDATIONS:
        if any(needle in haystack for needle in v["match"]):
            matched.append(
                {
                    "@type": "Review",
                    "url": v["url"],
                    "name": f"{v['lab']} clinical testing — {v['product']}",
                    "author": {
                        "@type": "Organization",
                        "name": v["lab"],
                        "url": v["lab_url"],
                    },
                    "itemReviewed": {
                        "@type": "Product",
                        "name": v["product"],
                        "brand": {"@type": "Brand", "name": ORG_NAME},
                    },
                    "reviewAspect": v["review_type"],
                }
            )
    return matched


def _author_team() -> dict:
    return {
        "@type": "Organization",
        "name": "Happy Aging Team",
        "url": SITE_URL,
        "description": (
            "Longevity researchers and women's health writers focused on "
            "evidence-based wellness after 40."
        ),
    }


def _citation_objects(meta: dict) -> list[dict]:
    items = meta.get("citations") or []
    out: list[dict] = []
    for c in items:
        if not isinstance(c, dict):
            continue
        pmid = c.get("pmid")
        doi = c.get("doi")
        identifier = None
        url = None
        if pmid:
            identifier = f"PMID:{pmid}"
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        elif doi:
            identifier = f"DOI:{doi}"
            url = f"https://doi.org/{doi}"
        if not identifier:
            continue
        obj: dict[str, Any] = {
            "@type": "ScholarlyArticle",
            "identifier": identifier,
            "name": c.get("title", ""),
            "url": url,
        }
        if c.get("journal"):
            obj["publisher"] = {"@type": "Organization", "name": c["journal"]}
        if c.get("year"):
            obj["datePublished"] = str(c["year"])
        if c.get("study_type"):
            obj["additionalType"] = c["study_type"]
        if c.get("n"):
            obj["description"] = f"Sample size: {c['n']}"
        out.append(obj)
    return out


def _detect_schema_type(meta: dict, html: str) -> str:
    explicit = meta.get("schema_type")
    if explicit in {"MedicalWebPage", "Article", "BlogPosting"}:
        return explicit
    medical_signals = (
        meta.get("medical_audience")
        or meta.get("primary_topic", "").lower().startswith(("medical", "treatment"))
        or re.search(
            r"\b(symptom|diagnos|treatment|condition|disorder|disease|"
            r"deficiency|menopause|perimenopause|hormone|insulin|cortisol)\b",
            html,
            re.IGNORECASE,
        )
    )
    return "MedicalWebPage" if medical_signals else "Article"


def build_medical_schema(
    *,
    title: str,
    slug: str,
    meta_desc: str,
    meta: dict,
    html: str,
) -> dict:
    """Return JSON-LD-ready dict for the article page."""
    schema_type = _detect_schema_type(meta, html)
    url = f"{BLOG_URL}/{slug}"
    schema: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": title,
        "name": title,
        "description": meta_desc,
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": "en-US",
        "isAccessibleForFree": True,
        "author": _author_team(),
        "reviewedBy": _person_reviewer(meta),
        "publisher": _organization_publisher(),
        "datePublished": meta.get("date_published") or meta.get("date_reviewed"),
        "dateModified": meta.get("date_modified")
        or meta.get("date_reviewed")
        or meta.get("date_published"),
        "speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": ["article p:first-of-type", ".what-to-know", ".faq h3"],
        },
    }
    if schema_type == "MedicalWebPage":
        schema["medicalAudience"] = {
            "@type": "MedicalAudience",
            "audienceType": meta.get("medical_audience", "Patient"),
        }
        schema["lastReviewed"] = meta.get("date_reviewed") or schema["dateModified"]
    if meta.get("about"):
        schema["about"] = [
            {"@type": "Thing", "name": x} for x in meta["about"] if x
        ]
    if meta.get("mentions"):
        schema["mentions"] = [
            {"@type": "Thing", "name": x} for x in meta["mentions"] if x
        ]
    citations = _citation_objects(meta)
    if citations:
        schema["citation"] = citations
    article_reviews = _article_third_party_reviews(html, meta)
    if article_reviews:
        schema["subjectOf"] = article_reviews
    # Surface the hero product whenever the article touches NAD/NMN/longevity
    # entities. This puts a structured DietarySupplement next to the article
    # body for LLM/Google extraction.
    if _article_mentions_hero(html, meta):
        schema["mentions"] = (schema.get("mentions") or []) + [_hero_product_schema()]
    return schema


def build_comparison_itemlist(*, title: str, meta: dict) -> dict | None:
    """When meta['format'] == 'comparison', emit an ItemList of Product objects.
    Google Shopping + AI Overviews shopping ingest ItemList for side-by-side
    product cards. Pulled from meta['products_compared']."""
    if (meta.get("format") or "").lower() != "comparison":
        return None
    products = meta.get("products_compared") or []
    if len(products) < 2:
        return None
    items = []
    for i, p in enumerate(products, start=1):
        if not isinstance(p, dict) or not p.get("name"):
            continue
        prod_obj: dict = {
            "@type": "Product",
            "name": p["name"],
        }
        if p.get("url"):
            prod_obj["url"] = p["url"]
        if p.get("brand"):
            prod_obj["brand"] = {"@type": "Brand", "name": p["brand"]}
        elif "happyaging" in (p.get("url") or "").lower():
            prod_obj["brand"] = {"@type": "Brand", "name": ORG_NAME}
        if p.get("active"):
            prod_obj["additionalProperty"] = [
                {"@type": "PropertyValue", "name": "Active ingredient", "value": p["active"]}
            ]
        if p.get("dose"):
            prod_obj.setdefault("additionalProperty", []).append(
                {"@type": "PropertyValue", "name": "Dose", "value": p["dose"]}
            )
        if p.get("form"):
            prod_obj.setdefault("additionalProperty", []).append(
                {"@type": "PropertyValue", "name": "Form", "value": p["form"]}
            )
        if p.get("third_party_tested"):
            prod_obj.setdefault("additionalProperty", []).append(
                {"@type": "PropertyValue", "name": "Third-party tested", "value": p["third_party_tested"]}
            )
        items.append({"@type": "ListItem", "position": i, "item": prod_obj})
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": title,
        "itemListOrder": "https://schema.org/ItemListUnordered",
        "numberOfItems": len(items),
        "itemListElement": items,
    }


def build_howto_schema(*, title: str, html: str) -> dict | None:
    """If the article contains a numbered <ol> protocol with 3+ items, emit HowTo."""
    # Find the first <ol> with multiple <li>
    ol_match = re.search(r"<ol[^>]*>(.*?)</ol>", html, re.IGNORECASE | re.DOTALL)
    if not ol_match:
        return None
    items = re.findall(r"<li[^>]*>(.*?)</li>", ol_match.group(1), re.IGNORECASE | re.DOTALL)
    items = [re.sub(r"<[^>]+>", "", i).strip() for i in items]
    items = [i for i in items if len(i) > 8]
    if len(items) < 3:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": title,
        "step": [
            {"@type": "HowToStep", "position": idx + 1, "text": text}
            for idx, text in enumerate(items[:10])
        ],
    }


def render_jsonld_block(obj: dict) -> str:
    return (
        '\n<script type="application/ld+json">\n'
        + json.dumps(obj, ensure_ascii=False, indent=2)
        + "\n</script>\n"
    )


def inject_medical_schema(
    html: str,
    *,
    title: str,
    slug: str,
    meta_desc: str,
    meta: dict,
) -> str:
    """Replace any prior MedicalWebPage/Article schema and re-inject."""
    # Strip stale MedicalWebPage / Article blocks (re-runs).
    html = re.sub(
        r'\s*<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"(?:MedicalWebPage|Article)".*?</script>\s*',
        "\n",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'\s*<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"HowTo".*?</script>\s*',
        "\n",
        html,
        flags=re.DOTALL,
    )
    # Strip stale ItemList (re-runs)
    html = re.sub(
        r'\s*<script type="application/ld\+json">\s*\{[^}]*"@type":\s*"ItemList".*?</script>\s*',
        "\n",
        html,
        flags=re.DOTALL,
    )
    schema = build_medical_schema(
        title=title, slug=slug, meta_desc=meta_desc, meta=meta, html=html
    )
    block = render_jsonld_block(schema)
    howto = build_howto_schema(title=title, html=html)
    if howto:
        block += render_jsonld_block(howto)
    comparison = build_comparison_itemlist(title=title, meta=meta)
    if comparison:
        block += render_jsonld_block(comparison)
    if "</body>" in html:
        return html.replace("</body>", block + "</body>", 1)
    return html + block


__all__ = [
    "build_medical_schema",
    "build_howto_schema",
    "build_comparison_itemlist",
    "inject_medical_schema",
    "render_jsonld_block",
    "DEFAULT_REVIEWER",
    "REVIEWER_LINKEDIN",
    "AUTHOR_PAGE",
    "ORG_DESCRIPTION",
]

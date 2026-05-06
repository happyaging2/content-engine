#!/usr/bin/env python3
"""
patch-blog-schema.py — Inject Blog + ItemList + BreadcrumbList schema into
the Shopify blog listing page (happyaging.com/blogs/news) via Theme Assets API.

Usage:
    SHOPIFY_TOKEN=shpat_... python3 articles/patch-blog-schema.py
"""

import json, os, sys, re, urllib.request, urllib.parse, urllib.error

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID       = "109440303424"
BLOG_HANDLE   = "news"
BLOG_URL      = "https://happyaging.com/blogs/news"
SITE_URL      = "https://happyaging.com"
LOGO_URL      = "https://happyaging.com/cdn/shop/files/happy-aging-logo.png"

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
if not SHOPIFY_TOKEN:
    raise SystemExit("ERROR: set SHOPIFY_TOKEN")

API = f"https://{SHOPIFY_STORE}/admin/api/2024-01"
HEADERS = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}


def api_get(path):
    req = urllib.request.Request(f"{API}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def api_put(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{API}{path}", data=data, method="PUT", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def get_active_theme_id():
    themes = api_get("/themes.json")["themes"]
    for t in themes:
        if t.get("role") == "main":
            return t["id"]
    return themes[0]["id"]


def get_asset(theme_id, key):
    path = f"/themes/{theme_id}/assets.json?" + urllib.parse.urlencode({"asset[key]": key})
    try:
        return api_get(path)["asset"]
    except Exception:
        return None


def put_asset(theme_id, key, value):
    payload = {"asset": {"key": key, "value": value}}
    return api_put(f"/themes/{theme_id}/assets.json", payload)


def fetch_articles():
    """Fetch recent articles for ItemList schema (up to 250)."""
    path = f"/blogs/{BLOG_ID}/articles.json?limit=250&fields=id,title,handle,published_at"
    data = api_get(path)
    return data.get("articles", [])


def build_schemas(articles):
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BLOG_URL},
        ],
    }

    blog_schema = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Happy Aging Blog",
        "description": (
            "Science-backed articles on healthy aging, longevity, and wellness "
            "for women over 40 — covering nutrition, hormones, supplements, and lifestyle."
        ),
        "url": BLOG_URL,
        "publisher": {
            "@type": "Organization",
            "name": "Happy Aging",
            "url": SITE_URL,
            "logo": {"@type": "ImageObject", "url": LOGO_URL},
        },
        "inLanguage": "en-US",
    }

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Happy Aging Blog Articles",
        "url": BLOG_URL,
        "numberOfItems": len(articles),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": f"{BLOG_URL}/{a['handle']}",
                "name": a["title"],
            }
            for i, a in enumerate(articles[:50])  # top 50 most recent
        ],
    }

    def schema_tag(obj):
        return ('<script type="application/ld+json">\n'
                + json.dumps(obj, ensure_ascii=False, indent=2)
                + '\n</script>')

    return "\n".join([schema_tag(breadcrumb), schema_tag(blog_schema), schema_tag(item_list)])


MARKER_START = "<!-- happy-aging-blog-schema-start -->"
MARKER_END   = "<!-- happy-aging-blog-schema-end -->"

def inject_into_template(content, schema_block):
    """Insert/replace schema block just before </body> or {% endblock %}."""
    tagged = f"{MARKER_START}\n{schema_block}\n{MARKER_END}"

    # Replace existing block if re-running
    if MARKER_START in content:
        content = re.sub(
            re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
            tagged, content, flags=re.DOTALL)
        return content

    # Insert before </body>
    if "</body>" in content:
        return content.replace("</body>", tagged + "\n</body>", 1)

    # Insert before {% endblock %} (some Shopify themes)
    if "{% endblock %}" in content:
        return content.replace("{% endblock %}", tagged + "\n{% endblock %}", 1)

    # Append at end
    return content + "\n" + tagged


def main():
    print("=== patch-blog-schema.py ===\n")

    print("[1/4] Finding active theme...")
    theme_id = get_active_theme_id()
    print(f"  Theme ID: {theme_id}")

    # Try blog.liquid first, then sections/main-blog.liquid (OS 2.0)
    candidates = [
        f"templates/blog.liquid",
        f"templates/blog.json",
        f"sections/main-blog.liquid",
        f"layout/theme.liquid",
    ]

    print("[2/4] Locating blog template asset...")
    target_key = None
    target_asset = None
    for key in candidates:
        asset = get_asset(theme_id, key)
        if asset:
            print(f"  Found: {key}")
            target_key = key
            target_asset = asset
            break

    if not target_asset:
        print("  ERROR: could not find blog template. Keys tried:", candidates)
        sys.exit(1)

    print("[3/4] Fetching recent articles for ItemList...")
    articles = fetch_articles()
    print(f"  {len(articles)} articles fetched")

    schema_block = build_schemas(articles)

    print("[4/4] Injecting schema and updating theme asset...")

    content = target_asset.get("value", "")

    # blog.json is a JSON file (OS 2.0) — inject into the referenced section instead
    if target_key.endswith(".json"):
        try:
            tmpl = json.loads(content)
            sections = tmpl.get("sections", {})
            # Find the main blog section key
            main_key = next((k for k, v in sections.items()
                             if "blog" in v.get("type", "").lower()), None)
            if main_key:
                section_key = f"sections/{sections[main_key]['type']}.liquid"
                print(f"  OS 2.0 theme — patching section: {section_key}")
                sec_asset = get_asset(theme_id, section_key)
                if sec_asset:
                    target_key = section_key
                    content = sec_asset.get("value", "")
                else:
                    print(f"  WARNING: section {section_key} not found, trying layout/theme.liquid")
                    target_key = "layout/theme.liquid"
                    asset = get_asset(theme_id, target_key)
                    content = asset.get("value", "") if asset else ""
        except Exception as e:
            print(f"  WARNING: could not parse blog.json ({e}), patching layout/theme.liquid")
            target_key = "layout/theme.liquid"
            asset = get_asset(theme_id, target_key)
            content = asset.get("value", "") if asset else ""

    new_content = inject_into_template(content, schema_block)

    if new_content == content:
        print("  No changes needed (schema already present and unchanged).")
        return

    put_asset(theme_id, target_key, new_content)
    print(f"  Updated: {target_key}")
    print("\nDone. Schema injected:")
    print("  - BreadcrumbList (Home → Blog)")
    print("  - Blog (name, description, publisher)")
    print("  - ItemList (top 50 articles)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
patch-seo.py — Fix SEO issues on all published Shopify articles:
  1. Inject FAQ JSON-LD schema (for AI/rich-snippet eligibility)
  2. Set summary_html as meta description (≤155 chars)
  3. Re-inject body images matched to each H2 section (section-relevant)

Usage:
    SHOPIFY_TOKEN=shpat_... PEXELS_API_KEY=... python3 articles/patch-seo.py
    Add --schema-only to skip image re-fetch (faster, schema + meta only)
"""

import json, os, re, sys, time, glob
import urllib.request, urllib.parse, urllib.error

SHOPIFY_STORE = "shop-happy-aging.myshopify.com"
BLOG_ID       = "109440303424"
ARTICLES_DIR  = os.path.dirname(os.path.abspath(__file__))

SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN", "").strip()
PEXELS_KEY    = os.environ.get("PEXELS_API_KEY", "").strip()
UNSPLASH_KEY  = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
SCHEMA_ONLY   = "--schema-only" in sys.argv

if not SHOPIFY_TOKEN:
    raise SystemExit("ERROR: Set SHOPIFY_TOKEN")
if not SCHEMA_ONLY and not PEXELS_KEY and not UNSPLASH_KEY:
    print("WARNING: No image API keys set. Running in --schema-only mode.")
    SCHEMA_ONLY = True


# ── FAQ Schema ────────────────────────────────────────────────────────────────

def extract_faq_pairs(html):
    """Extract Q&A pairs from the Frequently Asked Questions section."""
    faq_match = re.search(
        r'<h2[^>]*>Frequently Asked Questions</h2>(.*?)(?:<h2[^>]*>References|$)',
        html, re.DOTALL | re.IGNORECASE)
    if not faq_match:
        return []
    faq_section = faq_match.group(1)
    pairs = []
    for m in re.finditer(r'<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>', faq_section, re.DOTALL):
        question = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        answer   = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        answer   = re.sub(r'\s+', ' ', answer)
        if question and answer and len(question) > 10:
            pairs.append((question, answer))
    return pairs


def build_faq_schema(pairs):
    entities = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}
        }
        for q, a in pairs
    ]
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    return (
        '\n<script type="application/ld+json">\n'
        + json.dumps(schema, ensure_ascii=False, indent=2)
        + '\n</script>\n'
    )


def inject_faq_schema(html, pairs):
    if not pairs:
        return html
    # Remove existing FAQ schema if re-running
    html = re.sub(
        r'\s*<script type="application/ld\+json">\s*\{[^}]*"FAQPage".*?</script>\s*',
        '\n', html, flags=re.DOTALL)
    schema_block = build_faq_schema(pairs)
    # Insert before the FAQ h2
    html = re.sub(
        r'(<h2[^>]*>Frequently Asked Questions</h2>)',
        schema_block + r'\1',
        html, flags=re.IGNORECASE)
    return html


# ── Meta description ──────────────────────────────────────────────────────────

def extract_meta_description(html, max_chars=155):
    """Extract first paragraph text, strip tags, truncate to max_chars."""
    m = re.search(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    if not m:
        return ""
    text = re.sub(r'<[^>]+>', '', m.group(1))
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(' ', 1)[0]
    return truncated.rstrip('.,;:') + '...'


# ── Section-relevant images ───────────────────────────────────────────────────

BLOCKED_TERMS = {
    "nude", "naked", "topless", "nudity", "lingerie", "bikini",
    "underwear", "explicit", "adult content", "erotic", "sensual",
    "sexy", "sexual", "pornographic", "nsfw",
}

_unsplash_req = 0
_unsplash_win = None

def _rate_check_unsplash():
    global _unsplash_req, _unsplash_win
    now = time.time()
    if _unsplash_win is None:
        _unsplash_win = now
    if (now - _unsplash_win) >= 3600:
        _unsplash_req = 0; _unsplash_win = now
    if _unsplash_req >= 45:
        wait = 3605 - (now - _unsplash_win)
        print(f"  [unsplash] rate limit, waiting {int(wait)}s...")
        time.sleep(wait)
        _unsplash_req = 0; _unsplash_win = time.time()


def pexels_search(query):
    if not PEXELS_KEY:
        return None
    for attempt in range(3):
        try:
            url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 10})
            req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            photos = [p for p in (data.get("photos") or [])
                      if not any(t in (p.get("alt") or "").lower() for t in BLOCKED_TERMS)]
            if not photos:
                return None
            p = photos[0]
            return {"src": p["src"]["large2x"], "alt": (p.get("alt") or query)[:120]}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(60 * (attempt + 1))
            else:
                return None
        except Exception:
            return None
    return None


def unsplash_search(query):
    global _unsplash_req
    if not UNSPLASH_KEY:
        return None
    _rate_check_unsplash()
    for attempt in range(3):
        try:
            url = "https://api.unsplash.com/search/photos?" + urllib.parse.urlencode(
                {"query": query, "orientation": "landscape", "per_page": 10,
                 "content_filter": "high"})
            req = urllib.request.Request(url,
                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            _unsplash_req += 1
            results = [p for p in (data.get("results") or [])
                       if not any(t in (p.get("alt_description") or "").lower()
                                  for t in BLOCKED_TERMS)]
            if not results:
                return None
            p = results[0]
            return {"src": p["urls"]["regular"], "alt": (p.get("alt_description") or query)[:120]}
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(65 * (attempt + 1)); _unsplash_req = 0
            else:
                return None
        except Exception:
            return None
    return None


def find_image(query):
    img = pexels_search(query) or unsplash_search(query)
    time.sleep(1.5)
    return img


def h2_to_query(h2_text, article_title=""):
    """Convert an H2 heading to a relevant Pexels/Unsplash search query."""
    skip = {"what", "why", "how", "the", "a", "an", "and", "or", "of", "to",
            "is", "are", "for", "after", "with", "your", "that", "its", "in",
            "on", "at", "by", "does", "do", "can", "will", "about", "from",
            "this", "these", "40", "over", "women", "woman"}
    words = [w.strip(".,?:!-()") for w in h2_text.split()
             if w.lower().strip(".,?:!-()") not in skip and len(w) > 2][:5]
    if not words:
        words = [w.strip(".,?:!-()") for w in article_title.split()
                 if w.lower().strip(".,?:!-()") not in skip][:4]
    return "woman " + " ".join(words).lower() + " wellness health"


def inject_section_images(html, article_title):
    """Re-inject body images, one per H2 section, each matched to that section's topic."""
    # Remove previously injected figures
    html = re.sub(
        r'\s*<figure class="article-stock-image"[^>]*>.*?</figure>\s*',
        '\n', html, flags=re.DOTALL)

    # Find all H2 positions (skip FAQ and References)
    skip_h2 = {"frequently asked questions", "references", "faq"}
    h2_matches = [(m.end(), re.sub(r'<[^>]+>', '', m.group(1)).strip())
                  for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
                  if re.sub(r'<[^>]+>', '', m.group(1)).strip().lower() not in skip_h2]

    if not h2_matches:
        return html

    # Skip first H2 (too close to top); use remaining, max 3 images
    targets = h2_matches[1:4]

    offset = 0
    for pos, h2_text in targets:
        query = h2_to_query(h2_text, article_title)
        print(f"    section img: '{h2_text[:45]}' → '{query[:55]}'")
        img = find_image(query)
        if not img:
            print(f"    no image found for: {query[:55]}")
            continue
        alt = img.get("alt", article_title)[:140].replace('"', "'")
        figure = (
            f'\n<figure class="article-stock-image" style="margin:24px 0">'
            f'<img src="{img["src"]}" alt="{alt}" '
            f'style="width:100%;border-radius:12px;display:block">'
            f'</figure>\n'
        )
        insert_at = pos + offset
        html = html[:insert_at] + figure + html[insert_at:]
        offset += len(figure)

    return html


# ── Shopify helpers ───────────────────────────────────────────────────────────

def shopify_get_articles():
    articles = {}
    page_info = None
    base = f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}/articles.json"
    while True:
        params = {"limit": 250, "fields": "id,handle,title"}
        if page_info:
            params["page_info"] = page_info
        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url,
            headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN})
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        for a in data.get("articles", []):
            articles[a["handle"]] = {"id": a["id"], "title": a.get("title", "")}
        link = resp.headers.get("Link", "")
        next_url = next((p.strip().split(";")[0].strip("<> ")
                         for p in link.split(",") if 'rel="next"' in p), None)
        if not next_url:
            break
        pi = re.search(r"page_info=([^&]+)", next_url)
        if not pi:
            break
        page_info = pi.group(1)
    return articles


def shopify_update(article_id, body_html, summary_html):
    url = (f"https://{SHOPIFY_STORE}/admin/api/2024-01/blogs/{BLOG_ID}"
           f"/articles/{article_id}.json")
    payload = {"article": {
        "id": article_id,
        "body_html": body_html,
        "summary_html": summary_html,
    }}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PUT",
        headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    mode = "schema + meta only" if SCHEMA_ONLY else "schema + meta + section images"
    print(f"=== patch-seo.py [{mode}] ===\n")

    print("[1/3] Fetching Shopify article list...")
    existing = shopify_get_articles()
    print(f"  {len(existing)} articles on Shopify.\n")

    meta_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.meta.json")))
    published = [
        mf for mf in meta_files
        if (lambda s: s in existing and os.path.exists(
            os.path.join(ARTICLES_DIR, f"{s}-final.html")))(
            json.load(open(mf)).get("slug") or
            os.path.basename(mf).replace(".meta.json", ""))
    ]
    print(f"[2/3] Processing {len(published)} published articles...\n")

    ok = failed = schema_added = meta_set = img_updated = 0

    for mf in published:
        meta   = json.load(open(mf))
        slug   = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        title  = meta.get("title", slug)
        html_f = os.path.join(ARTICLES_DIR, f"{slug}-final.html")
        art_id = existing[slug]["id"]

        body = open(html_f).read()

        # 1. FAQ Schema
        pairs = extract_faq_pairs(body)
        if pairs:
            body = inject_faq_schema(body, pairs)
            schema_added += 1

        # 2. Meta description
        meta_desc = extract_meta_description(body)

        # 3. Section images (skip if --schema-only or already has stock images)
        if not SCHEMA_ONLY:
            print(f"  {slug[:55]}")
            body = inject_section_images(body, title)
            img_updated += 1
        else:
            print(f"  {slug[:55]} (schema+meta)")

        meta_set += 1

        # Write back
        open(html_f, "w").write(body)

        # Update Shopify
        try:
            shopify_update(art_id, body, meta_desc)
            ok += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:120]
            print(f"    FAIL {e.code}: {err}")
            failed += 1
        except Exception as e:
            print(f"    FAIL: {str(e)[:80]}")
            failed += 1

        time.sleep(1.2)

    print(f"\n[3/3] Done.")
    print(f"  FAQ schema injected: {schema_added}")
    print(f"  Meta descriptions set: {meta_set}")
    print(f"  Section images updated: {img_updated}")
    print(f"  Shopify updates: {ok} OK, {failed} failed")


if __name__ == "__main__":
    main()

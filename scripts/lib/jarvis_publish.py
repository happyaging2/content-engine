"""Shared helpers for the JARVIS publish pipeline.

Use from inline `python3 << PYEOF` blocks in scripts/qa-and-publish.sh:

    import sys; sys.path.insert(0, "scripts/lib")
    from jarvis_publish import http_retry, validate_meta, fetch_product_handles

Two responsibilities:
  1. http_retry  : exponential backoff for flaky upstreams (Unsplash/Pexels/Shopify)
  2. validation  : reject metas that would publish broken (bad slug, unknown
                   product handle, generic image_query) before we POST.
"""
import json
import re
import time
import urllib.error
import urllib.request


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GENERIC_IMAGE_TERMS = {
    "wellness", "health", "happy", "lifestyle", "people", "woman",
    "women", "person", "background", "abstract", "stock", "image",
}
PRODUCTS_JSON = "https://happyaging.com/products.json?limit=250"


def http_retry(fn, attempts=4, base_delay=2.0, label=""):
    """Run fn() with exponential backoff on transient failures.

    Retries on URLError, timeouts, and 5xx. Re-raises 4xx immediately
    (auth/permanent errors should not be retried)."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                raise
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        if i < attempts - 1:
            delay = base_delay * (2 ** i)
            print(f"    retry {label} in {delay:.0f}s ({type(last).__name__})")
            time.sleep(delay)
    raise last


def fetch_product_handles():
    """Pull live product handles from happyaging.com. Returns set or None
    if the call fails (caller decides whether to halt)."""
    try:
        def _go():
            req = urllib.request.Request(PRODUCTS_JSON,
                headers={"User-Agent": "JARVIS/1.0"})
            return json.loads(urllib.request.urlopen(req, timeout=15).read())
        data = http_retry(_go, label="products.json")
        return {p["handle"] for p in data.get("products", [])}
    except Exception as e:
        print(f"  WARN: could not fetch product handles: {str(e)[:80]}")
        return None


def validate_meta(meta, known_handles=None):
    """Return list of validation errors for a single meta dict.

    Empty list means safe to publish."""
    errors = []
    slug = meta.get("slug", "")
    if not slug or not SLUG_RE.match(slug):
        errors.append(f"invalid slug: {slug!r}")

    title = (meta.get("title") or "").strip()
    if not title:
        errors.append("missing title")
    elif title.upper() == title and len(title) > 10:
        errors.append("title is ALL CAPS")

    handle = meta.get("product_handle")
    if handle and known_handles is not None and handle not in known_handles:
        errors.append(f"unknown product_handle: {handle!r}")

    iq = (meta.get("image_query") or "").strip()
    if iq:
        words = iq.lower().split()
        if len(words) < 3:
            errors.append(f"image_query too short ({len(words)} words): {iq!r}")
        elif all(w in GENERIC_IMAGE_TERMS for w in words):
            errors.append(f"image_query is generic: {iq!r}")

    body_qs = meta.get("body_image_queries") or []
    for j, q in enumerate(body_qs):
        if len((q or "").split()) < 2:
            errors.append(f"body_image_queries[{j}] too short: {q!r}")

    return errors


if __name__ == "__main__":
    # Quick self-check: validate every meta in articles/.
    import glob, sys
    handles = fetch_product_handles()
    bad = 0
    total = 0
    for mf in sorted(glob.glob("articles/*.meta.json")):
        try:
            meta = json.load(open(mf))
        except Exception as e:
            print(f"  PARSE-ERR {mf}: {e}")
            bad += 1
            continue
        total += 1
        errs = validate_meta(meta, handles)
        if errs:
            bad += 1
            print(f"  FAIL {meta.get('slug', mf)}")
            for e in errs:
                print(f"    - {e}")
    print(f"\n{total - bad}/{total} metas pass; {bad} fail")
    sys.exit(1 if bad else 0)

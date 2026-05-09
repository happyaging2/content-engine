#!/usr/bin/env python3
"""
enrich-citations-from-pubmed.py — Convert raw PMIDs found in articles into
structured `citations` entries inside each meta.json.

For every PMID in the article body, fetch metadata from PubMed E-utilities
(esummary.fcgi) and populate `citations` as:
    {pmid, title, journal, year, study_type, n}

`study_type` is heuristically inferred from the article title (RCT, meta-analysis,
cohort, etc.). `n` (sample size) is best-effort regex from the abstract.

NCBI rate limit: 3 req/sec without API key, 10 req/sec with NCBI_API_KEY.

Usage:
    python3 scripts/enrich-citations-from-pubmed.py
    NCBI_API_KEY=... python3 scripts/enrich-citations-from-pubmed.py
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES = os.path.join(ROOT, "articles")
NCBI_KEY = os.environ.get("NCBI_API_KEY", "").strip()
DELAY = 0.12 if NCBI_KEY else 0.4

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_pubmed(pmid: str) -> dict | None:
    qs = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    if NCBI_KEY:
        qs["api_key"] = NCBI_KEY
    url = f"{EUTILS}/efetch.fcgi?" + urllib.parse.urlencode(qs)
    try:
        raw = urllib.request.urlopen(url, timeout=20).read()
    except Exception as e:
        return {"error": str(e)}
    try:
        root = ET.fromstring(raw)
        article = root.find(".//PubmedArticle/MedlineCitation/Article")
        if article is None:
            return None
        title = (article.findtext("ArticleTitle") or "").strip()
        journal = (article.findtext("Journal/Title") or "").strip()
        year = (
            article.findtext("Journal/JournalIssue/PubDate/Year")
            or article.findtext("Journal/JournalIssue/PubDate/MedlineDate")
            or ""
        )
        if year:
            year = re.match(r"\d{4}", year).group(0) if re.match(r"\d{4}", year) else ""
        pub_types = [pt.text for pt in article.findall("PublicationTypeList/PublicationType")]
        abstract = " ".join(
            (a.text or "") for a in article.findall("Abstract/AbstractText")
        )
        # Sample size heuristic
        m = re.search(r"\b(?:n\s*=\s*|enrolled\s+|included\s+)(\d{2,5})\b", abstract, re.I)
        n = int(m.group(1)) if m else None
        # Study type heuristic
        types_lower = [t.lower() for t in pub_types if t]
        if any("meta-analysis" in t for t in types_lower):
            study_type = "Meta-analysis"
        elif any("systematic review" in t for t in types_lower):
            study_type = "Systematic Review"
        elif any("randomized" in t for t in types_lower):
            study_type = "RCT"
        elif any("review" in t for t in types_lower):
            study_type = "Review"
        elif any("clinical trial" in t for t in types_lower):
            study_type = "Clinical Trial"
        else:
            study_type = "Observational"
        return {
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "year": int(year) if year else None,
            "study_type": study_type,
            "n": n,
        }
    except Exception as e:
        return {"error": str(e)}


def extract_pmids(html: str) -> list[str]:
    pmids = set()
    for m in re.finditer(r"PMID[:\s]*(\d{6,9})", html, re.IGNORECASE):
        pmids.add(m.group(1))
    for m in re.finditer(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d{6,9})", html):
        pmids.add(m.group(1))
    return sorted(pmids)


def main():
    cache: dict[str, dict] = {}
    cache_path = os.path.join(ROOT, ".pubmed-cache.json")
    if os.path.exists(cache_path):
        cache = json.load(open(cache_path))

    metas = sorted(glob.glob(os.path.join(ARTICLES, "*.meta.json")))
    print(f"Enriching citations for {len(metas)} articles...")

    enriched = 0
    new_pmids = 0
    for mf in metas:
        meta = json.load(open(mf))
        slug = meta.get("slug") or os.path.basename(mf).replace(".meta.json", "")
        html_path = os.path.join(ARTICLES, f"{slug}-final.html")
        if not os.path.exists(html_path):
            html_path = os.path.join(ARTICLES, f"{slug}.html")
        if not os.path.exists(html_path):
            continue
        html = open(html_path).read()
        pmids = extract_pmids(html)
        if not pmids:
            continue

        existing = {c.get("pmid"): c for c in (meta.get("citations") or []) if c.get("pmid")}
        citations = list(existing.values())
        added = 0
        for pmid in pmids:
            if pmid in existing and existing[pmid].get("title"):
                continue
            if pmid in cache and cache[pmid].get("title"):
                cit = cache[pmid]
            else:
                cit = fetch_pubmed(pmid)
                time.sleep(DELAY)
                new_pmids += 1
                if cit and "error" not in cit:
                    cache[pmid] = cit
                else:
                    continue
            if cit and cit.get("title"):
                # Replace stub if exists
                citations = [c for c in citations if c.get("pmid") != pmid]
                citations.append(cit)
                added += 1
        if added:
            meta["citations"] = citations
            json.dump(meta, open(mf, "w"), indent=2, ensure_ascii=False)
            enriched += 1
            print(f"  ✓ {slug[:60]} (+{added})")

    json.dump(cache, open(cache_path, "w"), indent=2)
    print(f"\nDone. {enriched} meta files enriched. {new_pmids} new PubMed lookups.")


if __name__ == "__main__":
    main()

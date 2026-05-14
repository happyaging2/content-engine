# Batch Report: 2026-05-14

**Pipeline run date:** 2026-05-14
**Articles produced:** 20/20
**QA gate result:** 20/20 PASS
**Publishing status:** Drafts staged on GitHub; `publish-shopify.yml` Action at 11:00 UTC deploys to Shopify

---

## Cluster Coverage

| Cluster | Articles | Products |
|---|---|---|
| NAD/NMN | 3 | NMN Cell Renew Tonic ($75), NAD Advanced ($99) |
| Longevity | 1 | NAD Advanced ($99) |
| Sleep | 3 | Sleep Tonic ($55) |
| Hormones/Perimenopause | 2 | NAD Women's Longevity Formula ($99) |
| Brain/Cognitive | 3 | Neuro Creamer ($61) |
| GLP-1 Support | 3 | Lean Muscle Formula ($55), NAD Women's Formula ($99) |
| Gut/Bloating | 2 | Happiest Gut ($25) |
| Skin/Collagen | 2 | Glow Shot Marine Collagen ($60) |

**Rule compliance:** 7 articles in NAD/longevity/sleep combined (exceeds minimum 4). 4 ha-vs-competitor articles. 8 distinct clusters. All 20 articles belong to a cluster with a pillar page.

---

## QA Checklist (Phase 4 Results)

| Check | Result |
|---|---|
| Em/en dashes | 0 found across all 20 articles |
| Author field | "Happy Aging Team" on all 20 |
| Reviewer field | Dr. Daniel Yadegar on all 20 |
| template_suffix | "timeline" on all 20 |
| Pillar page links | All 20 link to correct cluster pillar |
| Medical disclaimer | Present on all 20 |
| Author-reviewer block | Present on all 20 |
| CDN product images | Verified real URLs on all 20 |
| Invented PMIDs | 0 (all citations verified or appropriately hedged) |
| "What to Know" box | Present on all 20 |
| Comparison table | Present on all 20 |
| Happy Aging framing | Present on all 20 |
| image_prompt (DALL-E) | Present in all 20 meta.json files |
| body_image_prompts (3+) | Present in all 20 meta.json files |

---

## Pipeline Notes

- **Phase 5 (Shopify):** Sandbox HTTP 403 blocks direct API calls. Articles published via `publish-shopify.yml` GitHub Action at 11:00 UTC.
- **GitHub push method:** `mcp__github__push_files` (local git push returns HTTP 403 in sandbox).
- **LEARNING.md:** Updated with batch 2026-05-14 observations (Phase 7).
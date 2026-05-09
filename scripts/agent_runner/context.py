"""
System-prompt assembly with prompt caching.

The pipeline reads the SAME large context (brand.md, hero-product.json,
LEARNING.md, agent prompt) on every Phase 3 article and every Phase 4 review.
We render those as a list of text blocks with `cache_control: ephemeral` on
the LAST stable block, so subsequent calls within the 5-minute TTL window
hit the cache (~10% of base input price).

Render order: tools -> system -> messages. Cache_control on the last system
block caches everything before it (no tools defined in this pipeline yet).

Silent invalidators we explicitly avoid:
- No timestamps in the system prompt (date goes in user message instead)
- No per-batch IDs in system context
- json.dumps(..., sort_keys=True) for hero-product.json so dict order is stable
- Stable file read order (alphabetical glob)
"""

from __future__ import annotations

import json
import os
from typing import Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTS_DIR = os.path.join(ROOT, "agents")
CONFIG_DIR = os.path.join(ROOT, "config")
LEARNING_PATH = os.path.join(ROOT, "LEARNING.md")


def _read(path: str) -> str:
    if not os.path.exists(path):
        return ""
    return open(path, encoding="utf-8").read()


def _stable_json(path: str) -> str:
    """Read JSON and re-emit deterministically so cache prefix is byte-stable."""
    if not os.path.exists(path):
        return ""
    data = json.load(open(path, encoding="utf-8"))
    return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)


def _block(text: str, cache: bool = False) -> dict:
    block: dict = {"type": "text", "text": text}
    if cache:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def _shared_brand_blocks() -> list[dict]:
    """Stable context every phase loads. NOT cached individually — the caller
    decides where to put the cache breakpoint based on what comes after."""
    blocks = []
    brand = _read(os.path.join(CONFIG_DIR, "brand.md"))
    if brand:
        blocks.append(_block(f"# Brand context\n\n{brand}"))

    hero = _stable_json(os.path.join(CONFIG_DIR, "hero-product.json"))
    if hero:
        blocks.append(
            _block(
                "# Hero product (single source of truth for NAD Advanced)\n\n"
                "```json\n" + hero + "\n```"
            )
        )

    competitors = _stable_json(os.path.join(CONFIG_DIR, "competitors.json"))
    if competitors:
        blocks.append(
            _block(
                "# Competitor registry (per cluster, used by comparison content)\n\n"
                "```json\n" + competitors + "\n```"
            )
        )

    learning = _read(LEARNING_PATH)
    if learning:
        blocks.append(_block(f"# Learning rules (feedback loop)\n\n{learning}"))

    return blocks


def build_phase_system_blocks(
    agent_files: Iterable[str],
) -> list[dict]:
    """Generic phase system prompt builder.

    `agent_files` are filenames inside agents/ (e.g. ['01-opportunity-engine.md']).
    The agent prompts go FIRST (most stable across calls), brand context next,
    cache breakpoint on the LAST block.
    """
    blocks: list[dict] = []
    for fname in agent_files:
        text = _read(os.path.join(AGENTS_DIR, fname))
        if text:
            blocks.append(_block(f"# Agent prompt: {fname}\n\n{text}"))
    blocks.extend(_shared_brand_blocks())
    if blocks:
        # cache_control on the last block caches everything above (and tools,
        # if any). Stable across all parallel Phase 3 writers in the same run.
        last = dict(blocks[-1])
        last["cache_control"] = {"type": "ephemeral"}
        blocks[-1] = last
    return blocks


def build_writer_system_blocks(comparison: bool = False) -> list[dict]:
    """Phase 3 writer system prompt. Extended with 03b for comparison briefs."""
    files = ["03-content-writer.md"]
    if comparison:
        files.append("03b-comparison-writer.md")
    return build_phase_system_blocks(files)

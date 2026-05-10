"""
Agent runner — autonomous Phase 1 -> Phase 4 execution for the JARVIS content
pipeline. Calls the Claude API with prompt caching, streaming, parallel Phase 3
(10 articles concurrently), and JSON-schema validation on Phase 1 / Phase 4.

Models:
  - Opus 4.7 (claude-opus-4-7) for Phase 1 (strategy) and Phase 4 (quality gate)
  - Sonnet 4.6 (claude-sonnet-4-6) for Phase 3 (high-volume writing)

Entry point: scripts/run-pipeline.py
"""

from .context import build_writer_system_blocks, build_phase_system_blocks
from .phases import run_phase1, run_phase3_parallel, run_phase4

__all__ = [
    "build_writer_system_blocks",
    "build_phase_system_blocks",
    "run_phase1",
    "run_phase3_parallel",
    "run_phase4",
]

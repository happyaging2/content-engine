"""
Agent runner — autonomous Phase 1 -> Phase 4 execution for the JARVIS content
pipeline. Calls the Claude API with prompt caching, streaming, parallel Phase 3
(10 articles concurrently), and JSON-schema validation on Phase 1 / Phase 4.

Models:
  - Opus 4.7 (claude-opus-4-7) for Phase 1 (strategy)
  - Sonnet 4.6 (claude-sonnet-4-6) for Phase 3 writers and Phase 4 gate
    (Phase 4 model overridable via PHASE4_MODEL env var)

Entry point: scripts/run-pipeline.py
"""

from .context import build_writer_system_blocks, build_phase_system_blocks
from .phases import run_phase1, run_phase3_parallel, run_phase4, run_phase4_parallel

__all__ = [
    "build_writer_system_blocks",
    "build_phase_system_blocks",
    "run_phase1",
    "run_phase3_parallel",
    "run_phase4",
    "run_phase4_parallel",
]

# dna/__init__.py — Re-exports for the DNA subpackage
# Created: 2026-02-22 — Initial DNA module setup

from __future__ import annotations

from soul_protocol.dna.prompt import dna_to_markdown, dna_to_system_prompt

__all__ = ["dna_to_system_prompt", "dna_to_markdown"]

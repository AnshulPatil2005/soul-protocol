# dna/__init__.py — Re-exports for the DNA subpackage
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Initial DNA module setup

from __future__ import annotations

from soul_protocol.runtime.dna.prompt import dna_to_markdown, dna_to_system_prompt

__all__ = ["dna_to_system_prompt", "dna_to_markdown"]

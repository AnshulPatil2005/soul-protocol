# spec/context/__init__.py — Protocol-level context management interfaces.
# Created: v0.3.0 — ContextEngine protocol, Pydantic models for Lossless Context
# Management (LCM). Part of the spec protocol layer — no opinionated implementations.

from .models import (
    AssembleResult,
    CompactionLevel,
    ContextMessage,
    ContextNode,
    DescribeResult,
    ExpandResult,
    GrepResult,
)
from .protocol import ContextEngine

__all__ = [
    "AssembleResult",
    "CompactionLevel",
    "ContextEngine",
    "ContextMessage",
    "ContextNode",
    "DescribeResult",
    "ExpandResult",
    "GrepResult",
]

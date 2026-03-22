# spec/a2a.py — A2A (Agent-to-Agent) protocol models for Agent Card interop.
# Created: 2026-03-23 — Pydantic models mapping Google's A2A Agent Card spec
#   to Soul Protocol primitives. Includes A2ASkill, A2AAgentCard, and
#   SoulExtension for embedding soul identity into Agent Card extensions.

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class A2ASkill(BaseModel):
    """A single skill advertised in an A2A Agent Card.

    Maps to the ``skills`` array in the Agent Card JSON spec.
    """

    id: str
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class SoulExtension(BaseModel):
    """Soul Protocol extension block for an A2A Agent Card.

    Embedded under ``extensions.soul`` to advertise that the agent
    has a persistent Digital Soul with identity, personality, and memory.
    """

    did: str = ""
    personality: dict[str, float] = Field(default_factory=dict)
    soul_version: str = ""
    protocol: str = "dsp/1.0"


class A2AAgentCard(BaseModel):
    """Google A2A Protocol Agent Card — the public identity of an agent.

    See https://google.github.io/A2A for the full spec. This model covers
    the fields relevant to Soul Protocol interop.
    """

    name: str
    description: str = ""
    url: str = ""
    version: str = ""
    provider: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    skills: list[A2ASkill] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)

# parsers/markdown.py — Parse soul.md files (with optional YAML frontmatter) into SoulConfig
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — Regex-based markdown parser for soul definition files

from __future__ import annotations

import re

import yaml

from soul_protocol.runtime.identity.did import generate_did
from soul_protocol.runtime.types import (
    DNA,
    CoreMemory,
    Identity,
    Personality,
    SoulConfig,
)

# Matches YAML frontmatter between --- delimiters
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Matches top-level markdown headings: # Heading
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _extract_frontmatter(content: str) -> tuple[dict, str]:
    """Split optional YAML frontmatter from the markdown body.

    Returns:
        A tuple of (frontmatter_dict, remaining_body).
    """
    match = _FRONTMATTER_RE.match(content)
    if match:
        fm_text = match.group(1)
        body = content[match.end() :]
        parsed = yaml.safe_load(fm_text) or {}
        return parsed, body
    return {}, content


def _split_sections(body: str) -> dict[str, str]:
    """Split markdown body into {heading: content} sections.

    Only top-level headings (# Heading) are treated as section delimiters.
    Content before the first heading is stored under the empty-string key.
    """
    sections: dict[str, str] = {}
    parts = _HEADING_RE.split(body)

    # parts is [pre-heading-text, heading1, content1, heading2, content2, ...]
    if parts[0].strip():
        sections[""] = parts[0].strip()

    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        content = parts[i + 1].strip() if (i + 1) < len(parts) else ""
        sections[heading.lower()] = content

    return sections


def _parse_list_items(text: str) -> list[str]:
    """Extract items from a markdown list (- item or * item)."""
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")):
            items.append(line[2:].strip())
        elif line and not line.startswith("#"):
            # Plain text lines treated as items too
            items.append(line)
    return items


def _parse_personality(text: str) -> Personality:
    """Parse personality traits from a section body.

    Supports formats like:
        - openness: 0.8
        - Openness: 0.8
        openness: 0.8
    """
    traits: dict[str, float] = {}
    trait_names = {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}

    for line in text.splitlines():
        line = line.strip().lstrip("- *")
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            if key in trait_names:
                try:
                    traits[key] = float(value.strip())
                except ValueError:
                    pass

    return Personality(**traits)


async def soul_from_md(content: str) -> SoulConfig:
    """Parse a soul.md file into a SoulConfig.

    The file may optionally start with YAML frontmatter (between --- delimiters).
    The body is split by # Heading sections. Recognized sections:
        - Identity: name, archetype, origin story
        - Personality: OCEAN trait scores
        - Core Values / Values: list of values
        - Persona / About: persona core memory text

    Args:
        content: Raw string content of a soul.md file.

    Returns:
        A SoulConfig populated from the parsed markdown.
    """
    frontmatter, body = _extract_frontmatter(content)
    sections = _split_sections(body)

    # --- Name & archetype ---
    name = frontmatter.get("name", "")
    archetype = frontmatter.get("archetype", "")
    origin_story = frontmatter.get("origin_story", frontmatter.get("origin", ""))

    # Try the identity section if frontmatter didn't provide a name
    if not name and "identity" in sections:
        id_text = sections["identity"]
        for line in id_text.splitlines():
            line = line.strip().lstrip("- *")
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower()
                if key == "name":
                    name = value.strip()
                elif key == "archetype":
                    archetype = value.strip()
                elif key in ("origin", "origin_story"):
                    origin_story = value.strip()

    # Fallback name
    if not name:
        name = "unnamed-soul"

    # --- DID ---
    did = frontmatter.get("did", generate_did(name))

    # --- Personality ---
    personality = Personality()
    if "personality" in sections:
        personality = _parse_personality(sections["personality"])

    # --- Core values ---
    core_values: list[str] = []
    for key in ("core values", "values"):
        if key in sections:
            core_values = _parse_list_items(sections[key])
            break
    # Also check frontmatter
    if not core_values and "core_values" in frontmatter:
        core_values = frontmatter["core_values"]

    # --- Core memory (persona section) ---
    persona = ""
    for key in ("persona", "about", "description"):
        if key in sections:
            persona = sections[key]
            break

    # --- Build the SoulConfig ---
    identity = Identity(
        did=did,
        name=name,
        archetype=archetype,
        origin_story=origin_story,
        core_values=core_values,
    )

    dna = DNA(personality=personality)
    core_memory = CoreMemory(persona=persona)

    return SoulConfig(
        identity=identity,
        dna=dna,
        core_memory=core_memory,
    )

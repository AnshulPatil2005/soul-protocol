# parsers/json_parser.py — Parse soul.json configuration files into SoulConfig
# Updated: runtime restructure — fixed absolute import paths to soul_protocol.runtime.
# Created: 2026-02-22 — JSON parser using Pydantic's model_validate_json

from __future__ import annotations

from soul_protocol.runtime.types import SoulConfig


def parse_soul_json(content: str) -> SoulConfig:
    """Parse a soul.json string into a SoulConfig.

    Uses Pydantic's model_validate_json which handles JSON deserialization
    and validation in a single step.

    Args:
        content: Raw JSON string.

    Returns:
        A validated SoulConfig instance.

    Raises:
        pydantic.ValidationError: If the JSON doesn't match the SoulConfig schema.
        ValueError: If the JSON is malformed.
    """
    return SoulConfig.model_validate_json(content)

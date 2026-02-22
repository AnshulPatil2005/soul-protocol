# parsers/yaml_parser.py — Parse soul.yaml configuration files into SoulConfig
# Created: 2026-02-22 — YAML parser using pyyaml + Pydantic validation

from __future__ import annotations

import yaml

from soul_protocol.types import SoulConfig


def parse_soul_yaml(content: str) -> SoulConfig:
    """Parse a soul.yaml string into a SoulConfig.

    Uses yaml.safe_load to deserialize the YAML, then validates through
    Pydantic's model_validate for type checking and defaults.

    Args:
        content: Raw YAML string.

    Returns:
        A validated SoulConfig instance.

    Raises:
        yaml.YAMLError: If the YAML is malformed.
        pydantic.ValidationError: If the data doesn't match the SoulConfig schema.
    """
    data = yaml.safe_load(content)
    return SoulConfig.model_validate(data)

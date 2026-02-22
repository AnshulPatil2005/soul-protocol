# export/unpack.py — Load a SoulConfig from a .soul zip archive.
# Created: 2026-02-22 — Reads soul.json from a zip archive and validates it
# back into a SoulConfig model.

from __future__ import annotations

import io
import json
import zipfile

from soul_protocol.types import SoulConfig


async def unpack_soul(data: bytes) -> SoulConfig:
    """Load a ``SoulConfig`` from a ``.soul`` zip archive.

    Reads the ``soul.json`` entry from the archive and validates it.

    Args:
        data: Raw bytes of the zip archive (as produced by ``pack_soul``).

    Returns:
        A validated ``SoulConfig`` instance.

    Raises:
        KeyError: If the archive does not contain ``soul.json``.
        pydantic.ValidationError: If the JSON does not match the schema.
    """
    buf = io.BytesIO(data)

    with zipfile.ZipFile(buf, "r") as zf:
        raw = zf.read("soul.json")
        payload = json.loads(raw)

    return SoulConfig.model_validate(payload)

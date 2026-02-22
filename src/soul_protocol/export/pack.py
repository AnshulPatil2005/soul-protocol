# export/pack.py — Create .soul zip archives from a SoulConfig.
# Created: 2026-02-22 — Bundles manifest.json, soul.json, dna.md, state.json,
# and memory/core.json into an in-memory zip archive.

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime

from soul_protocol.dna.prompt import dna_to_markdown
from soul_protocol.types import SoulConfig, SoulManifest


async def pack_soul(config: SoulConfig) -> bytes:
    """Create a ``.soul`` zip archive from a ``SoulConfig``.

    The archive contains:

    - ``manifest.json`` — archive metadata (``SoulManifest``)
    - ``soul.json`` — the complete ``SoulConfig``
    - ``dna.md`` — human-readable DNA markdown
    - ``state.json`` — current ``SoulState`` snapshot
    - ``memory/core.json`` — ``CoreMemory`` (persona + human)

    Returns:
        The zip archive as raw bytes.
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # soul.json — full config
        soul_json = config.model_dump_json(indent=2)
        zf.writestr("soul.json", soul_json)

        # dna.md — human-readable personality blueprint
        dna_md = dna_to_markdown(config.identity, config.dna)
        zf.writestr("dna.md", dna_md)

        # state.json — current state
        state_json = config.state.model_dump_json(indent=2)
        zf.writestr("state.json", state_json)

        # memory/core.json — always-loaded core memory
        core_json = config.core_memory.model_dump_json(indent=2)
        zf.writestr("memory/core.json", core_json)

        # manifest.json — archive metadata (written last so we know contents)
        manifest = SoulManifest(
            format_version="1.0.0",
            created=config.identity.born,
            exported=datetime.now(),
            soul_id=config.identity.did,
            soul_name=config.identity.name,
            checksum="",  # MVP: no checksum yet
            stats={
                "version": config.version,
                "lifecycle": config.lifecycle.value,
            },
        )
        manifest_json = manifest.model_dump_json(indent=2)
        zf.writestr("manifest.json", manifest_json)

    return buf.getvalue()

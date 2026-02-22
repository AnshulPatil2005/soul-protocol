# storage/file.py — FileStorage backend persisting souls to the local filesystem.
# Updated: 2026-02-22 — Added save_soul_full() and load_soul_full() for full
# memory persistence. Writes memory/ directory with core.json, episodic.json,
# semantic.json, procedural.json, graph.json alongside soul.json, dna.md, state.json.

from __future__ import annotations

import json
import shutil
from pathlib import Path

from soul_protocol.dna.prompt import dna_to_markdown
from soul_protocol.types import SoulConfig

DEFAULT_SOUL_DIR: Path = Path.home() / ".soul"


class FileStorage:
    """Filesystem-backed soul storage.

    Directory layout::

        <base_dir>/
            <soul_id>/
                soul.json    — full SoulConfig serialization
                dna.md       — human-readable DNA markdown
                state.json   — current SoulState snapshot
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or DEFAULT_SOUL_DIR

    async def save(
        self, soul_id: str, config: SoulConfig, path: Path | None = None
    ) -> None:
        """Save a soul to the filesystem."""
        target_dir = (path or self._base_dir) / soul_id
        target_dir.mkdir(parents=True, exist_ok=True)

        # soul.json — full config
        soul_json_path = target_dir / "soul.json"
        soul_json_path.write_text(
            config.model_dump_json(indent=2), encoding="utf-8"
        )

        # dna.md — human-readable personality
        dna_md_path = target_dir / "dna.md"
        dna_md_path.write_text(
            dna_to_markdown(config.identity, config.dna), encoding="utf-8"
        )

        # state.json — current state snapshot
        state_json_path = target_dir / "state.json"
        state_json_path.write_text(
            config.state.model_dump_json(indent=2), encoding="utf-8"
        )

    async def load(
        self, soul_id: str, path: Path | None = None
    ) -> SoulConfig | None:
        """Load a soul from the filesystem, returning ``None`` if not found."""
        target_dir = (path or self._base_dir) / soul_id
        soul_json_path = target_dir / "soul.json"

        if not soul_json_path.exists():
            return None

        raw = soul_json_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return SoulConfig.model_validate(data)

    async def delete(self, soul_id: str) -> bool:
        """Delete a soul directory. Returns ``True`` if it existed."""
        target_dir = self._base_dir / soul_id
        if target_dir.exists():
            shutil.rmtree(target_dir)
            return True
        return False

    async def list_souls(self) -> list[str]:
        """List all soul IDs stored under the base directory."""
        if not self._base_dir.exists():
            return []
        return [
            p.name
            for p in sorted(self._base_dir.iterdir())
            if p.is_dir() and (p / "soul.json").exists()
        ]


# ------------------------------------------------------------------
# Convenience functions
# ------------------------------------------------------------------


async def save_soul(config: SoulConfig, path: Path | None = None) -> None:
    """Save a soul using the default FileStorage backend.

    The soul is identified by ``config.identity.did``.  If ``path`` is
    provided it is used as the base directory instead of ``~/.soul/``.
    """
    storage = FileStorage(base_dir=path)
    soul_id = config.identity.did or config.identity.name
    await storage.save(soul_id, config, path=None)


async def load_soul(path: Path) -> SoulConfig | None:
    """Load a soul from a specific directory path.

    ``path`` should point to a directory containing ``soul.json``.
    Returns ``None`` if the file does not exist.
    """
    soul_json = path / "soul.json"
    if not soul_json.exists():
        return None

    raw = soul_json.read_text(encoding="utf-8")
    data = json.loads(raw)
    return SoulConfig.model_validate(data)


# ------------------------------------------------------------------
# Full memory persistence functions
# ------------------------------------------------------------------


async def save_soul_full(
    config: SoulConfig,
    memory_data: dict,
    path: Path | None = None,
) -> None:
    """Save soul config + full memory data to disk.

    Writes the standard soul files (soul.json, dna.md, state.json) plus
    a ``memory/`` subdirectory containing per-tier JSON files:
    core.json, episodic.json, semantic.json, procedural.json, graph.json.

    Args:
        config: The SoulConfig to persist.
        memory_data: Dict as produced by MemoryManager.to_dict().
        path: Target directory. Defaults to ``~/.soul/<soul_id>/``.
    """
    soul_dir = path or DEFAULT_SOUL_DIR / (config.identity.did or config.identity.name)
    soul_dir.mkdir(parents=True, exist_ok=True)

    # Config files
    (soul_dir / "soul.json").write_text(
        config.model_dump_json(indent=2), encoding="utf-8"
    )
    (soul_dir / "state.json").write_text(
        config.state.model_dump_json(indent=2), encoding="utf-8"
    )
    (soul_dir / "dna.md").write_text(
        dna_to_markdown(config.identity, config.dna), encoding="utf-8"
    )

    # Memory directory
    mem_dir = soul_dir / "memory"
    mem_dir.mkdir(exist_ok=True)

    (mem_dir / "core.json").write_text(
        json.dumps(memory_data.get("core", {}), indent=2, default=str),
        encoding="utf-8",
    )
    (mem_dir / "episodic.json").write_text(
        json.dumps(memory_data.get("episodic", []), indent=2, default=str),
        encoding="utf-8",
    )
    (mem_dir / "semantic.json").write_text(
        json.dumps(memory_data.get("semantic", []), indent=2, default=str),
        encoding="utf-8",
    )
    (mem_dir / "procedural.json").write_text(
        json.dumps(memory_data.get("procedural", []), indent=2, default=str),
        encoding="utf-8",
    )
    (mem_dir / "graph.json").write_text(
        json.dumps(memory_data.get("graph", {}), indent=2, default=str),
        encoding="utf-8",
    )


async def load_soul_full(path: Path) -> tuple[SoulConfig | None, dict]:
    """Load soul config + full memory data from disk.

    Reads ``soul.json`` from the given directory and, if a ``memory/``
    subdirectory exists, loads each tier's JSON file into a dict keyed
    by tier name.

    Args:
        path: Directory containing ``soul.json`` and optionally ``memory/``.

    Returns:
        A tuple of (SoulConfig or None, memory_data dict).
        If ``soul.json`` does not exist, returns (None, {}).
    """
    soul_json = path / "soul.json"
    if not soul_json.exists():
        return None, {}

    config = SoulConfig.model_validate_json(soul_json.read_text(encoding="utf-8"))

    memory_data: dict = {}
    mem_dir = path / "memory"
    if mem_dir.exists():
        for name in ["core", "episodic", "semantic", "procedural", "graph"]:
            f = mem_dir / f"{name}.json"
            if f.exists():
                memory_data[name] = json.loads(f.read_text(encoding="utf-8"))

    return config, memory_data

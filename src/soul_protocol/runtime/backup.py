# backup.py — Side-by-side backup helper for destructive soul mutations.
# Created: feat/0.3.2-backup-safety-net — Writes <path>.bak before destructive
#   writes in cleanup/forget/etc., so a single "soul cleanup --auto" can't
#   silently wipe memory with no undo. Fixes #148.

from __future__ import annotations

import shutil
from pathlib import Path


def backup_soul_file(path: str | Path) -> Path | None:
    """Copy a .soul file to `<path>.bak` before a destructive overwrite.

    Returns the backup path on success, or None if no backup was made
    (source missing, or source is a directory — unpacked form relies on
    filesystem-level history like git until the in-zip snapshot feature
    from #148 lands).

    Any existing `.soul.bak` is overwritten — we keep exactly one
    generation, which is enough to recover from "I ran cleanup by
    accident." Multi-generation history is tracked in #148 as future
    work.
    """
    src = Path(path)
    if not src.exists() or src.is_dir():
        return None
    bak = src.with_suffix(src.suffix + ".bak")
    shutil.copy2(src, bak)
    return bak

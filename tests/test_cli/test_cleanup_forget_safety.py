# test_cleanup_forget_safety.py — Safety-net tests for cleanup and forget CLI commands.
# Created: feat/0.3.2-backup-safety-net (#148) — Locks the new dry-run-by-default
#   behavior, the --apply flag requirement, and the .soul.bak side-by-side backup
#   that protects against accidental memory deletion.

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from soul_protocol.cli.main import cli
from soul_protocol.runtime.backup import backup_soul_file

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _birth_soul_at(path: str, name: str = "Safety") -> None:
    runner = CliRunner()
    runner.invoke(cli, ["birth", name, "-o", path])


def _remember_twice(soul_path: str, text: str) -> None:
    """Add the same memory twice so dedup has something to remove."""
    runner = CliRunner()
    runner.invoke(cli, ["remember", soul_path, text, "-i", "6"])
    runner.invoke(cli, ["remember", soul_path, text, "-i", "6"])


# ---------------------------------------------------------------------------
# backup helper
# ---------------------------------------------------------------------------


class TestBackupHelper:
    """Tests for runtime.backup.backup_soul_file()."""

    def test_backup_creates_bak_file_next_to_source(self, tmp_path):
        src = tmp_path / "echo.soul"
        src.write_bytes(b"zipfile-contents")

        bak = backup_soul_file(src)

        assert bak is not None
        assert bak == tmp_path / "echo.soul.bak"
        assert bak.exists()
        assert bak.read_bytes() == b"zipfile-contents"

    def test_backup_overwrites_existing_bak(self, tmp_path):
        src = tmp_path / "echo.soul"
        bak = tmp_path / "echo.soul.bak"
        src.write_bytes(b"new-contents")
        bak.write_bytes(b"old-contents")

        result = backup_soul_file(src)

        assert result == bak
        assert bak.read_bytes() == b"new-contents"

    def test_backup_returns_none_when_source_missing(self, tmp_path):
        result = backup_soul_file(tmp_path / "does-not-exist.soul")
        assert result is None

    def test_backup_returns_none_for_directories(self, tmp_path):
        unpacked = tmp_path / "unpacked-soul"
        unpacked.mkdir()

        result = backup_soul_file(unpacked)

        assert result is None


# ---------------------------------------------------------------------------
# soul cleanup — dry-run default and --apply requirement
# ---------------------------------------------------------------------------


class TestCleanupDryRunDefault:
    """Without --apply, cleanup is a preview and leaves the soul untouched."""

    def test_cleanup_without_apply_does_not_modify_file(self, tmp_path):
        soul_path = str(tmp_path / "preview.soul")
        _birth_soul_at(soul_path, "Preview")
        _remember_twice(soul_path, "recurring fact about testing")

        mtime_before = Path(soul_path).stat().st_mtime
        runner = CliRunner()
        result = runner.invoke(cli, ["cleanup", soul_path])
        mtime_after = Path(soul_path).stat().st_mtime

        assert result.exit_code == 0, result.output
        assert mtime_before == mtime_after, "cleanup without --apply must not write"

    def test_cleanup_without_apply_tells_user_to_pass_apply(self, tmp_path):
        soul_path = str(tmp_path / "hint.soul")
        _birth_soul_at(soul_path, "Hint")
        _remember_twice(soul_path, "another recurring fact")

        runner = CliRunner()
        result = runner.invoke(cli, ["cleanup", soul_path])

        assert result.exit_code == 0, result.output
        assert "--apply" in result.output or "Preview" in result.output

    def test_cleanup_auto_without_apply_still_does_nothing(self, tmp_path):
        """--auto alone must NOT trigger destructive execution — this is the
        exact footgun that motivated #148."""
        soul_path = str(tmp_path / "auto-only.soul")
        _birth_soul_at(soul_path, "AutoOnly")
        _remember_twice(soul_path, "don't lose me")

        mtime_before = Path(soul_path).stat().st_mtime
        runner = CliRunner()
        result = runner.invoke(cli, ["cleanup", "--auto", soul_path])
        mtime_after = Path(soul_path).stat().st_mtime

        assert result.exit_code == 0, result.output
        assert mtime_before == mtime_after


# ---------------------------------------------------------------------------
# soul cleanup --apply — writes .soul.bak before saving
# ---------------------------------------------------------------------------


class TestCleanupBackup:
    def test_apply_creates_bak_file_when_changes_occur(self, tmp_path):
        soul_path = tmp_path / "backup-me.soul"
        _birth_soul_at(str(soul_path), "Backup")
        _remember_twice(str(soul_path), "duplicate memory worth backing up")

        runner = CliRunner()
        result = runner.invoke(cli, ["cleanup", "--apply", "--auto", str(soul_path)])

        assert result.exit_code == 0, result.output
        bak = soul_path.with_suffix(".soul.bak")
        assert bak.exists(), f"expected {bak} to exist after --apply"

    def test_bak_contains_pre_cleanup_contents(self, tmp_path):
        soul_path = tmp_path / "pre-state.soul"
        _birth_soul_at(str(soul_path), "PreState")
        _remember_twice(str(soul_path), "about to be deduped")

        pre_bytes = soul_path.read_bytes()

        runner = CliRunner()
        runner.invoke(cli, ["cleanup", "--apply", "--auto", str(soul_path)])

        bak = soul_path.with_suffix(".soul.bak")
        assert bak.exists()
        assert bak.read_bytes() == pre_bytes, "backup must hold the pre-cleanup zip"


# ---------------------------------------------------------------------------
# soul forget — dry-run default
# ---------------------------------------------------------------------------


class TestForgetDryRunDefault:
    def test_forget_without_apply_does_not_modify_file(self, tmp_path):
        soul_path = tmp_path / "forget-preview.soul"
        _birth_soul_at(str(soul_path), "Forgetter")
        runner = CliRunner()
        runner.invoke(cli, ["remember", str(soul_path), "sensitive credit card info", "-i", "7"])

        mtime_before = soul_path.stat().st_mtime
        result = runner.invoke(cli, ["forget", str(soul_path), "credit card"])
        mtime_after = soul_path.stat().st_mtime

        assert result.exit_code == 0, result.output
        assert mtime_before == mtime_after

    def test_forget_without_apply_mentions_preview(self, tmp_path):
        soul_path = tmp_path / "forget-hint.soul"
        _birth_soul_at(str(soul_path), "ForgetHint")
        runner = CliRunner()
        runner.invoke(cli, ["remember", str(soul_path), "something to forget", "-i", "7"])

        result = runner.invoke(cli, ["forget", str(soul_path), "forget"])

        assert result.exit_code == 0, result.output
        assert "Preview" in result.output or "--apply" in result.output


class TestForgetBackup:
    def test_forget_apply_writes_bak(self, tmp_path):
        soul_path = tmp_path / "forget-backup.soul"
        _birth_soul_at(str(soul_path), "ForgetBackup")
        runner = CliRunner()
        runner.invoke(cli, ["remember", str(soul_path), "will be forgotten", "-i", "7"])

        pre_bytes = soul_path.read_bytes()

        result = runner.invoke(
            cli,
            ["forget", str(soul_path), "forgotten", "--apply", "--confirm"],
        )

        assert result.exit_code == 0, result.output
        bak = soul_path.with_suffix(".soul.bak")
        assert bak.exists()
        assert bak.read_bytes() == pre_bytes

# cli/setup.py — Universal agent platform integration for soul-protocol
# Created: 2026-03-13 — Auto-detect and configure coding agents + AI platforms.
#
# Supports: Claude Code, Cursor, VS Code/Copilot, Windsurf, Cline, Continue,
#           Gemini CLI, Codex CLI, Amazon Q, Zed, Claude Desktop.
# Universal: AGENTS.md (read by 5+ platforms).

from __future__ import annotations

import json
import platform
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

console = Console()


# ── Soul instructions (injected into AGENTS.md and platform-specific files) ──

_SOUL_INSTRUCTIONS = """\

## Soul (Persistent Memory)

This project uses [Soul Protocol](https://github.com/qbtrix/soul-protocol) \
for persistent AI memory via MCP.

**On session start:**
1. Call `soul_recall` with the current task context to load relevant memories
2. Call `soul_state` to check current mood and energy

**During work:**
- `soul_observe` after key decisions, completed tasks, or important conversations
- `soul_remember` for facts that should persist across sessions

**On session end:**
- The soul auto-saves on shutdown — no manual save needed
"""

_SOUL_MARKER = "## Soul (Persistent Memory)"


# ── Platform definitions ──


@dataclass
class Platform:
    """A coding agent or AI platform that can integrate with soul-protocol."""

    name: str
    slug: str
    mcp_config_paths: list[Path] = field(default_factory=list)
    mcp_key: str = "mcpServers"
    instruction_files: list[Path] = field(default_factory=list)
    detect_paths: list[Path] = field(default_factory=list)
    config_format: str = "json"  # json or toml
    scope: str = "project"  # project or global

    def is_installed(self) -> bool:
        """Check if this platform is likely installed/in use."""
        # Check explicit detection paths (dirs or files that prove the platform exists)
        for p in self.detect_paths:
            if p.exists():
                return True
        # Check if any config file already exists
        for p in self.mcp_config_paths:
            if p.exists():
                return True
        # Check if any instruction file already exists
        for p in self.instruction_files:
            if p.exists():
                return True
        return False


def _home() -> Path:
    return Path.home()


def _macos_app_support() -> Path:
    return _home() / "Library" / "Application Support"


def get_platforms(cwd: Path) -> list[Platform]:
    """Return all known platforms with their config locations."""
    home = _home()
    app_support = _macos_app_support()
    is_mac = platform.system() == "Darwin"

    platforms = [
        Platform(
            name="Claude Code",
            slug="claude-code",
            mcp_config_paths=[cwd / ".mcp.json"],
            instruction_files=[cwd / ".claude" / "CLAUDE.md"],
            detect_paths=[cwd / ".claude"],
        ),
        Platform(
            name="Cursor",
            slug="cursor",
            mcp_config_paths=[cwd / ".cursor" / "mcp.json"],
            instruction_files=[cwd / ".cursor" / "rules" / "soul.mdc"],
            detect_paths=[cwd / ".cursor"],
        ),
        Platform(
            name="VS Code / Copilot",
            slug="vscode",
            mcp_config_paths=[cwd / ".vscode" / "mcp.json"],
            mcp_key="servers",
            instruction_files=[cwd / ".github" / "copilot-instructions.md"],
            detect_paths=[cwd / ".vscode"],
        ),
        Platform(
            name="Windsurf",
            slug="windsurf",
            mcp_config_paths=[home / ".codeium" / "windsurf" / "mcp_config.json"],
            instruction_files=[cwd / ".windsurfrules"],
            detect_paths=[home / ".codeium" / "windsurf"],
            scope="global",
        ),
        Platform(
            name="Cline",
            slug="cline",
            instruction_files=[cwd / ".clinerules" / "soul.md"],
            detect_paths=[cwd / ".clinerules"],
        ),
        Platform(
            name="Continue",
            slug="continue",
            mcp_config_paths=[home / ".continue" / "mcpServers" / "soul.json"],
            instruction_files=[cwd / ".continuerules"],
            detect_paths=[home / ".continue"],
            scope="global",
        ),
        Platform(
            name="Gemini CLI",
            slug="gemini",
            mcp_config_paths=[cwd / ".gemini" / "settings.json"],
            instruction_files=[cwd / "GEMINI.md"],
            detect_paths=[cwd / ".gemini"],
        ),
        Platform(
            name="Codex CLI",
            slug="codex",
            mcp_config_paths=[cwd / ".codex" / "config.toml"],
            config_format="toml",
            detect_paths=[cwd / ".codex"],
        ),
        Platform(
            name="Amazon Q",
            slug="amazon-q",
            mcp_config_paths=[cwd / ".amazonq" / "mcp.json"],
            detect_paths=[cwd / ".amazonq"],
        ),
        Platform(
            name="Zed",
            slug="zed",
            mcp_key="context_servers",
        ),
    ]

    if is_mac:
        platforms.append(
            Platform(
                name="Claude Desktop",
                slug="claude-desktop",
                mcp_config_paths=[
                    app_support / "Claude" / "claude_desktop_config.json"
                ],
                detect_paths=[app_support / "Claude"],
                scope="global",
            ),
        )

    return platforms


def detect_platforms(cwd: Path) -> list[Platform]:
    """Auto-detect which platforms are installed/configured."""
    detected = []
    for p in get_platforms(cwd):
        if p.is_installed():
            detected.append(p)
    return detected


# ── MCP config writers ──


def _mcp_server_entry(soul_path: Path) -> dict:
    """Standard MCP server config for soul-protocol."""
    return {
        "command": "uvx",
        "args": ["--from", "soul-protocol[mcp]", "soul-mcp"],
        "env": {"SOUL_PATH": str(soul_path.resolve())},
    }


def _mcp_server_entry_vscode(soul_path: Path) -> dict:
    """VS Code MCP server config (slightly different schema)."""
    return {
        "type": "stdio",
        "command": "uvx",
        "args": ["--from", "soul-protocol[mcp]", "soul-mcp"],
        "env": {"SOUL_PATH": str(soul_path.resolve())},
    }


def _write_mcp_json(config_path: Path, soul_path: Path, platform: Platform) -> bool:
    """Write MCP config for a JSON-based platform. Returns True if written."""
    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    key = platform.mcp_key
    config.setdefault(key, {})

    if platform.slug == "vscode":
        entry = _mcp_server_entry_vscode(soul_path)
    else:
        entry = _mcp_server_entry(soul_path)

    # For Continue, the file IS the server config (drop-in format)
    if platform.slug == "continue":
        config = {"mcpServers": {"soul": entry}}
    else:
        config[key]["soul"] = entry

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return True


def _write_mcp_toml(config_path: Path, soul_path: Path) -> bool:
    """Write MCP config for Codex CLI (TOML format). Returns True if written."""
    toml_section = (
        f'\n[mcp_servers.soul]\n'
        f'command = "uvx"\n'
        f'args = ["--from", "soul-protocol[mcp]", "soul-mcp"]\n'
        f'\n[mcp_servers.soul.env]\n'
        f'SOUL_PATH = "{soul_path.resolve()}"\n'
    )

    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        content = config_path.read_text()
        if "[mcp_servers.soul]" in content:
            return False  # already configured
        config_path.write_text(content.rstrip() + "\n" + toml_section)
    else:
        config_path.write_text(toml_section)
    return True


# ── Instruction file writers ──


def _append_instructions(file_path: Path, header: str | None = None) -> bool:
    """Append soul instructions to an instruction file. Returns True if written."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        content = file_path.read_text()
        if _SOUL_MARKER in content:
            return False  # already has soul instructions
        file_path.write_text(content.rstrip() + "\n" + _SOUL_INSTRUCTIONS)
    else:
        preamble = f"# {header}\n" if header else ""
        file_path.write_text(preamble + _SOUL_INSTRUCTIONS)
    return True


# ── Gitignore ──


def _update_gitignore(cwd: Path) -> bool:
    """Add .soul/ to .gitignore if not already there."""
    gitignore = cwd / ".gitignore"
    pattern = ".soul/"

    if gitignore.exists():
        content = gitignore.read_text()
        if pattern in content:
            return False
        gitignore.write_text(
            content.rstrip() + f"\n\n# Soul state (local)\n{pattern}\n"
        )
    else:
        gitignore.write_text(f"# Soul state (local)\n{pattern}\n")
    return True


# ── Main setup orchestrator ──


def setup_integrations(
    soul_path: Path,
    soul_name: str,
    cwd: Path,
    platforms: list[str] | None = None,
) -> list[str]:
    """Configure soul-protocol for detected or specified platforms.

    Args:
        soul_path: Path to the .soul directory.
        soul_name: Name of the soul (for headers).
        cwd: Current working directory.
        platforms: Explicit platform slugs, or None for auto-detect.

    Returns:
        List of status messages for display.
    """
    messages: list[str] = []

    # Determine which platforms to configure
    all_platforms = {p.slug: p for p in get_platforms(cwd)}

    if platforms:
        targets = [all_platforms[s] for s in platforms if s in all_platforms]
        if not targets:
            messages.append("[yellow]No recognized platforms specified.[/yellow]")
            return messages
    else:
        targets = detect_platforms(cwd)

    # Always include AGENTS.md (universal)
    agents_md = cwd / "AGENTS.md"
    if _append_instructions(agents_md, header=soul_name):
        messages.append(
            "  [green]✓[/green] Created [bold]AGENTS.md[/bold] "
            "(universal — Codex, Copilot, Claude, Cursor, Cline)"
        )
    else:
        messages.append(
            "  [dim]⊘[/dim] [bold]AGENTS.md[/bold] already has soul instructions"
        )

    # Write MCP configs for each target platform
    for plat in targets:
        for config_path in plat.mcp_config_paths:
            if plat.config_format == "toml":
                written = _write_mcp_toml(config_path, soul_path)
            else:
                written = _write_mcp_json(config_path, soul_path, plat)

            if written:
                rel = _rel_path(config_path, cwd)
                messages.append(
                    f"  [green]✓[/green] Configured [bold]{rel}[/bold] ({plat.name})"
                )
            else:
                rel = _rel_path(config_path, cwd)
                messages.append(
                    f"  [dim]⊘[/dim] [bold]{rel}[/bold] already configured ({plat.name})"
                )

        # Write platform-specific instruction files
        for inst_path in plat.instruction_files:
            if inst_path == agents_md:
                continue  # already handled
            if _append_instructions(inst_path, header=soul_name):
                rel = _rel_path(inst_path, cwd)
                messages.append(
                    f"  [green]✓[/green] Created [bold]{rel}[/bold] ({plat.name})"
                )

    # Gitignore
    if _update_gitignore(cwd):
        messages.append("  [green]✓[/green] Added .soul/ to [bold].gitignore[/bold]")
    else:
        messages.append(
            "  [dim]⊘[/dim] [bold].gitignore[/bold] already excludes .soul/"
        )

    if not targets:
        messages.append(
            "\n  [dim]No agent platforms detected. "
            "Use --setup claude-code,cursor,... to specify explicitly.[/dim]"
        )

    return messages


def _rel_path(path: Path, cwd: Path) -> str:
    """Return a human-friendly relative path, or ~ path for home-relative."""
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        try:
            return "~/" + str(path.relative_to(Path.home()))
        except ValueError:
            return str(path)

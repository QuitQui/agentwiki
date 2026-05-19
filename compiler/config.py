"""Load agentwiki.toml config, walking up from cwd."""
from __future__ import annotations

import tomllib
from pathlib import Path


def load_config(cwd: Path | None = None) -> dict:
    """Walk up from *cwd* looking for agentwiki.toml; return parsed dict or {}."""
    if cwd is None:
        cwd = Path.cwd()
    current = cwd.resolve()
    for directory in [current, *current.parents]:
        candidate = directory / "agentwiki.toml"
        if candidate.exists():
            with candidate.open("rb") as f:
                return tomllib.load(f)
    return {}


def scan_dirs_from_config(config: dict) -> list[Path]:
    """Extract and resolve the scan dirs from a loaded config dict."""
    raw = config.get("discovery", {}).get("scan", [])
    return [Path(p) for p in raw]

"""Tests for compiler/config.py — TOML config loader."""
from __future__ import annotations

from pathlib import Path

import pytest

from compiler.config import load_config, scan_dirs_from_config


def test_load_config_missing(tmp_path):
    result = load_config(cwd=tmp_path)
    assert result == {}


def test_load_config_scan_dirs(tmp_path):
    toml = tmp_path / "agentwiki.toml"
    toml.write_text('[discovery]\nscan = ["/tmp/a", "/tmp/b"]\n')
    result = load_config(cwd=tmp_path)
    assert result["discovery"]["scan"] == ["/tmp/a", "/tmp/b"]


def test_scan_dirs_from_config_empty():
    assert scan_dirs_from_config({}) == []


def test_scan_dirs_from_config_paths(tmp_path):
    config = {"discovery": {"scan": [str(tmp_path)]}}
    dirs = scan_dirs_from_config(config)
    assert len(dirs) == 1
    assert dirs[0] == Path(tmp_path)


def test_load_config_walks_up(tmp_path):
    (tmp_path / "agentwiki.toml").write_text('[discovery]\nscan = ["/x"]\n')
    subdir = tmp_path / "sub" / "deep"
    subdir.mkdir(parents=True)
    result = load_config(cwd=subdir)
    assert result["discovery"]["scan"] == ["/x"]

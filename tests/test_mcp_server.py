"""Tests for compiler/mcp_server.py — Phase 6b MCP server."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from compiler.mcp_server import (
    TOOLS,
    _make_text,
    _read_index,
    _read_node,
    _search_index,
    build_server,
    set_dist_dir,
)


@pytest.fixture()
def dist_dir(tmp_path: Path) -> Path:
    nodes_dir = tmp_path / "nodes"
    nodes_dir.mkdir()

    index = [
        {
            "id": "doc:hello",
            "type": "Document",
            "title": "Hello World",
            "source_path": "docs/hello.md",
            "created_at": None,
            "sections": 1,
            "entities": 0,
            "outgoing_links": 0,
            "backlinks": 0,
        }
    ]
    (tmp_path / "index.json").write_text(json.dumps(index))

    node = {
        "id": "doc:hello",
        "type": "Document",
        "title": "Hello World",
        "source_path": "docs/hello.md",
        "sections": [],
        "entities": [],
        "outgoing_links": [],
        "backlinks": [],
    }
    (nodes_dir / "doc__hello.json").write_text(json.dumps(node))

    set_dist_dir(tmp_path)
    return tmp_path


def test_tools_registered() -> None:
    """build_server should expose all 5 expected tools."""
    tool_names = {t.name for t in TOOLS}
    assert tool_names == {"list_nodes", "get_node", "search_nodes", "get_neighbors", "get_stats"}


def test_read_index(dist_dir: Path) -> None:
    index = _read_index()
    assert len(index) == 1
    assert index[0]["id"] == "doc:hello"


def test_read_node_found(dist_dir: Path) -> None:
    node = _read_node("doc:hello")
    assert node is not None
    assert node["title"] == "Hello World"


def test_read_node_missing(dist_dir: Path) -> None:
    assert _read_node("doc:does-not-exist") is None


def test_search_index(dist_dir: Path) -> None:
    results = _search_index("hello", top_k=5)
    assert len(results) == 1
    assert results[0]["id"] == "doc:hello"


def test_make_text_produces_text_content() -> None:
    result = _make_text({"key": "value"})
    assert len(result) == 1
    assert result[0].type == "text"
    parsed = json.loads(result[0].text)
    assert parsed["key"] == "value"

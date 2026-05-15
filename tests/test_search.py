"""Tests for compiler/search.py (Phase 3)."""
import json
from pathlib import Path

import pytest

from compiler.search import build_search_index


def _make_node(nid: str, title: str, text: str = "") -> dict:
    return {
        "id": nid,
        "type": "Document",
        "title": title,
        "source_path": f"samples/{nid}.md",
        "content_text": text,
        "sections": [],
        "entities": [],
        "outgoing_links": [],
        "backlinks": [],
    }


@pytest.fixture()
def tmp_out(tmp_path: Path) -> Path:
    return tmp_path / "dist"


def test_build_search_index_creates_outputs(tmp_out: Path) -> None:
    nodes = [
        _make_node("doc:a", "Alpha", "machine learning embeddings"),
        _make_node("doc:b", "Beta", "deep learning neural networks"),
    ]
    build_search_index(nodes, tmp_out)

    assert (tmp_out / "similar.json").exists()
    assert (tmp_out / "lance").exists()


def test_similar_json_structure(tmp_out: Path) -> None:
    nodes = [
        _make_node("doc:a", "Alpha", "machine learning"),
        _make_node("doc:b", "Beta", "deep learning"),
        _make_node("doc:c", "Gamma", "knowledge graph"),
    ]
    build_search_index(nodes, tmp_out)

    similar = json.loads((tmp_out / "similar.json").read_text())
    assert set(similar.keys()) == {"doc:a", "doc:b", "doc:c"}

    for entries in similar.values():
        for e in entries:
            assert "id" in e
            assert "title" in e
            assert "score" in e
            assert 0.0 <= e["score"] <= 1.0


def test_similar_excludes_self(tmp_out: Path) -> None:
    nodes = [_make_node(f"doc:{i}", f"Node {i}", f"text {i}") for i in range(4)]
    build_search_index(nodes, tmp_out)

    similar = json.loads((tmp_out / "similar.json").read_text())
    for nid, entries in similar.items():
        assert all(e["id"] != nid for e in entries)


def test_build_search_index_skips_single_node(tmp_out: Path) -> None:
    """With fewer than 2 nodes nothing should be written."""
    build_search_index([_make_node("doc:a", "Only")], tmp_out)
    assert not (tmp_out / "similar.json").exists()


def test_top_k_capped(tmp_out: Path) -> None:
    nodes = [_make_node(f"doc:{i}", f"Node {i}", f"content {i}") for i in range(10)]
    build_search_index(nodes, tmp_out)

    similar = json.loads((tmp_out / "similar.json").read_text())
    for entries in similar.values():
        assert len(entries) <= 5  # _TOP_K default

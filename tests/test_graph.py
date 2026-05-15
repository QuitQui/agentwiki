"""Tests for compiler/graph.py (Phase 4)."""
import json
from pathlib import Path

import pytest

from compiler.graph import build_graph


def _make_node(nid: str, title: str, links: list[dict] | None = None) -> dict:
    return {
        "id": nid,
        "type": "Document",
        "title": title,
        "source_path": f"samples/{nid}.md",
        "outgoing_links": links or [],
        "backlinks": [],
    }


@pytest.fixture()
def tmp_out(tmp_path: Path) -> Path:
    return tmp_path / "dist"


def test_build_graph_creates_outputs(tmp_out: Path) -> None:
    nodes = [
        _make_node("doc:a", "A"),
        _make_node("doc:b", "B"),
    ]
    build_graph(nodes, tmp_out)

    assert (tmp_out / "kuzu").exists()
    assert (tmp_out / "neighbors.json").exists()
    assert (tmp_out / "graph_stats.json").exists()


def test_neighbors_structure(tmp_out: Path) -> None:
    nodes = [
        _make_node("doc:a", "A", [{"source_id": "doc:a", "target_id": "doc:b", "edge_type": "links_to"}]),
        _make_node("doc:b", "B"),
        _make_node("doc:c", "C", [{"source_id": "doc:c", "target_id": "doc:b", "edge_type": "links_to"}]),
    ]
    build_graph(nodes, tmp_out)

    neighbors = json.loads((tmp_out / "neighbors.json").read_text())
    assert set(neighbors.keys()) == {"doc:a", "doc:b", "doc:c"}

    # a→b direct (1-hop)
    a_neighbors = {n["id"]: n for n in neighbors["doc:a"]}
    assert "doc:b" in a_neighbors
    assert a_neighbors["doc:b"]["hops"] == 1

    # b has no outgoing links
    assert neighbors["doc:b"] == []


def test_two_hop_neighbor(tmp_out: Path) -> None:
    nodes = [
        _make_node("doc:a", "A", [{"source_id": "doc:a", "target_id": "doc:b", "edge_type": "links_to"}]),
        _make_node("doc:b", "B", [{"source_id": "doc:b", "target_id": "doc:c", "edge_type": "links_to"}]),
        _make_node("doc:c", "C"),
    ]
    build_graph(nodes, tmp_out)

    neighbors = json.loads((tmp_out / "neighbors.json").read_text())
    a_map = {n["id"]: n for n in neighbors["doc:a"]}

    assert a_map["doc:b"]["hops"] == 1
    assert a_map["doc:c"]["hops"] == 2


def test_graph_stats_counts(tmp_out: Path) -> None:
    nodes = [
        _make_node("doc:a", "A", [{"source_id": "doc:a", "target_id": "doc:b", "edge_type": "links_to"}]),
        _make_node("doc:b", "B"),
    ]
    build_graph(nodes, tmp_out)

    stats = json.loads((tmp_out / "graph_stats.json").read_text())
    assert stats["node_count"] == 2
    assert stats["edge_count"] == 1
    assert len(stats["top_by_degree"]) > 0


def test_build_graph_skips_external_targets(tmp_out: Path) -> None:
    """Links to nodes not in the compiled set must not raise errors."""
    nodes = [
        _make_node("doc:a", "A", [{"source_id": "doc:a", "target_id": "concept:external", "edge_type": "mentions"}]),
        _make_node("doc:b", "B"),
    ]
    build_graph(nodes, tmp_out)

    stats = json.loads((tmp_out / "graph_stats.json").read_text())
    assert stats["edge_count"] == 0  # external target filtered out


def test_build_graph_empty_nodes(tmp_out: Path) -> None:
    build_graph([], tmp_out)
    assert not (tmp_out / "kuzu").exists()
    assert not (tmp_out / "neighbors.json").exists()


def test_build_graph_idempotent(tmp_out: Path) -> None:
    """Running twice should not crash (kuzu dir is rebuilt cleanly)."""
    nodes = [_make_node("doc:a", "A"), _make_node("doc:b", "B")]
    build_graph(nodes, tmp_out)
    build_graph(nodes, tmp_out)

    stats = json.loads((tmp_out / "graph_stats.json").read_text())
    assert stats["node_count"] == 2

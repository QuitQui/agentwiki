"""Tests for compiler/api.py — Phase 6a REST API."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from compiler.api import app, set_dist_dir


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
        },
        {
            "id": "doc:other",
            "type": "Document",
            "title": "Other Doc",
            "source_path": "docs/other.md",
            "created_at": None,
            "sections": 0,
            "entities": 0,
            "outgoing_links": 0,
            "backlinks": 0,
        },
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

    stats = {"node_count": 2, "edge_count": 0, "top_nodes": []}
    (tmp_path / "graph_stats.json").write_text(json.dumps(stats))

    set_dist_dir(tmp_path)
    return tmp_path


@pytest.fixture()
def client(dist_dir: Path) -> TestClient:
    return TestClient(app)


def test_list_nodes(client: TestClient) -> None:
    resp = client.get("/nodes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["id"] == "doc:hello"


def test_get_node_known_id(client: TestClient) -> None:
    resp = client.get("/nodes/doc:hello")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Hello World"


def test_get_node_unknown_id(client: TestClient) -> None:
    resp = client.get("/nodes/doc:does-not-exist")
    assert resp.status_code == 404


def test_search_returns_top_k(client: TestClient) -> None:
    resp = client.get("/search?q=hello&top_k=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "doc:hello"


def test_get_stats_structure(client: TestClient) -> None:
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "node_count" in data
    assert data["node_count"] == 2

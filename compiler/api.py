"""Phase 6a REST API — serves compiled dist/ over HTTP."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

_DEFAULT_DIST = Path(__file__).parent.parent / "dist"

app = FastAPI(title="AgentWiki API", version="0.1.0")

# ---------------------------------------------------------------------------
# Dist-dir override (set at startup via compiler/cli.py)
# ---------------------------------------------------------------------------
_dist_dir: Path = _DEFAULT_DIST


def set_dist_dir(p: Path) -> None:
    global _dist_dir
    _dist_dir = p
    _get_index.cache_clear()
    _get_neighbors.cache_clear()
    _get_similar.cache_clear()
    _get_graph_stats.cache_clear()


# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_index() -> list[dict]:
    p = _dist_dir / "index.json"
    if not p.exists():
        return []
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _get_neighbors() -> dict[str, list[dict]]:
    p = _dist_dir / "neighbors.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _get_similar() -> dict[str, list[dict]]:
    p = _dist_dir / "similar.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


@lru_cache(maxsize=1)
def _get_graph_stats() -> dict[str, Any]:
    p = _dist_dir / "graph_stats.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _id_to_filename(node_id: str) -> str:
    return node_id.replace(":", "__").replace("/", "-") + ".json"


def _load_node(node_id: str) -> dict | None:
    path = _dist_dir / "nodes" / _id_to_filename(node_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/nodes")
def list_nodes() -> list[dict]:
    """Return the node index (summaries, not full nodes)."""
    return _get_index()


@app.get("/nodes/{node_id:path}")
def get_node(node_id: str) -> dict:
    """Return a full KnowledgeNode by ID."""
    node = _load_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return node


@app.get("/search")
def search(
    q: str = Query(..., description="Query string"),
    top_k: int = Query(5, ge=1, le=50),
) -> list[dict]:
    """Full-text search over node titles using the pre-built similar.json index."""
    q_lower = q.lower()
    index = _get_index()
    results = [n for n in index if q_lower in n.get("title", "").lower() or q_lower in n.get("type", "").lower()]
    return results[:top_k]


@app.get("/neighbors/{node_id:path}")
def get_neighbors(node_id: str) -> list[dict]:
    """Return 1- and 2-hop graph neighbors for a node."""
    neighbors = _get_neighbors()
    return neighbors.get(node_id, [])


@app.get("/stats")
def get_stats() -> dict:
    """Return graph statistics (node count, edge count, top nodes by degree)."""
    index = _get_index()
    stats = _get_graph_stats()
    return {
        "node_count": len(index),
        "graph": stats,
    }

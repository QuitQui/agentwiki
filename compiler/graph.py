"""Phase 4: Kuzu knowledge graph — build DB, export neighbors + stats."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import kuzu

if TYPE_CHECKING:
    from compiler.models import KnowledgeNode

_TOP_N = 10  # top-N nodes by degree in graph_stats.json


def build_graph(nodes: list[KnowledgeNode], output_dir: Path) -> None:
    """Populate a Kuzu graph DB and export neighbors.json + graph_stats.json."""
    if not nodes:
        return

    kuzu_dir = output_dir / "kuzu"
    output_dir.mkdir(parents=True, exist_ok=True)
    if kuzu_dir.exists():
        shutil.rmtree(kuzu_dir) if kuzu_dir.is_dir() else kuzu_dir.unlink()
    db = kuzu.Database(str(kuzu_dir))
    conn = kuzu.Connection(db)

    # Schema
    conn.execute(
        "CREATE NODE TABLE Node(id STRING, type STRING, title STRING, PRIMARY KEY(id))"
    )
    conn.execute("CREATE REL TABLE Edge(FROM Node TO Node, edge_type STRING)")

    # Insert nodes
    for n in nodes:
        conn.execute(
            "CREATE (:Node {id: $id, type: $type, title: $title})",
            {"id": n["id"], "type": n["type"], "title": n["title"]},
        )

    # Insert edges (outgoing_links only — backlinks are derived)
    seen: set[tuple[str, str, str]] = set()
    node_ids = {n["id"] for n in nodes}
    for n in nodes:
        for e in n.get("outgoing_links", []):
            key = (e["source_id"], e["target_id"], e["edge_type"])
            if key in seen or e["target_id"] not in node_ids:
                continue
            seen.add(key)
            conn.execute(
                """
                MATCH (a:Node {id: $src}), (b:Node {id: $tgt})
                CREATE (a)-[:Edge {edge_type: $et}]->(b)
                """,
                {"src": e["source_id"], "tgt": e["target_id"], "et": e["edge_type"]},
            )

    _export_neighbors(conn, nodes, output_dir)
    _export_stats(conn, nodes, output_dir)


def _export_neighbors(
    conn: kuzu.Connection, nodes: list[KnowledgeNode], output_dir: Path
) -> None:
    """Write dist/neighbors.json: per-node 1- and 2-hop reachable nodes."""
    neighbors: dict[str, list[dict]] = {}

    for n in nodes:
        nid = n["id"]
        seen: dict[str, dict] = {}

        r1 = conn.execute(
            "MATCH (src:Node {id: $id})-[:Edge]->(dst:Node) RETURN dst.id, dst.type, dst.title",
            {"id": nid},
        )
        while r1.has_next():
            row = r1.get_next()
            if row[0] != nid:
                seen[row[0]] = {"id": row[0], "type": row[1], "title": row[2], "hops": 1}

        r2 = conn.execute(
            """
            MATCH (src:Node {id: $id})-[:Edge]->(:Node)-[:Edge]->(dst:Node)
            RETURN DISTINCT dst.id, dst.type, dst.title
            """,
            {"id": nid},
        )
        while r2.has_next():
            row = r2.get_next()
            if row[0] != nid and row[0] not in seen:
                seen[row[0]] = {"id": row[0], "type": row[1], "title": row[2], "hops": 2}

        neighbors[nid] = sorted(seen.values(), key=lambda x: (x["hops"], x["id"]))

    (output_dir / "neighbors.json").write_text(
        json.dumps(neighbors, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _export_stats(
    conn: kuzu.Connection, nodes: list[KnowledgeNode], output_dir: Path
) -> None:
    """Write dist/graph_stats.json: counts + top nodes by total degree."""
    node_count = len(nodes)

    ec = conn.execute("MATCH ()-[:Edge]->() RETURN count(*)")
    edge_count = ec.get_next()[0] if ec.has_next() else 0

    # Build degree map in Python from node data (avoids complex Kuzu aggregation)
    title_map = {n["id"]: n["title"] for n in nodes}
    degree: dict[str, dict] = {
        n["id"]: {"id": n["id"], "title": title_map[n["id"]], "out_degree": 0, "in_degree": 0}
        for n in nodes
    }
    out_r = conn.execute("MATCH (a:Node)-[:Edge]->(b:Node) RETURN a.id, b.id")
    while out_r.has_next():
        src, tgt = out_r.get_next()
        if src in degree:
            degree[src]["out_degree"] += 1
        if tgt in degree:
            degree[tgt]["in_degree"] += 1

    top = sorted(degree.values(), key=lambda d: d["out_degree"] + d["in_degree"], reverse=True)[:_TOP_N]

    stats = {"node_count": node_count, "edge_count": edge_count, "top_by_degree": top}
    (output_dir / "graph_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

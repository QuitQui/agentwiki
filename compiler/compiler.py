"""Core compilation pipeline: discovers inputs, parses them, resolves backlinks, emits dist/."""
from __future__ import annotations

import json
from pathlib import Path

from compiler.models import KnowledgeNode, Edge
from compiler.parser.html_report import parse_report_dir
from compiler.parser.markdown_doc import parse_markdown
from compiler.search import build_search_index
from compiler.graph import build_graph


def _safe_id_to_filename(node_id: str) -> str:
    """Convert a node id like 'report:foo-bar' to a safe filename 'report__foo-bar.json'."""
    return node_id.replace(":", "__") + ".json"


def compile_inputs(input_dir: Path) -> list[KnowledgeNode]:
    """Discover and parse all inputs under input_dir. Returns raw nodes (no backlinks yet)."""
    nodes: list[KnowledgeNode] = []

    reports_dir = input_dir / "reports"
    if reports_dir.exists():
        for d in sorted(reports_dir.iterdir()):
            if d.is_dir() and (d / "report.html").exists():
                nodes.append(parse_report_dir(d))

    docs_dir = input_dir / "docs"
    if docs_dir.exists():
        for f in sorted(docs_dir.glob("*.md")):
            nodes.append(parse_markdown(f))

    return nodes


def resolve_backlinks(nodes: list[KnowledgeNode]) -> list[KnowledgeNode]:
    """Scan all outgoing_links and inject backlink edges into target nodes."""
    index: dict[str, KnowledgeNode] = {n["id"]: n for n in nodes}

    for node in nodes:
        for edge in node.get("outgoing_links", []):
            target_id = edge["target_id"]
            if target_id in index:
                backlink = Edge(
                    source_id=target_id,
                    target_id=node["id"],
                    edge_type=edge["edge_type"],
                )
                target = index[target_id]
                if "backlinks" not in target:
                    target["backlinks"] = []
                if backlink not in target["backlinks"]:
                    target["backlinks"].append(backlink)

    return list(index.values())


def emit(nodes: list[KnowledgeNode], output_dir: Path) -> None:
    """Write per-node JSON files and an index to output_dir."""
    nodes_dir = output_dir / "nodes"
    nodes_dir.mkdir(parents=True, exist_ok=True)

    for node in nodes:
        filename = _safe_id_to_filename(node["id"])
        (nodes_dir / filename).write_text(
            json.dumps(node, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    index = [
        {
            "id": n["id"],
            "type": n["type"],
            "title": n["title"],
            "source_path": n["source_path"],
            "created_at": n.get("created_at"),
            "sections": len(n.get("sections", [])),
            "entities": len(n.get("entities", [])),
            "outgoing_links": len(n.get("outgoing_links", [])),
            "backlinks": len(n.get("backlinks", [])),
        }
        for n in nodes
    ]
    (output_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def run(
    input_dir: Path,
    output_dir: Path,
    embed: bool = True,
    graph: bool = True,
) -> list[KnowledgeNode]:
    """Full pipeline: parse → backlinks → emit → search index → graph. Returns the final node list."""
    nodes = compile_inputs(input_dir)
    nodes = resolve_backlinks(nodes)
    emit(nodes, output_dir)
    if embed:
        build_search_index(nodes, output_dir)
    if graph:
        build_graph(nodes, output_dir)
    return nodes

"""Core compilation pipeline: discovers inputs, parses them, resolves backlinks, emits dist/."""
from __future__ import annotations

import json
from pathlib import Path

from compiler.models import KnowledgeNode, Edge
from compiler.parser.html_report import parse_report_dir
from compiler.parser.markdown_doc import parse_markdown
from compiler.parser.code_file import parse_code_file
from compiler.search import build_search_index
from compiler.graph import build_graph


def _safe_id_to_filename(node_id: str) -> str:
    """Convert a node id to a safe flat filename (no path separators)."""
    return node_id.replace(":", "__").replace("/", "-") + ".json"


def _collect_report_dirs(reports_dir: Path) -> list[Path]:
    """Return sorted list of subdirs inside reports_dir that contain a report.html."""
    if not reports_dir.exists():
        return []
    return sorted(d for d in reports_dir.iterdir() if d.is_dir() and (d / "report.html").exists())


def _extra_reports_dirs(scan_dirs: list[Path]) -> list[Path]:
    """For each scan path, yield its reports/ subdir and also depth-1 children's reports/ subdirs."""
    seen: set[Path] = set()
    result: list[Path] = []
    for scan in scan_dirs:
        candidates = [scan / "reports"] + [child / "reports" for child in sorted(scan.iterdir()) if child.is_dir()]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen and candidate.exists():
                seen.add(resolved)
                result.append(candidate)
    return result


_SKIP_DIRS = frozenset({".venv", "venv", "__pycache__", ".git", "node_modules", ".tox", "build", "dist"})


def _collect_code_files(scan_dirs: list[Path]) -> list[tuple[Path, Path]]:
    """Return (py_file, base_scan_dir) pairs, deduplicated by resolved path."""
    seen: set[Path] = set()
    result: list[tuple[Path, Path]] = []
    for scan in scan_dirs:
        if not scan.exists():
            continue
        for py_file in sorted(scan.rglob("*.py")):
            if any(part in _SKIP_DIRS for part in py_file.parts):
                continue
            resolved = py_file.resolve()
            if resolved not in seen:
                seen.add(resolved)
                result.append((py_file, scan))
    return result


def _link_code_to_reports(nodes: list[KnowledgeNode]) -> None:
    """Add related_to edges from CodeFile nodes to AgentReport nodes sharing file entities."""
    report_nodes = [n for n in nodes if n.get("type") == "AgentReport"]
    code_nodes = [n for n in nodes if n.get("type") == "CodeFile"]
    for code_node in code_nodes:
        code_paths = {e.get("path", "") for e in code_node.get("entities", []) if e.get("type") == "file"}
        for report in report_nodes:
            report_paths = {e.get("path", "") for e in report.get("entities", []) if e.get("type") == "file"}
            matched = any(
                cp and rp and (cp.endswith(rp) or rp.endswith(cp))
                for cp in code_paths for rp in report_paths
            )
            if matched:
                edge = Edge(source_id=code_node["id"], target_id=report["id"], edge_type="related_to")
                links = code_node.setdefault("outgoing_links", [])
                if edge not in links:
                    links.append(edge)


def compile_inputs(input_dir: Path, scan_dirs: list[Path] | None = None, code: bool = False) -> list[KnowledgeNode]:
    """Discover and parse all inputs under input_dir. Returns raw nodes (no backlinks yet)."""
    nodes: list[KnowledgeNode] = []
    seen_report_dirs: set[Path] = set()

    primary_reports = input_dir / "reports"
    seen_report_dirs.add(primary_reports.resolve())
    for d in _collect_report_dirs(primary_reports):
        nodes.append(parse_report_dir(d))

    for extra_reports in _extra_reports_dirs(scan_dirs or []):
        if extra_reports.resolve() in seen_report_dirs:
            continue
        seen_report_dirs.add(extra_reports.resolve())
        for d in _collect_report_dirs(extra_reports):
            nodes.append(parse_report_dir(d))

    docs_dir = input_dir / "docs"
    if docs_dir.exists():
        for f in sorted(docs_dir.glob("*.md")):
            nodes.append(parse_markdown(f))

    if code and scan_dirs:
        for py_file, base in _collect_code_files(scan_dirs):
            nodes.extend(parse_code_file(py_file, base))
        _link_code_to_reports(nodes)

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
    scan_dirs: list[Path] | None = None,
    code: bool = False,
) -> list[KnowledgeNode]:
    """Full pipeline: parse → backlinks → emit → search index → graph. Returns the final node list."""
    nodes = compile_inputs(input_dir, scan_dirs=scan_dirs, code=code)
    nodes = resolve_backlinks(nodes)
    emit(nodes, output_dir)
    if embed:
        build_search_index(nodes, output_dir)
    if graph:
        build_graph(nodes, output_dir)
    return nodes

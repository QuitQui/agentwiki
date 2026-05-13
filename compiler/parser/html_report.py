"""Parse a report.html + manifest.json pair into a KnowledgeNode.

Phase 0 stub — discovery and validation only, no full extraction yet.
"""
from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup

from compiler.models import KnowledgeNode, Section, Entity, Edge


def parse_report_dir(report_dir: Path) -> KnowledgeNode:
    """Read report.html + manifest.json from a report directory and return a KnowledgeNode stub."""
    html_file = report_dir / "report.html"
    manifest_file = report_dir / "manifest.json"

    if not html_file.exists():
        raise FileNotFoundError(f"Missing report.html in {report_dir}")
    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing manifest.json in {report_dir}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "lxml")

    article = soup.find("article")
    sections: list[Section] = []
    if article:
        for sec in article.find_all("section"):
            sec_type = sec.get("data-section-type", "")
            heading = sec.find(["h1", "h2", "h3", "h4"])
            sections.append(
                Section(
                    id=f"{manifest['id']}#{sec_type}",
                    type=sec_type,
                    title=heading.get_text(strip=True) if heading else sec_type,
                    content_html=str(sec),
                    content_text=sec.get_text(separator=" ", strip=True),
                )
            )

    entities: list[Entity] = [
        Entity(type=e["type"], name=e["name"], **({"path": e["path"]} if "path" in e else {}))
        for e in manifest.get("entities", [])
    ]

    outgoing_links: list[Edge] = [
        Edge(source_id=manifest["id"], target_id=lnk["target"], edge_type=lnk["type"])
        for lnk in manifest.get("links", [])
    ]

    return KnowledgeNode(
        id=manifest["id"],
        type=manifest.get("type", "AgentReport"),
        title=manifest["title"],
        source_path=str(manifest_file),
        html_path=str(html_file),
        sections=sections,
        entities=entities,
        outgoing_links=outgoing_links,
        backlinks=[],
        git_commit=manifest.get("source", {}).get("git_commit"),
        created_at=manifest.get("created_at"),
    )

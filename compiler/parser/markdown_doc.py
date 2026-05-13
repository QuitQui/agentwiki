"""Parse a Markdown doc into a KnowledgeNode with H2-level sections."""
from __future__ import annotations

import re
from pathlib import Path

from compiler.models import KnowledgeNode, Section


def _split_sections(text: str, doc_id: str) -> list[Section]:
    """Split markdown at H2 headings into sections."""
    pattern = re.compile(r'^##\s+(.+)', re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    sections: list[Section] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        title = m.group(1).strip()
        sec_type = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        sections.append(
            Section(
                id=f"{doc_id}#{sec_type}",
                type=sec_type,
                title=title,
                content_text=body,
            )
        )
    return sections


def parse_markdown(md_file: Path) -> KnowledgeNode:
    text = md_file.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else md_file.stem.replace("-", " ").title()

    node_id = f"doc:{md_file.stem}"
    sections = _split_sections(text, node_id)

    return KnowledgeNode(
        id=node_id,
        type="Document",
        title=title,
        source_path=str(md_file),
        content_text=text,
        sections=sections,
        entities=[],
        outgoing_links=[],
        backlinks=[],
    )

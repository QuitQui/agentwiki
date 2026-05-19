"""Parse a Python source file into CodeFile + Function/Class KnowledgeNodes."""
from __future__ import annotations

from pathlib import Path

import tree_sitter_python as tsp
from tree_sitter import Language, Parser

from compiler.models import Entity, KnowledgeNode

_LANGUAGE = Language(tsp.language())
_PARSER = Parser(_LANGUAGE)


def _get_name(node) -> str | None:
    for child in node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8")
    return None


def parse_code_file(path: Path, base_path: Path | None = None) -> list[KnowledgeNode]:
    """Return one CodeFile node + N Function/Class nodes for a Python source file."""
    if base_path is None:
        base_path = path.parent

    try:
        rel = path.relative_to(base_path)
    except ValueError:
        rel = path

    rel_str = str(rel).replace("\\", "/")
    file_id = f"codefile:{rel_str}"

    source = path.read_bytes()
    tree = _PARSER.parse(source)
    root = tree.root_node

    symbols: list[KnowledgeNode] = []
    entities: list[Entity] = [Entity(type="file", path=rel_str)]

    for node in root.children:
        if node.type == "function_definition":
            name = _get_name(node)
            if name:
                sym_id = f"codesymbol:{rel_str}:{name}"
                symbols.append(KnowledgeNode(
                    id=sym_id,
                    type="Function",
                    title=f"{name}()",
                    source_path=str(path),
                    content_text=node.text.decode("utf-8", errors="replace"),
                    sections=[],
                    entities=[Entity(type="function", name=name, path=rel_str)],
                    outgoing_links=[],
                    backlinks=[],
                ))
                entities.append(Entity(type="function", name=name))
        elif node.type == "class_definition":
            name = _get_name(node)
            if name:
                sym_id = f"codesymbol:{rel_str}:{name}"
                symbols.append(KnowledgeNode(
                    id=sym_id,
                    type="Class",
                    title=name,
                    source_path=str(path),
                    content_text=node.text.decode("utf-8", errors="replace"),
                    sections=[],
                    entities=[Entity(type="class", name=name, path=rel_str)],
                    outgoing_links=[],
                    backlinks=[],
                ))
                entities.append(Entity(type="class", name=name))

    title = path.stem.replace("_", " ").title()
    file_node = KnowledgeNode(
        id=file_id,
        type="CodeFile",
        title=title,
        source_path=str(path),
        content_text=source.decode("utf-8", errors="replace"),
        sections=[],
        entities=entities,
        outgoing_links=[],
        backlinks=[],
    )

    return [file_node, *symbols]

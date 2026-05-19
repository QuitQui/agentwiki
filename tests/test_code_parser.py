"""Tests for compiler/parser/code_file.py — tree-sitter Python parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from compiler.parser.code_file import parse_code_file


@pytest.fixture
def py_file(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text(
        "def foo():\n    pass\n\ndef bar(x, y):\n    return x + y\n\nclass Baz:\n    pass\n"
    )
    return f, tmp_path


def test_parse_python_functions(py_file):
    path, base = py_file
    nodes = parse_code_file(path, base)
    func_titles = [n["title"] for n in nodes if n["type"] == "Function"]
    assert "foo()" in func_titles
    assert "bar()" in func_titles


def test_parse_python_classes(py_file):
    path, base = py_file
    nodes = parse_code_file(path, base)
    class_titles = [n["title"] for n in nodes if n["type"] == "Class"]
    assert "Baz" in class_titles


def test_code_file_node_id(py_file):
    path, base = py_file
    nodes = parse_code_file(path, base)
    file_node = next(n for n in nodes if n["type"] == "CodeFile")
    assert file_node["id"] == "codefile:sample.py"


def test_code_file_node_count(py_file):
    path, base = py_file
    nodes = parse_code_file(path, base)
    assert len(nodes) == 4  # 1 CodeFile + 2 Functions + 1 Class


def test_symbol_node_ids(py_file):
    path, base = py_file
    nodes = parse_code_file(path, base)
    ids = {n["id"] for n in nodes}
    assert "codesymbol:sample.py:foo" in ids
    assert "codesymbol:sample.py:bar" in ids
    assert "codesymbol:sample.py:Baz" in ids


def test_file_node_entities_include_functions(py_file):
    path, base = py_file
    nodes = parse_code_file(path, base)
    file_node = next(n for n in nodes if n["type"] == "CodeFile")
    entity_names = [e.get("name") for e in file_node["entities"]]
    assert "foo" in entity_names
    assert "bar" in entity_names
    assert "Baz" in entity_names


def test_parse_empty_file(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    nodes = parse_code_file(f, tmp_path)
    assert len(nodes) == 1
    assert nodes[0]["type"] == "CodeFile"


def test_parse_no_base_path(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text("def hello(): pass\n")
    nodes = parse_code_file(f)
    assert any(n["type"] == "Function" for n in nodes)

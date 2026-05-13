from __future__ import annotations
from typing import Literal, Optional
from typing_extensions import TypedDict

NodeType = Literal[
    "Document",
    "AgentReport",
    "AgentRun",
    "CodeFile",
    "Function",
    "Class",
    "Experiment",
    "Dataset",
    "Metric",
    "Decision",
    "Issue",
    "PullRequest",
    "Concept",
    "Citation",
    "Asset",
]

EdgeType = Literal[
    "links_to",
    "backlinks_to",
    "mentions",
    "implements",
    "modifies",
    "generated_by",
    "depends_on",
    "imports",
    "evaluates",
    "cites",
    "supersedes",
    "contradicts",
    "related_to",
]


class Entity(TypedDict, total=False):
    type: str
    name: str
    path: str  # optional, for code entities


class Edge(TypedDict):
    source_id: str
    target_id: str
    edge_type: EdgeType


class Section(TypedDict, total=False):
    id: str
    type: str          # e.g. "summary", "changes", "evidence"
    title: str
    content_html: str
    content_text: str


class KnowledgeNode(TypedDict, total=False):
    id: str            # required — unique stable identifier
    type: NodeType     # required
    title: str         # required
    source_path: str   # required — path to the source file
    content_text: str
    content_html: str
    html_path: str
    sections: list[Section]
    entities: list[Entity]
    outgoing_links: list[Edge]
    backlinks: list[Edge]
    embeddings: list[float]
    related_nodes: list[str]
    git_commit: str
    created_at: str
    updated_at: str

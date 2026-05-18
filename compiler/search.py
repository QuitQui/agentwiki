"""Phase 3 search: TF-IDF similarity + LanceDB vector storage + similar.json export."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import lancedb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if TYPE_CHECKING:
    from compiler.models import KnowledgeNode

_TOP_K = 5


def _node_text(node: KnowledgeNode) -> str:
    """Flatten a node to a single searchable string."""
    parts = [node.get("title", ""), node.get("type", "")]
    for sec in node.get("sections", []):
        if sec.get("content_text"):
            parts.append(sec["content_text"])
    if node.get("content_text"):
        parts.append(node["content_text"])
    for e in node.get("entities", []):
        parts.append(e.get("name", ""))
    return " ".join(filter(None, parts))


def build_search_index(nodes: list[KnowledgeNode], output_dir: Path) -> None:
    """Compute TF-IDF vectors, store in LanceDB, write dist/similar.json."""
    if len(nodes) < 2:
        return

    ids = [n["id"] for n in nodes]
    titles = {n["id"]: n["title"] for n in nodes}
    corpus = [_node_text(n) for n in nodes]

    # --- TF-IDF vectors ---
    vectorizer = TfidfVectorizer(
        min_df=1, ngram_range=(1, 2), sublinear_tf=True, max_features=4096
    )
    tfidf_sparse = vectorizer.fit_transform(corpus)
    sim_matrix = cosine_similarity(tfidf_sparse)

    # --- LanceDB storage ---
    lance_dir = output_dir / "lance"
    lance_dir.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(lance_dir))

    records = [
        {"id": nid, "title": titles[nid], "vector": tfidf_sparse[i].toarray().astype(np.float32)[0].tolist()}
        for i, nid in enumerate(ids)
    ]
    existing = db.list_tables()
    table_names = existing.tables if hasattr(existing, "tables") else list(existing)
    if "nodes" in table_names:
        db.drop_table("nodes")
    db.create_table("nodes", data=records)

    # --- pre-compute top-k similar per node → dist/similar.json ---
    similar: dict[str, list[dict]] = {}
    for i, nid in enumerate(ids):
        row = sim_matrix[i]
        ranked = np.argsort(row)[::-1]
        top = []
        for j in ranked:
            if j == i:
                continue
            top.append({"id": ids[j], "title": titles[ids[j]], "score": round(float(row[j]), 4)})
            if len(top) >= _TOP_K:
                break
        similar[nid] = top

    (output_dir / "similar.json").write_text(
        json.dumps(similar, indent=2, ensure_ascii=False), encoding="utf-8"
    )

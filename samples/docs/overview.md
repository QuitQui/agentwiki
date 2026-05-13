# AgentWiki Overview

AgentWiki is a **project memory compiler** for AI-assisted software development.

AI agents generate work continuously — code changes, reports, decisions, experiment results — but that output scatters across chat logs, files, and PRs. AgentWiki solves this by compiling all agent outputs and project docs into a single, searchable, graph-connected website that both humans and agents can query.

## What it is

- A **compiler**, not an editor. You feed it inputs; it produces a website and indices.
- An **HTML-first system**. Agent reports are rich HTML artifacts, not plain text logs.
- A **dual-interface layer**. The website is for humans; the graph + API is for agents.

## What it is not

- Not a Notion or Obsidian clone (no editing in-app).
- Not just a documentation site (it models knowledge as a graph, not just pages).
- Not just a RAG system (it also renders a human-readable website).

## Core workflow

1. An agent completes a task and emits a `report.html` + `manifest.json`.
2. AgentWiki ingests the report, extracts entities and sections, and builds graph edges.
3. The compiled website shows the report with backlinks, related code, and graph neighbors.
4. A human searches "why was hybrid search changed?" and gets report sections + prior decisions.
5. A future agent queries the same memory before making its next change.

## Key concepts

- **KnowledgeNode** — any compiled artifact (report, doc, code file, concept, decision).
- **Edge** — a typed relationship between two nodes (e.g. `modifies`, `mentions`, `cites`).
- **Manifest** — the machine-readable metadata file (`manifest.json`) that accompanies each HTML report.
- **Chunk** — a section-level excerpt stored in the search index for retrieval.

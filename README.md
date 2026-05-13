# AgentWiki

An HTML-first project memory compiler for human–AI collaboration.

AgentWiki ingests AI agent reports, Markdown docs, and source code, then compiles them into a static website with backlinks, knowledge graph navigation, hybrid search, and an API for AI agents.

## Quick start

```bash
# Install dependencies
uv sync

# Run the compiler (Phase 0 — discovery + validation)
uv run agentwiki compile --input-dir samples/ --output-dir dist/
```

## Project layout

```
compiler/       Python compiler package
schema/         JSON Schemas for manifest and knowledge node formats
samples/        Synthetic sample inputs (reports + docs)
site/           Astro frontend (Phase 2+)
```

## Development

```bash
uv run pytest          # run tests
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Roadmap

| Phase | Deliverable |
|---|---|
| 0 | Repo skeleton, schemas, sample inputs ✓ |
| 1 | HTML report compiler → KnowledgeNode |
| 2 | Static Astro website |
| 3 | Keyword + semantic search |
| 4 | Knowledge graph (Kuzu) |
| 5 | Codebase integration (tree-sitter) |
| 6 | Agent API (REST → MCP) |

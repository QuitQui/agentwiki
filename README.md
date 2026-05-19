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

## Agent API (Phase 6)

### REST API

```bash
# Compile first, then serve
uv run agentwiki compile
uv run agentwiki serve          # http://127.0.0.1:8000
```

Endpoints: `GET /nodes`, `GET /nodes/{id}`, `GET /search?q=`, `GET /neighbors/{id}`, `GET /stats`

### MCP server (Claude Code / Claude Desktop)

```bash
uv run agentwiki mcp            # reads from dist/ over stdio
```

Add to `~/.claude.json` (Claude Code) or `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentwiki": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/agentwiki", "agentwiki", "mcp"],
      "env": {}
    }
  }
}
```

Available tools: `list_nodes`, `get_node`, `search_nodes`, `get_neighbors`, `get_stats`

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

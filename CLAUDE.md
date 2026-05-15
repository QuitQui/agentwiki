# AgentWiki — Project Rules

Inherits all rules from the workspace `../CLAUDE.md`.

## Stack (do not change without discussion)
- **Compiler**: Python, managed by `uv`
- **Frontend**: Astro 5 (static output), in `site/`
- **Graph DB**: Kuzu (Phase 4+)
- **Search**: Pagefind (keyword) + LanceDB (vector) (Phase 3+)

## Dev workflow
```bash
uv sync                          # install / update deps
uv run agentwiki compile         # compile samples/ → dist/
uv run agentwiki dev             # compile + start Astro at localhost:4321
```

## Project phases
| Phase | Status |
|---|---|
| 0 — Skeleton + schemas | ✅ done |
| 1 — Compiler pipeline | ✅ done |
| 2 — Astro website | ✅ done |
| 3 — Search (Pagefind + vector) | ⬜ (PR open) |
| 4 — Knowledge graph (Kuzu) | ✅ done |
| 5 — Codebase integration (tree-sitter) | ⬜ |
| 6 — Agent API (REST → MCP) | ⬜ |

## Output format
- `dist/index.json` — all nodes summarised
- `dist/nodes/<id>.json` — one compiled KnowledgeNode per input
- `dist/neighbors.json` — per-node 1- and 2-hop graph neighbors (Phase 4)
- `dist/graph_stats.json` — node/edge counts + top nodes by degree (Phase 4)
- `dist/kuzu/` — embedded Kuzu graph DB (Phase 4)
- Node IDs use `:` as separator (`report:foo`); filenames use `__` (`report__foo.json`)

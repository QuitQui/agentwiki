# Architecture

## Pipeline overview

```
Inputs
  ├── HTML agent reports  (report.html + manifest.json + chunks.jsonl)
  ├── Markdown / MDX docs
  ├── Source code         (Python, TypeScript — via tree-sitter)
  └── Git metadata        (commits, branches, PRs)

Compiler  (Python)
  ├── Parse HTML reports  → extract sections, entities, links
  ├── Parse Markdown docs → extract headings, wikilinks
  ├── Parse code symbols  → functions, classes, imports
  ├── Validate manifests  → JSON Schema
  ├── Build backlinks     → cross-reference all nodes
  ├── Chunk content       → section-level excerpts
  ├── Generate embeddings → vector index
  ├── Build knowledge graph → Kuzu (graph DB)
  └── Emit outputs

Outputs
  ├── Static HTML website  (Astro)
  ├── Pagefind keyword index
  ├── Vector index         (LanceDB)
  ├── Graph database       (Kuzu)
  └── REST + MCP agent API
```

## Stack decisions

| Layer | Choice | Reason |
|---|---|---|
| Compiler | Python | Strong ML/embedding ecosystem, Kuzu Python SDK |
| Website | Astro + Starlight | Static, fast, flexible MDX + HTML support |
| Keyword search | Pagefind | Indexes static HTML, no backend needed |
| Semantic search | LanceDB | Embedded, local-first, good for prototyping |
| Graph store | Kuzu | Embedded graph DB, no server to run |
| Code parsing | tree-sitter | Reliable, language-agnostic AST extraction |
| Graph viz | Sigma.js | Lightweight, canvas-based, handles large graphs |
| Agent API | REST → MCP | REST is easy to debug; MCP added after model stabilizes |

## Report format

Each agent report is a directory:

```
reports/
  2026-05-13-retrieval-refactor/
    report.html      ← rich human-facing artifact
    manifest.json    ← machine-readable metadata (validated by JSON Schema)
    chunks.jsonl     ← one JSON line per section, for search indexing
    assets/          ← plots, screenshots, diagrams
```

The `<article>` element in `report.html` carries `data-*` attributes for compiler extraction:

```html
<article
  data-node-id="report:retrieval-refactor-001"
  data-node-type="agent_report"
  data-agent="coding-agent"
  data-commit="d4f8a2c"
>
```

## Knowledge graph schema

Nodes: `Document`, `AgentReport`, `CodeFile`, `Function`, `Class`, `Concept`, `Decision`, `Issue`, `PullRequest`, `Experiment`, `Dataset`, `Metric`, `Citation`, `Asset`, `AgentRun`

Edges: `links_to`, `mentions`, `modifies`, `depends_on`, `generated_by`, `implements`, `cites`, `supersedes`, `contradicts`, `related_to`, `imports`, `evaluates`, `backlinks_to`

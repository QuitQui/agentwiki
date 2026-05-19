# From Zero to AgentWiki: A Setup Guide

By the end of this guide you'll have a compiled knowledge graph, a static site with keyword and vector search, and a local development server you can browse.

**Prerequisites:** Python 3.12+, [`uv`](https://docs.astral.sh/uv/getting-started/installation/), Node 18+

---

## Step 1: Clone and Install

```bash
git clone https://github.com/JimChienTW/agentwiki
cd agentwiki
uv sync
```

`uv sync` installs the Python dependencies and registers the `agentwiki` CLI. The site dependencies are in `site/` — install those separately before building:

```bash
cd site && npm install && cd ..
```

---

## Step 2: Write Your First Report

AgentWiki compiles AI session reports. A report is a directory under `samples/reports/` containing three files:

**`manifest.json`** — structured metadata:
```json
{
  "id": "report:my-first-session",
  "type": "agent_report",
  "title": "My First Session",
  "created_at": "2026-01-15T10:00:00+00:00",
  "agent": { "name": "claude-code", "model": "claude-sonnet-4-6", "run_id": "my-first-session" },
  "source": { "git_commit": "abc1234", "branch": "main" },
  "entities": [
    { "type": "file", "path": "src/main.py", "name": "main" }
  ],
  "links": [
    { "type": "modifies", "target": "codefile:src/main.py" }
  ]
}
```

**`report.html`** — the session narrative in HTML. The compiler parses it for sections and text content.

**`chunks.jsonl`** — one JSON object per line, each a searchable content chunk from the session. Minimal required format:
```jsonl
{"id": "chunk-0", "text": "Implemented the main entry point."}
```

The `samples/` directory contains working examples. Use them as a reference.

---

## Step 3: Compile

```bash
uv run agentwiki compile --input-dir samples/ --output-dir dist/
```

This reads all reports and docs under `samples/`, builds the knowledge graph and vector index, and writes everything to `dist/`. You'll see a table of compiled nodes and a summary line confirming the output files.

Options:
- `--no-embed` — skip the LanceDB vector index (faster, no `dist/similar.json`)
- `--no-graph` — skip Kuzu graph build (no `dist/neighbors.json`)

---

## Step 4: Preview Locally

```bash
uv run agentwiki dev
```

This compiles (same as Step 3) then starts the Astro dev server at `http://localhost:4321`. The site hot-reloads on changes to the `site/` source.

You'll see:
- **Index page** — all compiled nodes as cards, with Pagefind search
- **Node detail pages** — sections, backlinks, similar nodes, graph neighborhood
- **Graph page** (`/graph`) — force-directed canvas of all nodes and edges

---

## Step 5: Production Build

```bash
uv run agentwiki build
```

This runs the full production pipeline:

1. Compiles inputs → `dist/`
2. Runs `npm run build` in `site/` → `site/dist/` (static HTML)
3. Runs Pagefind over the built HTML → search index embedded in `site/dist/`

The output in `site/dist/` is a fully static site ready to deploy anywhere — GitHub Pages, Netlify, an S3 bucket.

---

## Step 6: Add More Input

The `--input-dir` flag accepts any directory with the expected structure. To compile a different project, point it there:

```bash
uv run agentwiki compile --input-dir /path/to/other-project/reports/ --output-dir dist/
```

Docs go under `<input-dir>/docs/` as `.md` files. Reports go under `<input-dir>/reports/<session-name>/`.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'compiler'`**

Run:
```bash
uv pip install -e .
```

This installs the package in editable mode and makes the `agentwiki` CLI available in the current virtual environment.

**`npm: command not found` or Astro errors**

Make sure you ran `npm install` inside `site/` before running `build` or `dev`. Node 18+ is required.

**Pagefind not found warning**

The `build` command will warn if Pagefind isn't available. Fix: run `npm install` in `site/` first. Pagefind is listed as a dev dependency in `site/package.json`.

**Compilation succeeds but the site shows no nodes**

Check that your `manifest.json` files are valid against the schema. The compiler validates them before running and will exit with a schema error if they're malformed. Compare against the samples in `samples/reports/`.

---

That's the full setup. From here, add `/report` to the end of your CLAUDE.md session rules — every session then produces a new report directory ready to compile.

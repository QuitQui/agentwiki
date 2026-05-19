# Why AI Agents Are Amnesiac (And What to Do About It)

Every Claude Code session ends with context death.

You spend an afternoon building something. The agent reads files, makes decisions, explains tradeoffs, writes code. Then the session closes. You open a new one the next day and the agent has no idea what it did yesterday. You explain the problem again, re-establish context, remind it what you decided last week.

This isn't a bug. It's the design. Sessions are stateless by default. The model doesn't persist memory across conversations. What you lose is everything you built up during the session: the reasoning, the architectural decisions, the dead ends you explored so you wouldn't explore them again.

## The Artifact Is Already There

Here's the thing: AI agent sessions already produce output. They don't just produce code changes.

When you run `/report` at the end of a Claude Code session, you get three files:

- `report.html` — the full narrative: what was done, what was decided, why
- `manifest.json` — structured metadata: node ID, timestamp, entities touched, links to other nodes
- `chunks.jsonl` — the session content in searchable chunks

These files exist. They're just sitting in a directory, disconnected from everything else. They don't link to each other. They don't link to the docs you wrote six months ago. There's no way to ask "what did we decide about the search indexing approach?"

## What AgentWiki Does

AgentWiki compiles those scattered artifacts into a persistent, navigable knowledge graph.

Run one command after your sessions accumulate:

```bash
uv run agentwiki compile --input-dir samples/ --output-dir dist/
```

The compiler reads every `manifest.json` and `report.html` in the input directory, parses them into structured `KnowledgeNode` records, resolves the links between nodes, and writes:

- `dist/nodes/report__session-name.json` — one structured record per session
- `dist/index.json` — all nodes summarized
- `dist/neighbors.json` — the graph: which nodes each node connects to, 1-hop and 2-hop
- `dist/kuzu/` — an embedded Kuzu graph database backing the neighbor queries

Each node knows what it links to, and what links to it. A session report that modified `compiler/search.py` will have a backlink from any doc node that mentions that module. A later session that built on earlier work will show up as a neighbor.

## The Site Is the Interface

The compiled output powers a static Astro site. Run `uv run agentwiki dev` to compile and start it locally.

On each node's detail page, the graph neighborhood section shows every directly connected node — the sessions that came before, the docs that reference the same concepts, the code files that were touched in related work. This is a 1-hop view backed by `dist/neighbors.json`, which Kuzu computed during compilation.

The `/graph` page renders all nodes and their edges on a force-directed canvas. You can see the shape of your project's history: which sessions are densely connected, which nodes sit at the center of the graph, which are isolated.

Search is wired in at two levels. Pagefind handles keyword search across every page. LanceDB stores TF-IDF vectors and pre-computes `dist/similar.json` — so each node also surfaces the top-k semantically similar nodes, not just the explicitly linked ones.

## The Rule That Changes the Loop

None of this requires you to change how you work. It requires one addition:

Add `/report` to the end of your CLAUDE.md session instructions.

That's it. Each session produces a report. Each report gets compiled into the graph. The graph accumulates. Three months in, you have a searchable record of every decision, every dead end, every piece of reasoning your agents produced.

The next time you start a session and the agent asks "what did we decide about the search indexing approach?" — you don't have to answer from memory. You compile the graph, open the site, and search.

The agent is still stateless. The knowledge base isn't.

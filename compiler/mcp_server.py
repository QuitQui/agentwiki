"""Phase 6b MCP server — exposes AgentWiki dist/ as MCP tools."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

_DEFAULT_DIST = Path(__file__).parent.parent / "dist"
_dist_dir: Path = _DEFAULT_DIST


def set_dist_dir(p: Path) -> None:
    global _dist_dir
    _dist_dir = p


def _id_to_filename(node_id: str) -> str:
    return node_id.replace(":", "__").replace("/", "-") + ".json"


def _read_index() -> list[dict]:
    p = _dist_dir / "index.json"
    return json.loads(p.read_text()) if p.exists() else []


def _read_node(node_id: str) -> dict | None:
    path = _dist_dir / "nodes" / _id_to_filename(node_id)
    return json.loads(path.read_text()) if path.exists() else None


def _read_neighbors() -> dict[str, list[dict]]:
    p = _dist_dir / "neighbors.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _read_stats() -> dict[str, Any]:
    p = _dist_dir / "graph_stats.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _search_index(q: str, top_k: int = 5) -> list[dict]:
    q_lower = q.lower()
    index = _read_index()
    results = [n for n in index if q_lower in n.get("title", "").lower() or q_lower in n.get("type", "").lower()]
    return results[:top_k]


TOOLS: list[Tool] = [
    Tool(
        name="list_nodes",
        description="List all knowledge nodes (id, type, title) in the AgentWiki.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="get_node",
        description="Get the full content of a knowledge node by its ID.",
        inputSchema={
            "type": "object",
            "properties": {"node_id": {"type": "string", "description": "Node ID, e.g. report:my-report"}},
            "required": ["node_id"],
        },
    ),
    Tool(
        name="search_nodes",
        description="Search knowledge nodes by a text query against titles and types.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="get_neighbors",
        description="Get 1- and 2-hop graph neighbors for a node.",
        inputSchema={
            "type": "object",
            "properties": {"node_id": {"type": "string", "description": "Node ID"}},
            "required": ["node_id"],
        },
    ),
    Tool(
        name="get_stats",
        description="Get graph statistics: node count, edge count, top nodes by degree.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


def _make_text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]


def build_server() -> Server:
    server = Server("agentwiki")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "list_nodes":
            return _make_text(_read_index())
        if name == "get_node":
            node = _read_node(arguments["node_id"])
            if node is None:
                return _make_text({"error": f"Node not found: {arguments['node_id']}"})
            return _make_text(node)
        if name == "search_nodes":
            results = _search_index(arguments["query"], arguments.get("top_k", 5))
            return _make_text(results)
        if name == "get_neighbors":
            neighbors = _read_neighbors()
            return _make_text(neighbors.get(arguments["node_id"], []))
        if name == "get_stats":
            index = _read_index()
            stats = _read_stats()
            return _make_text({"node_count": len(index), "graph": stats})
        return _make_text({"error": f"Unknown tool: {name}"})

    return server


async def _run_stdio(dist: Path) -> None:
    set_dist_dir(dist)
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def serve_stdio(dist: Path) -> None:
    asyncio.run(_run_stdio(dist))

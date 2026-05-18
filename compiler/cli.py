from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import click
import jsonschema
from rich.console import Console
from rich.table import Table
from rich import box

from compiler import compiler as core

console = Console()

SCHEMA_DIR = Path(__file__).parent.parent / "schema"


def _load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text()) if path.exists() else {}


def _validate_manifests(input_dir: Path, schema: dict) -> list[str]:
    errors: list[str] = []
    reports_dir = input_dir / "reports"
    if not reports_dir.exists() or not schema:
        return errors
    for d in sorted(reports_dir.iterdir()):
        mf = d / "manifest.json"
        if mf.exists():
            try:
                jsonschema.validate(json.loads(mf.read_text()), schema)
            except jsonschema.ValidationError as exc:
                errors.append(f"{d.name}: {exc.message}")
    return errors


@click.group()
def main() -> None:
    """AgentWiki — project memory compiler."""


@main.command()
@click.option("--input-dir", "-i", default="samples", show_default=True)
@click.option("--output-dir", "-o", default="dist", show_default=True)
@click.option("--no-embed", is_flag=True, default=False, help="Skip vector index build.")
@click.option("--no-graph", is_flag=True, default=False, help="Skip Kuzu graph build.")
@click.option("--scan", "-s", multiple=True, help="Extra directories to scan for reports/ (may repeat).")
def compile(input_dir: str, output_dir: str, no_embed: bool, no_graph: bool, scan: tuple[str, ...]) -> None:
    """Compile inputs to dist/: per-node JSON + index.json + search index + graph."""
    root = Path(input_dir)
    out = Path(output_dir)
    scan_dirs = [Path(s) for s in scan]

    if not root.exists():
        console.print(f"[red]Input directory not found:[/red] {root}")
        raise SystemExit(1)

    console.rule("[bold cyan]AgentWiki compiler — Phase 4[/bold cyan]")

    if scan_dirs:
        console.print(f"[dim]Extra scan dirs:[/dim] {', '.join(str(s) for s in scan_dirs)}")

    # --- validate manifests before compiling ---
    manifest_schema = _load_schema("manifest.schema.json")
    errors = _validate_manifests(root, manifest_schema)
    if errors:
        for e in errors:
            console.print(f"[red]Schema error:[/red] {e}")
        raise SystemExit(1)

    # --- run the full pipeline ---
    nodes = core.run(root, out, embed=not no_embed, graph=not no_graph, scan_dirs=scan_dirs)

    # --- report ---
    table = Table(box=box.SIMPLE_HEAVY, show_lines=False)
    table.add_column("Node ID", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Title")
    table.add_column("Sections", justify="right")
    table.add_column("Links", justify="right")
    table.add_column("Backlinks", justify="right")

    for n in nodes:
        table.add_row(
            n["id"],
            n["type"],
            n["title"],
            str(len(n.get("sections", []))),
            str(len(n.get("outgoing_links", []))),
            str(len(n.get("backlinks", []))),
        )

    console.print(table)
    embed_note = "" if no_embed else f" + [cyan]{out}/similar.json[/cyan] + [cyan]{out}/lance/[/cyan]"
    graph_note = "" if no_graph else f" + [cyan]{out}/neighbors.json[/cyan] + [cyan]{out}/graph_stats.json[/cyan] + [cyan]{out}/kuzu/[/cyan]"
    console.print(
        f"\n[bold green]✓[/bold green] Compiled [bold]{len(nodes)}[/bold] node(s) → "
        f"[cyan]{out}/nodes/[/cyan] + [cyan]{out}/index.json[/cyan]{embed_note}{graph_note}"
    )


@main.command()
@click.option("--input-dir", "-i", default="samples", show_default=True)
@click.option("--output-dir", "-o", default="dist", show_default=True)
@click.option("--port", "-p", default=4321, show_default=True)
@click.option("--scan", "-s", multiple=True, help="Extra directories to scan for reports/ (may repeat).")
def dev(input_dir: str, output_dir: str, port: int, scan: tuple[str, ...]) -> None:
    """Compile inputs then start the Astro dev server."""
    repo_root = Path(__file__).parent.parent
    site_dir = repo_root / "site"

    if not site_dir.exists():
        console.print("[red]site/ directory not found. Run from the repo root.[/red]")
        raise SystemExit(1)

    # compile first
    ctx = click.get_current_context()
    ctx.invoke(compile, input_dir=input_dir, output_dir=output_dir, scan=scan)

    console.print(f"\n[bold cyan]Starting Astro dev server[/bold cyan] on port {port}…\n")
    subprocess.run(
        ["npm", "run", "dev", "--", "--port", str(port)],
        cwd=site_dir,
        check=True,
    )


@main.command(name="build")
@click.option("--input-dir", "-i", default="samples", show_default=True)
@click.option("--output-dir", "-o", default="dist", show_default=True)
@click.option("--scan", "-s", multiple=True, help="Extra directories to scan for reports/ (may repeat).")
def build_cmd(input_dir: str, output_dir: str, scan: tuple[str, ...]) -> None:
    """Compile + Astro build + Pagefind index → site/dist/ (production)."""
    repo_root = Path(__file__).parent.parent
    site_dir = repo_root / "site"

    if not site_dir.exists():
        console.print("[red]site/ directory not found.[/red]")
        raise SystemExit(1)

    # 1. compile
    ctx = click.get_current_context()
    ctx.invoke(compile, input_dir=input_dir, output_dir=output_dir, no_embed=False, scan=scan)

    # 2. astro build
    console.rule("[bold cyan]Astro build[/bold cyan]")
    subprocess.run(["npm", "run", "build"], cwd=site_dir, check=True)

    # 3. pagefind index
    console.rule("[bold cyan]Pagefind index[/bold cyan]")
    site_dist = site_dir / "dist"
    result = subprocess.run(
        ["npx", "pagefind", "--site", str(site_dist)],
        cwd=site_dir,
        check=False,
    )
    if result.returncode != 0:
        console.print("[yellow]⚠[/yellow] Pagefind not found — run [cyan]npm install[/cyan] in site/ first.")
    else:
        console.print(f"\n[bold green]✓[/bold green] Production build ready → [cyan]{site_dist}/[/cyan]")

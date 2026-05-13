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
def compile(input_dir: str, output_dir: str) -> None:
    """Compile inputs to dist/: per-node JSON + index.json."""
    root = Path(input_dir)
    out = Path(output_dir)

    if not root.exists():
        console.print(f"[red]Input directory not found:[/red] {root}")
        raise SystemExit(1)

    console.rule("[bold cyan]AgentWiki compiler — Phase 1[/bold cyan]")

    # --- validate manifests before compiling ---
    manifest_schema = _load_schema("manifest.schema.json")
    errors = _validate_manifests(root, manifest_schema)
    if errors:
        for e in errors:
            console.print(f"[red]Schema error:[/red] {e}")
        raise SystemExit(1)

    # --- run the full pipeline ---
    nodes = core.run(root, out)

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
    console.print(
        f"\n[bold green]✓[/bold green] Compiled [bold]{len(nodes)}[/bold] node(s) → "
        f"[cyan]{out}/nodes/[/cyan] + [cyan]{out}/index.json[/cyan]"
    )


@main.command()
@click.option("--input-dir", "-i", default="samples", show_default=True)
@click.option("--output-dir", "-o", default="dist", show_default=True)
@click.option("--port", "-p", default=4321, show_default=True)
def dev(input_dir: str, output_dir: str, port: int) -> None:
    """Compile inputs then start the Astro dev server."""
    repo_root = Path(__file__).parent.parent
    site_dir = repo_root / "site"

    if not site_dir.exists():
        console.print("[red]site/ directory not found. Run from the repo root.[/red]")
        raise SystemExit(1)

    # compile first
    ctx = click.get_current_context()
    ctx.invoke(compile, input_dir=input_dir, output_dir=output_dir)

    console.print(f"\n[bold cyan]Starting Astro dev server[/bold cyan] on port {port}…\n")
    subprocess.run(
        ["npm", "run", "dev", "--", "--port", str(port)],
        cwd=site_dir,
        check=True,
    )

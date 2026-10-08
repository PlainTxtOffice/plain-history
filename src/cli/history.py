"""Present saved snapshot history in the terminal."""

from pathlib import Path

import typer

from src.adapters import snapshots
from src.domains import tracking


def show(root: Path, file: Path | None) -> None:
    """List newest saves first, optionally containing one relative file path.

    - Read saved records without inspecting documents or tracking rules.
    - Match filenames using the platform's path case rules, without globbing.
    """
    name = tracking.normalize_pattern(str(file)) if file is not None else None
    saved = snapshots.load(root)
    if not saved:
        typer.echo("No snapshots saved yet. Use phist save to save a draft.")
        return
    selected = [
        snapshot
        for snapshot in reversed(saved)
        if name is None
        or any(Path(path) == Path(name) for path in snapshot.files)
    ]
    if not selected:
        typer.echo(f"No saved snapshots contain: {name}")
        return
    typer.echo(f"Saved history for: {name}" if name else "Saved history:")
    for index, snapshot in enumerate(selected):
        if index:
            typer.echo()
        typer.echo(f"Snapshot {snapshot.number}: {snapshot.message}")
        typer.echo(f"Saved at (UTC): {snapshot.created_at}")
        typer.echo(f"Version: {snapshot.version or 'none'}")
        typer.echo(f"Files saved: {len(snapshot.files)}")

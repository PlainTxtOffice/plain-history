"""Expose repository operations through the phist command."""

from pathlib import Path
from typing import Annotated

import typer

from src.adapters import repository, snapshots, tracking
from src.cli import documents
from src.cli import history as history_report
from src.cli import save as save_prompt
from src.cli.options import Root

app = typer.Typer(no_args_is_help=True, help="Version history for plain text.")


def _repository_path(root: Path, *, initialize: bool = False) -> Path:
    """Translate repository errors into concise CLI failures."""
    try:
        return repository.init(root) if initialize else repository.load(root)
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


def _show_tracking(root: Path, patterns: list[str]) -> None:
    """Print saved selection rules and the documents they currently match."""
    typer.echo("Tracking rules:")
    for pattern in patterns:
        typer.echo(f"  {pattern}")
    if not patterns:
        typer.echo('  None yet. Use phist track "*.md" to select documents.')
    files = tracking.list_files(root, patterns)
    typer.echo(f"Matching files: {len(files)}")
    for file in files:
        typer.echo(f"  {file}")


@app.command()
def init(path: Root = Path()) -> None:
    """Create .plain_history metadata in an existing folder."""
    metadata = _repository_path(path, initialize=True)
    typer.echo(f"Repository ready: {metadata}")


@app.command()
def check(path: Root = Path()) -> None:
    """Check history setup and report what is available for this folder.

    Read metadata without changing files; exit 1 if setup is missing or invalid.
    """
    metadata = _repository_path(path)
    typer.echo(f"History is set up for: {metadata.parent}")
    try:
        _show_tracking(metadata.parent, tracking.load(metadata.parent))
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


@app.command()
def track(
    patterns: Annotated[
        list[str], typer.Argument(help="Files or quoted globs.")
    ],
    path: Root = Path(),
) -> None:
    """Select files and glob patterns for future snapshots."""
    metadata = _repository_path(path)
    try:
        rules = tracking.add(metadata.parent, patterns)
        _show_tracking(metadata.parent, rules)
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    typer.echo("Selection saved. No snapshot created.")


@app.command()
def save(
    message: Annotated[str | None, typer.Argument()] = None,
    path: Root = Path(),
) -> None:
    """Save tracked documents after prompting for a message and version."""
    metadata = _repository_path(path)
    try:
        saved = snapshots.load(metadata.parent)
        snapshots.list_selection(metadata.parent)
        current = saved[-1].version if saved else None
        message, version = save_prompt.read_details(message, current)
        snapshot = snapshots.save(metadata.parent, message, version, len(saved))
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Saved snapshot {snapshot.number}: {snapshot.message}")
    typer.echo(f"Files saved: {len(snapshot.files)}")
    typer.echo(f"Version: {snapshot.version or 'none'}")


@app.command()
def last(path: Root = Path()) -> None:
    """Show the latest saved snapshot and its recorded files."""
    metadata = _repository_path(path)
    try:
        saved = snapshots.load(metadata.parent)
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    if not saved:
        typer.echo("No snapshots saved yet. Use phist save to save a draft.")
        return
    snapshot = saved[-1]
    typer.echo(f"Last saved snapshot {snapshot.number}: {snapshot.message}")
    typer.echo(f"Saved at (UTC): {snapshot.created_at}")
    typer.echo(f"Version: {snapshot.version or 'none'}")
    typer.echo(f"Files saved: {len(snapshot.files)}")
    for file in sorted(snapshot.files):
        typer.echo(f"  {file}")


@app.command()
def history(
    file: Annotated[
        Path | None, typer.Argument(help="Optional relative document path.")
    ] = None,
    path: Root = Path(),
) -> None:
    """List saved snapshots, optionally containing a particular document."""
    metadata = _repository_path(path)
    try:
        history_report.show(metadata.parent, file)
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


app.command()(documents.diff)
app.command()(documents.restore)


def main() -> None:
    """Run the CLI with literal glob rules, including on Windows."""
    app(windows_expand_args=False)

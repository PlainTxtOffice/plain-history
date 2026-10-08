"""Compare and restore saved documents through the terminal."""

from pathlib import Path
from typing import Annotated

import typer

from src.adapters import repository, snapshot_documents
from src.cli import history as history_report
from src.cli.options import Root
from src.domains import diff as text_diff


def diff(
    file: Path,
    version: Annotated[
        int | None,
        typer.Option(min=1, help="Snapshot number; latest by default."),
    ] = None,
    path: Root = Path(),
) -> None:
    """Compare a saved UTF-8 document with its current contents."""
    try:
        root = repository.load(path).parent
        snapshot, name, before = snapshot_documents.load(root, file, version)
        current = snapshot_documents.read_current(root, name)
        after = current if current is not None else b""
        result = text_diff.format_diff(
            before.decode("utf-8"), after.decode("utf-8")
        )
    except UnicodeDecodeError as error:
        typer.echo("Diff supports UTF-8 text documents only.", err=True)
        raise typer.Exit(1) from error
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Comparing {name}: snapshot {snapshot.number} to current file")
    if current is None:
        typer.echo("Current file is missing.")
    if before == current:
        typer.echo("No changes.")
    elif result:
        typer.echo(result)
    else:
        typer.echo(
            "No text line changes; file bytes differ or the file is missing."
        )


def _choose_snapshot(root: Path, file: Path | None) -> int:
    """Show saved history and request a valid snapshot number."""
    latest = snapshot_documents.load_snapshot(root, None)
    history_report.show(root, file)
    while True:
        number = typer.prompt(
            "Snapshot number to restore", default=latest.number, type=int
        )
        try:
            if file is not None:
                snapshot_documents.load(root, file, number)
            else:
                snapshot_documents.load_snapshot(root, number)
        except (OSError, ValueError) as error:
            typer.echo(str(error), err=True)
        else:
            return number


def _show_plan(
    root: Path,
    snapshot_number: int,
    message: str,
    plan: snapshot_documents.RestorePlan,
    file: Path | None,
) -> None:
    """Show the destination and action for every file before confirmation."""
    if file is not None:
        name = next(iter(plan))
        typer.echo(f"Restore {name} from snapshot {snapshot_number}: {message}")
    else:
        typer.echo(f"Restore writing folder: {root}")
        typer.echo(f"Snapshot {snapshot_number}: {message}")
        typer.echo("Files outside this snapshot will be left alone.")
    for name, (content, current) in plan.items():
        action = (
            "Unchanged"
            if current == content
            else "Recreate"
            if current is None
            else "Replace"
        )
        typer.echo(f"  {action}: {name}")


def restore(
    file: Annotated[
        Path | None,
        typer.Argument(help="One file; omit for the whole snapshot."),
    ] = None,
    version: Annotated[
        int | None,
        typer.Option(min=1, help="Snapshot number; prompts if omitted."),
    ] = None,
    path: Root = Path(),
    *,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes", "-y", help="Skip confirmation; requires --version."
        ),
    ] = False,
) -> None:
    """Restore a file or whole snapshot after reviewing the selected save."""
    if yes and version is None:
        typer.echo(
            "Supply --version with --yes to choose a snapshot explicitly.",
            err=True,
        )
        raise typer.Exit(1)
    try:
        root = repository.load(path).parent
        version = _choose_snapshot(root, file) if version is None else version
        snapshot, plan = snapshot_documents.prepare_restore(root, file, version)
        _show_plan(root, snapshot.number, snapshot.message, plan, file)
        typer.echo(f"Version: {snapshot.version or 'none'}")
        if all(content == current for content, current in plan.values()):
            typer.echo("Already matches this snapshot. No changes.")
            return
        if file is None:
            question = "Restore these files?"
        else:
            current = next(iter(plan.values()))[1]
            question = (
                "Replace the current file?"
                if current is not None
                else "Recreate this file?"
            )
        if not yes and not typer.confirm(question, default=False):
            typer.echo("Restore canceled. No files changed.")
            return
        completed = snapshot_documents.restore_files(root, plan)
    except (OSError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    if file is not None:
        typer.echo(
            f"Restored {next(iter(plan))} from snapshot {snapshot.number}."
        )
    else:
        noun = "file" if len(completed) == 1 else "files"
        typer.echo(
            f"Restored {len(completed)} {noun} from snapshot {snapshot.number}."
        )
    typer.echo("Use phist save if you want to save this as a new snapshot.")

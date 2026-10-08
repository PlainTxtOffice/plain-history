"""Collect a writer's save message and optional semantic version."""

import typer

from src.domains import history


def _read_message(message: str | None) -> str:
    """Prompt for a nonempty message or preserve a valid argument."""
    while True:
        if message is None:
            message = str(typer.prompt("Save message", type=str))
        try:
            return history.validate_message(message)
        except ValueError as error:
            typer.echo(str(error), err=True)
            message = None


def _read_version(current: str | None) -> str | None:
    """Offer to apply or change a version, retaining it when declined."""
    if current is None:
        question = "Apply a version number?"
    else:
        typer.echo(f"Current version: {current}")
        question = "Change the version number?"
    if not typer.confirm(question, default=False):
        return current
    while True:
        version = typer.prompt(
            "Version (MAJOR.MINOR.PATCH)", default=current or "0.1.0"
        )
        try:
            return history.validate_version(version.strip())
        except ValueError as error:
            typer.echo(str(error), err=True)


def read_details(
    message: str | None,
    current: str | None,
) -> tuple[str, str | None]:
    """Ask for the message followed by an optional version choice.

    Ctrl+C or end-of-input aborts before any snapshot is written.
    """
    return _read_message(message), _read_version(current)

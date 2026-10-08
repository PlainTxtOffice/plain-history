"""Initialize and inspect a document repository on disk."""

import tomllib
from pathlib import Path

from src.domains import repository

DIRECTORY = ".plain_history"


def load(root: Path) -> Path:
    """Read and validate repository metadata at the exact root supplied.

    Raise ValueError for an uninitialized or unsupported repository.
    """
    metadata = root.resolve() / DIRECTORY
    config = metadata / "config.toml"
    if not config.is_file():
        message = f"No repository at {root.resolve()}; run phist init first."
        raise ValueError(message)
    with config.open("rb") as stream:
        settings = tomllib.load(stream)
    repository.validate_format(settings.get("format_version"))
    if not (metadata / "objects").is_dir():
        message = "Repository objects directory is missing."
        raise ValueError(message)
    return metadata


def init(root: Path) -> Path:
    """Create starter metadata without changing document contents.

    The root must already exist. Existing repositories are validated and
    preserved; unrecognized metadata is never overwritten.
    """
    root = root.resolve()
    if not root.is_dir():
        message = f"Repository root is not a directory: {root}"
        raise ValueError(message)
    metadata = root / DIRECTORY
    if metadata.exists():
        return load(root)
    metadata.mkdir()
    (metadata / "objects").mkdir()
    (metadata / "config.toml").write_text(
        "format_version = 1\n", encoding="utf-8", newline="\n"
    )
    return metadata

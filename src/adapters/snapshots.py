"""Persist snapshot history and document contents."""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from src.adapters import repository, snapshot_content, tracking
from src.domains import history


def load(root: Path) -> list[history.Snapshot]:
    """Read saved history; an absent file means no saves."""
    path = repository.load(root) / "history.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or any(
        not isinstance(record, dict) for record in raw
    ):
        message = "Invalid history.json: expected a list of snapshots."
        raise ValueError(message)
    return [
        history.parse_snapshot(record, number)
        for number, record in enumerate(raw, start=1)
    ]


def list_selection(root: Path) -> list[str]:
    """Return matching tracked files; reject an empty snapshot selection."""
    names = tracking.list_files(root, tracking.load(root))
    if not names:
        detail = "No tracked files match. Use phist track, then phist check."
        raise ValueError(detail)
    return names


def _write_snapshot(
    root: Path,
    metadata: Path,
    message: str,
    version: str | None,
    expected_count: int,
) -> history.Snapshot:
    """Write one snapshot after rechecking history and reading all documents."""
    saved = load(root)
    if len(saved) != expected_count:
        detail = (
            "History changed while answering prompts; run phist save again."
        )
        raise ValueError(detail)
    names = list_selection(root)
    contents = {
        name: snapshot_content.read_document(root, name) for name in names
    }
    files = snapshot_content.write_objects(metadata, contents)
    snapshot = history.Snapshot(
        len(saved) + 1,
        datetime.now(UTC).isoformat(),
        message,
        version,
        files,
    )
    payload = (
        json.dumps(
            [asdict(s) for s in [*saved, snapshot]],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    snapshot_content.write_atomic(
        metadata / "history.json", payload.encode("utf-8")
    )
    return snapshot


def save(
    root: Path,
    message: str,
    version: str | None,
    expected_count: int,
) -> history.Snapshot:
    """Save tracked files with one message and optional version for the folder.

    A lock serializes saves; changed history during prompting requires a retry.
    History is replaced atomically after objects are written. Document files
    are never modified. An empty current selection cannot be saved.
    """
    root = root.resolve()
    metadata = repository.load(root)
    message = history.validate_message(message)
    if version is not None:
        history.validate_version(version)
    lock = metadata / "save.lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as error:
        detail = (
            "Another save is active, or an interrupted save left save.lock."
        )
        raise ValueError(detail) from error
    try:
        with stream:
            return _write_snapshot(
                root, metadata, message, version, expected_count
            )
    finally:
        lock.unlink()

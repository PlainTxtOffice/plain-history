"""Retrieve saved contents and restore selected snapshot documents."""

from pathlib import Path

from src.adapters import repository, snapshot_content, snapshots
from src.domains import history, storage, tracking

RestorePlan = dict[str, tuple[bytes, bytes | None]]


def load_snapshot(root: Path, number: int | None) -> history.Snapshot:
    """Select a saved snapshot, defaulting to the latest whole-folder save."""
    saved = snapshots.load(root)
    if not saved:
        detail = "No snapshots saved yet. Use phist save to save a draft."
        raise ValueError(detail)
    number = len(saved) if number is None else number
    if number < 1 or number > len(saved):
        detail = f"No saved snapshot numbered {number}. Use phist history."
        raise ValueError(detail)
    return saved[number - 1]


def _select_name(snapshot: history.Snapshot, file: Path) -> str:
    """Find a recorded relative filename using platform path case rules."""
    name = tracking.normalize_pattern(str(file))
    matches = [path for path in snapshot.files if Path(path) == Path(name)]
    if not matches:
        detail = f"Snapshot {snapshot.number} does not contain: {name}"
        raise ValueError(detail)
    return matches[0]


def _read_content(root: Path, snapshot: history.Snapshot, name: str) -> bytes:
    """Verify stored document bytes before comparison or restoration."""
    digest = snapshot.files[name]
    metadata = repository.load(root)
    object_name = (metadata / "objects" / digest).relative_to(root).as_posix()
    content = snapshot_content.read_document(root, object_name)
    if storage.calc_digest(content) != digest:
        detail = f"Stored snapshot content is damaged: {digest}"
        raise ValueError(detail)
    return content


def load(
    root: Path,
    file: Path,
    number: int | None,
) -> tuple[history.Snapshot, str, bytes]:
    """Read one saved document and verify its content identifier."""
    root = repository.load(root).parent
    tracking.normalize_pattern(str(file))
    snapshot = load_snapshot(root, number)
    name = _select_name(snapshot, file)
    return snapshot, name, _read_content(root, snapshot, name)


def read_current(root: Path, name: str) -> bytes | None:
    """Read current document bytes, or return None if it is missing."""
    try:
        return snapshot_content.read_document(root, name)
    except FileNotFoundError:
        return None


def prepare_restore(
    root: Path,
    file: Path | None,
    number: int,
) -> tuple[history.Snapshot, RestorePlan]:
    """Verify selected saved contents and current destinations before writes."""
    root = repository.load(root).parent
    snapshot = load_snapshot(root, number)
    names = [_select_name(snapshot, file)] if file else sorted(snapshot.files)
    plan = {
        name: (_read_content(root, snapshot, name), read_current(root, name))
        for name in names
    }
    return snapshot, plan


def restore(
    root: Path,
    name: str,
    content: bytes,
    expected: bytes | None,
) -> None:
    """Replace or recreate one document after checking it has not changed.

    Preserve exact bytes and history. Missing parent folders are created.
    """
    if read_current(root, name) != expected:
        detail = "Document changed while answering prompts; retry restore."
        raise ValueError(detail)
    path = snapshot_content.document_path(root, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_content.write_atomic(path, content)


def restore_files(root: Path, plan: RestorePlan) -> list[str]:
    """Apply a reviewed plan after checking all destinations for new edits.

    Each replacement is atomic. A whole-folder restore is not transactional;
    a failure reports completed files without creating backup copies.
    """
    for name, (_, expected) in plan.items():
        if read_current(root, name) != expected:
            detail = "Document changed while answering prompts; retry restore."
            raise ValueError(detail)
    completed: list[str] = []
    try:
        for name, (content, current) in plan.items():
            if content != current:
                restore(root, name, content, current)
                completed.append(name)
    except (OSError, ValueError) as error:
        detail = (
            f"Restore stopped. Files restored: {len(completed)} "
            f"({', '.join(completed) or 'none'}). {error}"
        )
        raise ValueError(detail) from error
    return completed

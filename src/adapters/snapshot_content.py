"""Read selected document bytes and store content-addressed snapshot objects."""

import os
import tempfile
from pathlib import Path

from src.domains import storage


def write_atomic(path: Path, content: bytes) -> None:
    """Replace a file only after its complete contents have been written.

    Temporary files are removed on failure; no backup copies are created.
    """
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def document_path(root: Path, name: str) -> Path:
    """Resolve a document location while rejecting links and outside paths."""
    path = root / name
    relative = path.relative_to(root)
    chain = [
        root.joinpath(*relative.parts[:i])
        for i in range(1, len(relative.parts) + 1)
    ]
    if not path.resolve().is_relative_to(root) or any(
        p.is_symlink() or p.is_junction() for p in chain
    ):
        message = f"Cannot use a linked or outside file: {name}"
        raise ValueError(message)
    return path


def read_document(root: Path, name: str) -> bytes:
    """Read a selected file while rejecting links and outside paths."""
    return document_path(root, name).read_bytes()


def write_objects(metadata: Path, contents: dict[str, bytes]) -> dict[str, str]:
    """Store exact document bytes and return each file's content identifier.

    Existing objects are checked before reuse. Failed saves may leave unused
    objects, but do not modify previously saved contents.
    """
    files: dict[str, str] = {}
    for name, content in contents.items():
        digest = storage.calc_digest(content)
        path = metadata / "objects" / digest
        if path.exists():
            if path.read_bytes() != content:
                message = f"Stored snapshot content is damaged: {digest}"
                raise ValueError(message)
        else:
            write_atomic(path, content)
        files[name] = digest
    return files

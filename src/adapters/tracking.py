"""Persist tracking rules and find selected documents in a writing folder."""

import json
from pathlib import Path

from src.adapters import repository
from src.domains import tracking


def load(root: Path) -> list[str]:
    """Read tracking rules; older initialized folders start with no rules."""
    config = repository.load(root) / "tracking.json"
    if not config.exists():
        return []
    settings = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(settings, list) or any(
        not isinstance(pattern, str) for pattern in settings
    ):
        message = "Invalid tracking.json: expected a list of tracking rules."
        raise ValueError(message)
    return list(dict.fromkeys(tracking.normalize_pattern(p) for p in settings))


def add(root: Path, patterns: list[str]) -> list[str]:
    """Add unique rules without changing document contents or other settings.

    Validate the entire batch before writing. Unmatched rules are kept for
    future files; literal directory paths require an explicit glob instead.
    """
    existing = load(root)
    normalized = [tracking.normalize_pattern(pattern) for pattern in patterns]
    for pattern in normalized:
        if (root / pattern).is_dir():
            message = f"Use {pattern}/**/* to select files inside a folder."
            raise ValueError(message)
    combined = list(dict.fromkeys([*existing, *normalized]))
    if combined != existing:
        config = repository.load(root) / "tracking.json"
        config.write_text(
            json.dumps(combined, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return combined


def list_files(root: Path, patterns: list[str]) -> list[str]:
    """Find unique matching files, excluding metadata and symbolic links.

    Rules are evaluated anew so future documents are included automatically.
    Returned paths are relative to the initialized folder and sorted.
    """
    root = root.resolve()
    matches: set[str] = set()
    for pattern in patterns:
        for path in root.glob(tracking.normalize_pattern(pattern)):
            relative = path.relative_to(root)
            if any(p.casefold() == ".plain_history" for p in relative.parts):
                continue
            chain = [
                root.joinpath(*relative.parts[:index])
                for index in range(1, len(relative.parts) + 1)
            ]
            if any(p.is_symlink() or p.is_junction() for p in chain):
                continue
            if path.is_file() and path.resolve().is_relative_to(root):
                matches.add(relative.as_posix())
    return sorted(matches)

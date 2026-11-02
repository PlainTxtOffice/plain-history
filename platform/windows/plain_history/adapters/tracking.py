"""Persist tracking rules and find selected documents in a writing folder."""

import json
from pathlib import Path

from plain_history.adapters import repository
from plain_history.domains.tracking import rules as tracking_rules


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
    return list(
        dict.fromkeys(tracking_rules.normalize_pattern(p) for p in settings)
    )


def normalize_rules(root: Path, patterns: list[str]) -> list[str]:
    """Normalize a batch of rules; reject literal directory paths.

    Raise ValueError for a rule outside the folder or a bare folder path.
    """
    normalized = [
        tracking_rules.normalize_pattern(pattern) for pattern in patterns
    ]
    for pattern in normalized:
        if (root / pattern).is_dir():
            message = f"Use {pattern}/**/* to select files inside a folder."
            raise ValueError(message)
    return normalized


def _write_rules(root: Path, rules: list[str]) -> None:
    """Replace tracking.json with the supplied rules."""
    config = repository.load(root) / "tracking.json"
    config.write_text(
        json.dumps(rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def add(root: Path, patterns: list[str]) -> list[str]:
    """Add unique rules without changing document contents or other settings.

    Validate the entire batch before writing. Unmatched rules are kept for
    future files; literal directory paths require an explicit glob instead.
    """
    existing = load(root)
    normalized = normalize_rules(root, patterns)
    combined = list(dict.fromkeys([*existing, *normalized]))
    if combined != existing:
        _write_rules(root, combined)
    return combined


def update(root: Path, patterns: list[str]) -> list[str]:
    """Replace every tracking rule with a new list, keeping its order.

    Validate the entire list before writing, using the same rules as add.
    Removing a rule never changes documents or saved history.
    """
    existing = load(root)
    rules = list(dict.fromkeys(normalize_rules(root, patterns)))
    if rules != existing:
        _write_rules(root, rules)
    return rules


def list_files(root: Path, patterns: list[str]) -> list[str]:
    """Find unique matching files, excluding metadata and symbolic links.

    Rules are evaluated anew so future documents are included automatically.
    Returned paths are relative to the initialized folder and sorted.
    """
    root = root.resolve()
    matches: set[str] = set()
    for pattern in patterns:
        for path in root.glob(tracking_rules.normalize_pattern(pattern)):
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

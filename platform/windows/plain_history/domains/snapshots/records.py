"""Define snapshot records and classify how a restore changes a file."""

import re
from dataclasses import dataclass
from enum import StrEnum

from plain_history.domains.snapshots import labels
from plain_history.domains.tracking import rules as tracking_rules


@dataclass(frozen=True)
class Snapshot:
    """Describe one saved selection with an optional writing version label."""

    number: int
    created_at: str
    message: str
    version: str | None
    files: dict[str, str]


class RestoreAction(StrEnum):
    """Name what restoring one saved document would do to the current file."""

    UNCHANGED = "unchanged"
    RECREATE = "recreate"
    REPLACE = "replace"


def calc_restore_action(saved: bytes, current: bytes | None) -> RestoreAction:
    """Classify saved bytes against current bytes; None means missing."""
    if current == saved:
        return RestoreAction.UNCHANGED
    if current is None:
        return RestoreAction.RECREATE
    return RestoreAction.REPLACE


def parse_snapshot(raw: object, number: int) -> Snapshot:
    """Validate a stored snapshot before using its files or version label."""
    if not isinstance(raw, dict) or not raw:
        detail = "Invalid snapshot record."
        raise ValueError(detail)
    message, version = raw.get("message"), raw.get("version")
    files, created_at = raw.get("files"), raw.get("created_at")
    if (
        type(raw.get("number")) is not int
        or raw["number"] != number
        or not isinstance(message, str)
        or not isinstance(created_at, str)
        or not created_at
        or not isinstance(files, dict)
        or not files
        or (version is not None and not isinstance(version, str))
    ):
        detail = "Invalid snapshot fields."
        raise ValueError(detail)
    for path, digest in files.items():
        if (
            not isinstance(path, str)
            or tracking_rules.normalize_pattern(path) != path
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            detail = "Invalid snapshot file entry."
            raise ValueError(detail)
    return Snapshot(
        number,
        created_at,
        labels.validate_message(message),
        labels.validate_version(version) if version is not None else None,
        files,
    )

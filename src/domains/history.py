"""Define snapshot records and validate save messages and semantic versions."""

import re
from dataclasses import dataclass

from src.domains import tracking

_NUMBER = r"(?:0|[1-9][0-9]*)"
_IDENTIFIER = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}"
    rf"(?:-({_IDENTIFIER}(?:\.{_IDENTIFIER})*))?"
    rf"(?:\+{_IDENTIFIER}(?:\.{_IDENTIFIER})*)?"
)


@dataclass(frozen=True)
class Snapshot:
    """Describe one saved selection with an optional writing version label."""

    number: int
    created_at: str
    message: str
    version: str | None
    files: dict[str, str]


def validate_version(version: str) -> str:
    """Return a valid SemVer 2.0.0 label or raise ValueError.

    Numeric components and numeric prerelease identifiers cannot have leading
    zeroes. Build metadata may contain leading zeroes.
    """
    match = _VERSION.fullmatch(version)
    if match and not any(
        part.isdigit() and len(part) > 1 and part.startswith("0")
        for part in (match.group(1) or "").split(".")
    ):
        return version
    message = "Use a semantic version such as 0.1.0 or 1.0.0-beta.1."
    raise ValueError(message)


def validate_message(message: str) -> str:
    """Return a trimmed save message; reject empty or whitespace-only text."""
    if message.strip():
        return message.strip()
    detail = "Enter a nonempty save message."
    raise ValueError(detail)


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
            or tracking.normalize_pattern(path) != path
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            detail = "Invalid snapshot file entry."
            raise ValueError(detail)
    return Snapshot(
        number,
        created_at,
        validate_message(message),
        validate_version(version) if version is not None else None,
        files,
    )

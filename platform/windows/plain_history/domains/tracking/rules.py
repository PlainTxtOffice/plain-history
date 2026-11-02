"""Validate document selection rules independently of the filesystem."""

from pathlib import PurePosixPath, PureWindowsPath

CONTROL_CHARACTER_LIMIT = 32


def normalize_pattern(pattern: str) -> str:
    """Normalize a relative file or glob rule; reject paths outside history.

    Backslashes become forward slashes. Parent traversal and history metadata
    are forbidden, including Windows drive-relative paths.
    """
    normalized = pattern.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if (
        not parts
        or PureWindowsPath(normalized).drive
        or normalized.startswith("/")
        or ".." in parts
        or ":" in normalized
        or any("**" in part and part != "**" for part in parts)
        or any(part.casefold() == ".plain_history" for part in parts)
        or any(
            ord(character) < CONTROL_CHARACTER_LIMIT for character in normalized
        )
    ):
        message = f"Use a relative file or glob in this folder: {pattern!r}"
        raise ValueError(message)
    return PurePosixPath(normalized).as_posix()

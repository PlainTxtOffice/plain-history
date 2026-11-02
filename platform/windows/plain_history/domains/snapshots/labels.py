"""Validate the save message and semantic version a writer gives a snapshot."""

import re

_NUMBER = r"(?:0|[1-9][0-9]*)"
_IDENTIFIER = r"[0-9A-Za-z-]+"
_VERSION = re.compile(
    rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}"
    rf"(?:-({_IDENTIFIER}(?:\.{_IDENTIFIER})*))?"
    rf"(?:\+{_IDENTIFIER}(?:\.{_IDENTIFIER})*)?"
)


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

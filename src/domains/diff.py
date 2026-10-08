"""Compare document text independently of storage and interfaces."""

import difflib


def format_diff(before: str, after: str) -> str:
    """Return a line-based unified diff, or an empty string if equal.

    Lines are compared without terminators in this starter implementation.
    """
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )

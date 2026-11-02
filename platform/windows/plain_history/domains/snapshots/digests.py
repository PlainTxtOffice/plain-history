"""Define content addressing for future full-content snapshot storage."""

import hashlib


def calc_digest(content: bytes) -> str:
    """Return a stable SHA-256 identifier without writing to disk."""
    return hashlib.sha256(content).hexdigest()

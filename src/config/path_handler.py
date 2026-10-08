"""Static/base path constants for development and packaged builds."""

from __future__ import annotations

import sys
from pathlib import Path

IS_COMPILED = bool(
    globals().get("__compiled__", False) or getattr(sys, "frozen", False),
)
DEV_ROOT = Path(__file__).resolve().parents[2]

# This template assumes compiled binaries live under build/<mode>/name.exe.
COMPILED_ROOT = Path(sys.executable).resolve().parents[2]

ROOT_DIR = COMPILED_ROOT if IS_COMPILED else DEV_ROOT
LOGS_DIR = ROOT_DIR / "logs"
EXPORTS_DIR = ROOT_DIR / "exports"
BACKUPS_DIR = EXPORTS_DIR / "backups"
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Optional per-user persistence root for projects that choose a
# system-managed user data location instead of repository-local DATA_DIR.
USER_DATA_DIR: Path | None = None

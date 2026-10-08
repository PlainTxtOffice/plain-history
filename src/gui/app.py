"""Display a minimal desktop view of repository initialization status."""

import sys
from pathlib import Path

from PySide6 import QtWidgets

from src.adapters import repository


def build_window(root: Path) -> QtWidgets.QMainWindow:
    """Read status and build the starter window without showing it."""
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("plain_history")
    window.resize(640, 320)
    try:
        metadata = repository.load(root)
        status = f"Repository: {metadata.parent}"
    except (OSError, ValueError) as error:
        status = str(error)
    label = QtWidgets.QLabel(
        f"plain_history\n\n{status}\n\n"
        "Starter interface. Snapshot browsing and editing are not implemented."
    )
    label.setWordWrap(True)
    label.setMargin(24)
    window.setCentralWidget(label)
    return window


def main() -> None:
    """Open the desktop application for the current working directory."""
    application = QtWidgets.QApplication(sys.argv)
    window = build_window(Path.cwd())
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()

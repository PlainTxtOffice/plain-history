"""Start the desktop window and reopen the writer's last folder."""

import sys
from types import TracebackType

from PySide6 import QtCore, QtWidgets

from plain_history.ui.gui.events.session import Session
from plain_history.ui.gui.views.root_window.window import RootWindow

ORGANIZATION = "plaintxtoffice"
APPLICATION = "plain_history"


def build_session(settings: QtCore.QSettings) -> Session:
    """Create the root window and connect it to a folder session."""
    return Session(RootWindow(), settings)


def _report_fault(
    kind: type[BaseException],
    error: BaseException,
    trace: TracebackType | None,
) -> None:
    """Show unexpected faults that a windowed build would otherwise hide."""
    QtWidgets.QMessageBox.critical(
        None,
        APPLICATION,
        f"Something unexpected went wrong.\n\n{kind.__name__}: {error}",
    )
    sys.__excepthook__(kind, error, trace)


def main() -> None:
    """Open the desktop window; settings persist per Windows user."""
    application = QtWidgets.QApplication([])
    application.setOrganizationName(ORGANIZATION)
    application.setApplicationName(APPLICATION)
    sys.excepthook = _report_fault
    session = build_session(QtCore.QSettings())
    session.window.show()
    session.open_last_folder()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()

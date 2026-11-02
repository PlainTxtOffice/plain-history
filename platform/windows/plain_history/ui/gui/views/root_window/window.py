"""Lay out the main window around a writing folder's saved history."""

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from plain_history.ui.gui.views.root_window.history import HistoryList
from plain_history.ui.gui.views.root_window.snapshot import SnapshotPanel

_WELCOME_TEXT = (
    "plain_history keeps snapshots of the documents in a writing folder, so "
    "you can compare drafts and bring back earlier versions. Your documents "
    "stay where they are; history is kept in a hidden .plain_history folder."
)


class RootWindow(QtWidgets.QMainWindow):
    """Show a welcome page or an open folder's history, snapshot, and tracking.

    The window holds no repository state. It emits requests for the session
    and displays whatever the session gives it.
    """

    open_folder_requested = QtCore.Signal()
    save_requested = QtCore.Signal()
    choose_documents_requested = QtCore.Signal()
    activated = QtCore.Signal()

    def __init__(self) -> None:
        """Build the window on its welcome page."""
        super().__init__()
        self.setWindowTitle("plain_history")
        self.resize(980, 620)
        self.history = HistoryList()
        self.snapshot = SnapshotPanel()
        self._banner = QtWidgets.QLabel()
        self._banner.setWordWrap(True)
        self._banner.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self._banner.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self._banner.setMargin(8)
        self._banner.hide()
        self._folder = QtWidgets.QLabel()
        self._folder.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self._folder.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        # Long paths are clipped instead of widening the window.
        self._folder.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self._tracking = QtWidgets.QLabel()
        self._tracking.setWordWrap(True)
        self._tracking.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self._pages = QtWidgets.QStackedWidget()
        self._pages.addWidget(self._build_welcome())
        self._pages.addWidget(self._build_workspace())
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.addWidget(self._banner)
        layout.addWidget(self._pages, 1)
        self.setCentralWidget(central)
        self._build_menu()

    def _build_menu(self) -> None:
        """Add a File menu so every action has a keyboard shortcut."""
        menu = self.menuBar().addMenu("&File")
        entries = [
            ("&Open writing folder…", "Ctrl+O", self.open_folder_requested),
            ("&Save snapshot…", "Ctrl+S", self.save_requested),
            ("&Choose documents…", "Ctrl+D", self.choose_documents_requested),
        ]
        self._folder_actions: list[QtGui.QAction] = []
        for text, shortcut, signal in entries:
            action = menu.addAction(text)
            action.setShortcut(QtGui.QKeySequence(shortcut))
            action.triggered.connect(signal)
            self._folder_actions.append(action)
        menu.addSeparator()
        close = menu.addAction("E&xit")
        close.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
        close.triggered.connect(self.close)
        for action in self._folder_actions[1:]:
            action.setEnabled(False)

    def _build_welcome(self) -> QtWidgets.QWidget:
        """Create the first-run page that asks for a writing folder."""
        page = QtWidgets.QWidget()
        heading = QtWidgets.QLabel("Keep a history of your writing")
        font = heading.font()
        font.setPointSizeF(font.pointSizeF() * 1.6)
        font.setBold(True)
        heading.setFont(font)
        text = QtWidgets.QLabel(_WELCOME_TEXT)
        text.setWordWrap(True)
        choose = QtWidgets.QPushButton("Choose writing folder…")
        choose.setDefault(True)
        choose.clicked.connect(self.open_folder_requested)
        # A fixed-width column lets the wrapped paragraph claim its height.
        column = QtWidgets.QWidget()
        column.setFixedWidth(520)
        column_layout = QtWidgets.QVBoxLayout(column)
        column_layout.setSpacing(16)
        column_layout.addWidget(heading)
        column_layout.addWidget(text)
        column_layout.addWidget(choose, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        row.addWidget(column)
        row.addStretch(1)
        layout = QtWidgets.QVBoxLayout(page)
        layout.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(2)
        return page

    def _build_workspace(self) -> QtWidgets.QWidget:
        """Create the folder header, history split view, and tracking footer."""
        page = QtWidgets.QWidget()
        open_other = QtWidgets.QPushButton("Open another folder…")
        open_other.clicked.connect(self.open_folder_requested)
        save = QtWidgets.QPushButton("Save snapshot…")
        save.setDefault(True)
        save.clicked.connect(self.save_requested)
        header = QtWidgets.QHBoxLayout()
        header.addWidget(self._folder, 1)
        header.addWidget(open_other)
        header.addWidget(save)
        history_label = QtWidgets.QLabel("&History")
        history_label.setBuddy(self.history)
        history_column = QtWidgets.QWidget()
        history_layout = QtWidgets.QVBoxLayout(history_column)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history, 1)
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(history_column)
        splitter.addWidget(self.snapshot)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 640])
        choose = QtWidgets.QPushButton("Choose documents…")
        choose.clicked.connect(self.choose_documents_requested)
        footer = QtWidgets.QHBoxLayout()
        footer.addWidget(self._tracking, 1)
        footer.addWidget(choose)
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        layout.addWidget(splitter, 1)
        layout.addLayout(footer)
        return page

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """Emit activated when the writer returns to the window."""
        super().changeEvent(event)
        if (
            event.type() == QtCore.QEvent.Type.ActivationChange
            and self.isActiveWindow()
        ):
            self.activated.emit()

    def ask_yes_no(self, title: str, question: str) -> bool:
        """Ask a yes/no question; No is the default answer."""
        answer = QtWidgets.QMessageBox.question(
            self,
            title,
            question,
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    def ask_folder(self, start: Path | None) -> Path | None:
        """Ask for a writing folder; return None if the writer cancels."""
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose your writing folder", str(start or Path.home())
        )
        return Path(chosen) if chosen else None

    def show_welcome(self) -> None:
        """Show the first-run page and disable folder-only actions."""
        self.setWindowTitle("plain_history")
        self._pages.setCurrentIndex(0)
        for action in self._folder_actions[1:]:
            action.setEnabled(False)

    def show_folder(self, root: Path) -> None:
        """Show the workspace for an open writing folder."""
        self.setWindowTitle(f"{root.name} - plain_history")
        self._folder.setText(f"Writing folder: {root}")
        self._folder.setToolTip(str(root))
        self._pages.setCurrentIndex(1)
        for action in self._folder_actions:
            action.setEnabled(True)

    def show_tracking(self, rules: list[str], file_count: int) -> None:
        """Summarize the tracking rules and how many documents they match."""
        if not rules:
            self._tracking.setText(
                "No documents chosen yet. Choose the documents to keep history "
                "for before saving a snapshot."
            )
            return
        noun = "document" if file_count == 1 else "documents"
        self._tracking.setText(
            f"Tracking {', '.join(rules)}  ·  {file_count} {noun} match"
        )

    def show_notice(self, message: str) -> None:
        """Show a confirmation above the workspace until the next message."""
        self._banner.setText(message)
        self._banner.setAccessibleName("Notice")
        self._banner.show()

    def show_error(self, message: str) -> None:
        """Show a problem above the workspace with a clear text prefix."""
        self._banner.setText(f"Problem: {message}")
        self._banner.setAccessibleName("Problem")
        self._banner.show()

    def clear_message(self) -> None:
        """Hide the notice or problem banner."""
        self._banner.hide()

    def banner_text(self) -> str | None:
        """Return the visible banner text, or None when it is hidden."""
        return self._banner.text() if self._banner.isVisibleTo(self) else None

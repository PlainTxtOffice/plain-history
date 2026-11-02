"""Show one snapshot's documents and how each differs from the current file."""

from PySide6 import QtCore, QtWidgets

from plain_history.domains.snapshots import records
from plain_history.ui.gui.views import timestamps

_CURRENT_STATES = {
    records.RestoreAction.UNCHANGED: "Unchanged",
    records.RestoreAction.REPLACE: "Edited since this snapshot",
    records.RestoreAction.RECREATE: "Missing from the folder",
}
_NAME_ROLE = QtCore.Qt.ItemDataRole.UserRole
_ACTION_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


class SnapshotPanel(QtWidgets.QWidget):
    """Present snapshot details with compare and restore requests.

    Buttons emit requests only; the session decides what happens next.
    """

    compare_requested = QtCore.Signal(str)
    restore_file_requested = QtCore.Signal(str)
    restore_snapshot_requested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Build the panel showing a placeholder until a snapshot is shown."""
        super().__init__(parent)
        self._title = QtWidgets.QLabel()
        self._title.setWordWrap(True)
        self._title.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        font = self._title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        font.setBold(True)
        self._title.setFont(font)
        self._details = QtWidgets.QLabel()
        self._details.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self._documents = self._build_documents()
        self._compare = QtWidgets.QPushButton("&Compare with current")
        self._restore_file = QtWidgets.QPushButton("Restore &file…")
        self._restore_snapshot = QtWidgets.QPushButton("Restore &snapshot…")
        self._compare.clicked.connect(self._request_compare)
        self._restore_file.clicked.connect(self._request_restore_file)
        self._restore_snapshot.clicked.connect(self.restore_snapshot_requested)
        self._placeholder = QtWidgets.QLabel()
        self._placeholder.setWordWrap(True)
        self._placeholder.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self._stack = QtWidgets.QStackedLayout(self)
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._build_details_page())
        self.show_placeholder("Select a snapshot to see its documents.")

    def _build_documents(self) -> QtWidgets.QTreeWidget:
        """Create the two-column document table."""
        documents = QtWidgets.QTreeWidget()
        documents.setAccessibleName("Documents in this snapshot")
        documents.setHeaderLabels(["Document", "Current file"])
        documents.setRootIsDecorated(False)
        documents.setAlternatingRowColors(True)
        documents.header().setStretchLastSection(True)
        documents.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        documents.itemSelectionChanged.connect(self._update_buttons)
        documents.itemActivated.connect(self._request_compare)
        return documents

    def _build_details_page(self) -> QtWidgets.QWidget:
        """Arrange the heading, document table, and action buttons."""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._title)
        layout.addWidget(self._details)
        layout.addWidget(self._documents, 1)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self._compare)
        buttons.addWidget(self._restore_file)
        buttons.addStretch(1)
        buttons.addWidget(self._restore_snapshot)
        layout.addLayout(buttons)
        return page

    def _selected_entry(self) -> QtWidgets.QTreeWidgetItem | None:
        """Return the selected document row, if any."""
        selected = self._documents.selectedItems()
        return selected[0] if selected else None

    def _update_buttons(self) -> None:
        """Enable actions that make sense for the current selection."""
        entry = self._selected_entry()
        action = None if entry is None else entry.data(0, _ACTION_ROLE)
        self._compare.setEnabled(entry is not None)
        self._restore_file.setEnabled(
            action not in {None, records.RestoreAction.UNCHANGED}
        )

    def _request_compare(self) -> None:
        """Emit a compare request for the selected document."""
        name = self.selected_document()
        if name is not None:
            self.compare_requested.emit(name)

    def _request_restore_file(self) -> None:
        """Emit a restore request for the selected document."""
        name = self.selected_document()
        if name is not None:
            self.restore_file_requested.emit(name)

    def selected_document(self) -> str | None:
        """Return the selected document's relative path, if any."""
        entry = self._selected_entry()
        return None if entry is None else str(entry.data(0, _NAME_ROLE))

    def show_placeholder(self, message: str) -> None:
        """Replace the details with a short explanation."""
        self._placeholder.setText(message)
        self._stack.setCurrentIndex(0)

    def show_snapshot(
        self,
        snapshot: records.Snapshot,
        actions: dict[str, records.RestoreAction],
    ) -> None:
        """Show a snapshot and each document's state, keeping the selection."""
        previous = self.selected_document()
        self._title.setText(f"Snapshot {snapshot.number}: {snapshot.message}")
        saved_at = timestamps.format_saved_at(snapshot.created_at)
        version = snapshot.version or "none"
        self._details.setText(f"Saved {saved_at}  ·  Version: {version}")
        self._documents.clear()
        for name, action in sorted(actions.items()):
            entry = QtWidgets.QTreeWidgetItem([name, _CURRENT_STATES[action]])
            entry.setData(0, _NAME_ROLE, name)
            entry.setData(0, _ACTION_ROLE, action)
            self._documents.addTopLevelItem(entry)
            if name == previous:
                entry.setSelected(True)
        changed = any(
            action is not records.RestoreAction.UNCHANGED
            for action in actions.values()
        )
        self._restore_snapshot.setEnabled(changed)
        self._update_buttons()
        self._stack.setCurrentIndex(1)

"""List saved snapshots newest first and report which one is selected."""

from PySide6 import QtCore, QtWidgets

from plain_history.domains.snapshots import records
from plain_history.ui.gui.views import timestamps

_NUMBER_ROLE = QtCore.Qt.ItemDataRole.UserRole


def _format_entry(snapshot: records.Snapshot) -> str:
    """Return a two-line label with the message, save time, and version."""
    saved_at = timestamps.format_saved_at(snapshot.created_at)
    version = f"  ·  version {snapshot.version}" if snapshot.version else ""
    return f"{snapshot.number}. {snapshot.message}\n{saved_at}{version}"


class HistoryList(QtWidgets.QListWidget):
    """Show one entry per snapshot and emit the selected snapshot number."""

    snapshot_selected = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Build an empty list; selection changes emit snapshot_selected."""
        super().__init__(parent)
        self.setAccessibleName("Saved history")
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.setSpacing(2)
        self.currentItemChanged.connect(self._emit_selection)

    def _emit_selection(
        self,
        current: QtWidgets.QListWidgetItem | None,
        _previous: QtWidgets.QListWidgetItem | None,
    ) -> None:
        """Forward the snapshot number of a newly selected entry."""
        if current is not None:
            self.snapshot_selected.emit(int(current.data(_NUMBER_ROLE)))

    def selected_number(self) -> int | None:
        """Return the selected snapshot number, or None when nothing is."""
        current = self.currentItem()
        return None if current is None else int(current.data(_NUMBER_ROLE))

    def show_snapshots(self, snapshots: list[records.Snapshot]) -> None:
        """Replace all entries, then reselect the previous or newest snapshot.

        Emit snapshot_selected once for the final selection so details stay
        current after files change outside the window.
        """
        previous = self.selected_number()
        self.blockSignals(True)  # noqa: FBT003
        try:
            self.clear()
            for snapshot in reversed(snapshots):
                entry = QtWidgets.QListWidgetItem(_format_entry(snapshot))
                entry.setData(_NUMBER_ROLE, snapshot.number)
                self.addItem(entry)
        finally:
            self.blockSignals(False)  # noqa: FBT003
        numbers = [snapshot.number for snapshot in snapshots]
        if numbers:
            self.select_number(previous if previous in numbers else numbers[-1])

    def select_number(self, number: int) -> None:
        """Select the entry for one snapshot number, if it is listed."""
        for row in range(self.count()):
            entry = self.item(row)
            if int(entry.data(_NUMBER_ROLE)) == number:
                self.setCurrentRow(row)
                return

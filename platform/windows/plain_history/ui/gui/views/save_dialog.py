"""Collect a save message and optional version before saving a snapshot."""

from PySide6 import QtCore, QtWidgets

from plain_history.domains.snapshots import labels

_DEFAULT_VERSION = "0.1.0"
_VERSION_HINT = "Use three numbers such as 0.1.0, 1.0.0, or 1.0.0-beta.1."


class SaveDialog(QtWidgets.QDialog):
    """Ask what changed and whether to set or change the version number.

    Leaving the version box unchecked keeps the current version, matching
    the command line. Invalid input is reported inside the dialog.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        current_version: str | None,
        documents: list[str],
    ) -> None:
        """Build the form for the documents that will be saved."""
        super().__init__(parent)
        self.setWindowTitle("Save snapshot")
        self.setMinimumWidth(460)
        self._current_version = current_version
        self._message = QtWidgets.QLineEdit()
        self._message.setPlaceholderText("For example: Finished chapter 3")
        message_label = QtWidgets.QLabel("What &changed?")
        message_label.setBuddy(self._message)
        noun = "document" if len(documents) == 1 else "documents"
        summary = QtWidgets.QLabel(f"{len(documents)} {noun} will be saved:")
        listing = QtWidgets.QListWidget()
        listing.addItems(documents)
        listing.setAccessibleName("Documents to save")
        listing.setMaximumHeight(120)
        listing.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self._change_version = QtWidgets.QCheckBox(
            "Set a &version number"
            if current_version is None
            else f"Change the &version number (now {current_version})"
        )
        self._version = QtWidgets.QLineEdit(current_version or _DEFAULT_VERSION)
        self._version.setAccessibleName("Version number")
        self._version.setToolTip(_VERSION_HINT)
        self._version.setEnabled(False)
        self._change_version.toggled.connect(self._version.setEnabled)
        self._problem = QtWidgets.QLabel()
        self._problem.setWordWrap(True)
        self._problem.hide()
        self._buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        self._message.textChanged.connect(self._update_save_button)
        self._update_save_button()
        layout = QtWidgets.QVBoxLayout(self)
        for widget in (
            message_label,
            self._message,
            summary,
            listing,
            self._change_version,
            self._version,
            self._problem,
            self._buttons,
        ):
            layout.addWidget(widget)
        self._details: tuple[str, str | None] | None = None

    def _update_save_button(self) -> None:
        """Allow saving only once a message has been typed."""
        save = self._buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Save
        )
        save.setEnabled(bool(self._message.text().strip()))

    def _show_problem(self, message: str) -> None:
        """Explain why the form cannot be saved yet."""
        self._problem.setText(f"Problem: {message}")
        self._problem.show()

    def accept(self) -> None:
        """Validate the message and version, then close the dialog."""
        try:
            message = labels.validate_message(self._message.text())
        except ValueError as error:
            self._show_problem(str(error))
            self._message.setFocus()
            return
        version = self._current_version
        if self._change_version.isChecked():
            try:
                version = labels.validate_version(self._version.text().strip())
            except ValueError as error:
                self._show_problem(str(error))
                self._version.setFocus()
                return
        self._details = (message, version)
        super().accept()

    def details(self) -> tuple[str, str | None] | None:
        """Return the accepted message and version, or None if canceled."""
        return self._details


def ask_details(
    parent: QtWidgets.QWidget | None,
    current_version: str | None,
    documents: list[str],
) -> tuple[str, str | None] | None:
    """Show the save form; return the message and version, or None."""
    dialog = SaveDialog(parent, current_version, documents)
    dialog.exec()
    return dialog.details()

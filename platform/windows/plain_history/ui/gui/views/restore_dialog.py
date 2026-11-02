"""Confirm which documents a restore will replace or recreate."""

from PySide6 import QtWidgets

from plain_history.domains.snapshots import records

_ACTIONS = {
    records.RestoreAction.UNCHANGED: "No change",
    records.RestoreAction.REPLACE: "Replace the current file",
    records.RestoreAction.RECREATE: "Recreate the missing file",
}


def build_confirmation(
    parent: QtWidgets.QWidget | None,
    heading: str,
    actions: dict[str, records.RestoreAction],
    confirm_text: str,
) -> QtWidgets.QDialog:
    """Build the restore review without showing it; Cancel has focus."""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Restore")
    dialog.setMinimumWidth(520)
    title = QtWidgets.QLabel(heading)
    title.setWordWrap(True)
    plan = QtWidgets.QTreeWidget()
    plan.setAccessibleName("Restore plan")
    plan.setHeaderLabels(["Document", "What happens"])
    plan.setRootIsDecorated(False)
    for name, action in sorted(actions.items()):
        entry = QtWidgets.QTreeWidgetItem([name, _ACTIONS[action]])
        plan.addTopLevelItem(entry)
    plan.resizeColumnToContents(0)
    note = QtWidgets.QLabel(
        "Documents not in this snapshot are left alone. Restoring does not "
        "change saved history; save a snapshot afterward to record the "
        "result."
    )
    note.setWordWrap(True)
    buttons = QtWidgets.QDialogButtonBox()
    confirm = buttons.addButton(
        confirm_text, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole
    )
    cancel = buttons.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    confirm.setAutoDefault(False)
    cancel.setDefault(True)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.addWidget(title)
    layout.addWidget(plan, 1)
    layout.addWidget(note)
    layout.addWidget(buttons)
    cancel.setFocus()
    return dialog


def confirm_restore(
    parent: QtWidgets.QWidget | None,
    heading: str,
    actions: dict[str, records.RestoreAction],
    confirm_text: str,
) -> bool:
    """Show the restore review; return True only if the writer confirms."""
    dialog = build_confirmation(parent, heading, actions, confirm_text)
    return dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted

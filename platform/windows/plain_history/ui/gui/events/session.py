"""Answer window requests with repository operations for one writing folder."""

from pathlib import Path

from PySide6 import QtCore

from plain_history.adapters import (
    repository,
    snapshot_documents,
    snapshots,
    tracking,
)
from plain_history.domains.comparison import lines as text_diff
from plain_history.domains.snapshots import records
from plain_history.ui.gui.views import (
    compare_dialog,
    restore_dialog,
    save_dialog,
    tracking_dialog,
)
from plain_history.ui.gui.views.root_window.window import RootWindow

LAST_FOLDER_KEY = "last_folder"
_FAILURES = (OSError, ValueError)
_START_HISTORY = (
    "Start keeping history for {root}?\n\nThis adds a hidden .plain_history "
    "folder. Your documents are not changed."
)
_NO_DOCUMENTS = (
    "No documents are chosen for history yet, or none match your rules. "
    "Choose documents now?"
)
_NO_SNAPSHOTS = (
    "No snapshots yet. Choose documents, then select Save snapshot to record "
    "your first draft."
)


def _plural(count: int, noun: str) -> str:
    """Return a count with a singular or plural noun."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _calc_actions(
    plan: snapshot_documents.RestorePlan,
) -> dict[str, records.RestoreAction]:
    """Classify each planned document against its current contents."""
    return {
        name: records.calc_restore_action(saved, current)
        for name, (saved, current) in plan.items()
    }


class Session:
    """Hold the open writing folder and answer the window's requests.

    Each request gathers input through a dialog, calls an adapter, and then
    refreshes the window. Expected failures appear in the window's banner
    instead of interrupting the writer with a pop-up.
    """

    def __init__(self, window: RootWindow, settings: QtCore.QSettings) -> None:
        """Connect window signals; no folder is open until one is chosen."""
        self.window = window
        self._settings = settings
        self._root: Path | None = None
        window.open_folder_requested.connect(self.choose_folder)
        window.save_requested.connect(self.save_snapshot)
        window.choose_documents_requested.connect(self.choose_documents)
        window.activated.connect(self.refresh)
        window.history.snapshot_selected.connect(self.show_snapshot)
        snapshot = window.snapshot
        snapshot.compare_requested.connect(self.compare_document)
        snapshot.restore_file_requested.connect(self.restore_document)
        snapshot.restore_snapshot_requested.connect(self.restore_snapshot)

    @property
    def root(self) -> Path | None:
        """Return the open writing folder, or None before one is chosen."""
        return self._root

    def _open(self, root: Path) -> None:
        """Remember a valid folder and show its history."""
        self._root = root
        self._settings.setValue(LAST_FOLDER_KEY, str(root))
        self.window.show_folder(root)
        self.refresh()

    def open_last_folder(self) -> None:
        """Reopen the previous run's folder, or show the welcome page.

        A remembered folder that was moved or lost its history is skipped
        without asking to start history again.
        """
        saved = self._settings.value(LAST_FOLDER_KEY)
        if isinstance(saved, str) and saved:
            try:
                root = repository.load(Path(saved)).parent
            except _FAILURES:
                pass
            else:
                self._open(root)
                return
        self.window.show_welcome()

    def choose_folder(self) -> None:
        """Ask for a writing folder and open it."""
        chosen = self.window.ask_folder(self._root)
        if chosen is not None:
            self.open_folder(chosen)

    def open_folder(self, root: Path) -> None:
        """Open a writing folder, offering to start history if it has none.

        After starting history, ask which documents to keep history for.
        """
        root = root.resolve()
        is_new = not (root / repository.DIRECTORY).exists()
        if is_new and not self.window.ask_yes_no(
            "Start history", _START_HISTORY.format(root=root)
        ):
            return
        try:
            metadata = (
                repository.init(root) if is_new else repository.load(root)
            )
        except _FAILURES as error:
            self.window.show_error(str(error))
            return
        self.window.clear_message()
        self._open(metadata.parent)
        if is_new:
            self.choose_documents()

    def refresh(self) -> None:
        """Reload tracking and history so outside edits show up."""
        root = self._root
        if root is None:
            return
        try:
            rules = tracking.load(root)
            files = tracking.list_files(root, rules)
            saved = snapshots.load(root)
        except _FAILURES as error:
            self.window.show_error(str(error))
            return
        self.window.show_tracking(rules, len(files))
        self.window.history.show_snapshots(saved)
        if not saved:
            self.window.snapshot.show_placeholder(_NO_SNAPSHOTS)

    def show_snapshot(self, number: int) -> None:
        """Show one snapshot and whether each document changed since then."""
        if self._root is None:
            return
        try:
            snapshot, plan = snapshot_documents.prepare_restore(
                self._root, None, number
            )
        except _FAILURES as error:
            self.window.snapshot.show_placeholder(
                f"Snapshot {number} can't be shown. {error}"
            )
            return
        self.window.snapshot.show_snapshot(snapshot, _calc_actions(plan))

    def save_snapshot(self) -> None:
        """Ask for a message and version, then save the tracked documents."""
        root = self._root
        if root is None:
            return
        try:
            files = tracking.list_files(root, tracking.load(root))
            saved = snapshots.load(root)
        except _FAILURES as error:
            self.window.show_error(str(error))
            return
        if not files:
            if self.window.ask_yes_no("Choose documents", _NO_DOCUMENTS):
                self.choose_documents()
            return
        current = saved[-1].version if saved else None
        details = save_dialog.ask_details(self.window, current, files)
        if details is None:
            return
        message, version = details
        try:
            snapshot = snapshots.save(root, message, version, len(saved))
        except _FAILURES as error:
            self.window.show_error(f"Snapshot not saved. {error}")
            return
        self.window.show_notice(
            f"Saved snapshot {snapshot.number}: {snapshot.message} "
            f"({_plural(len(snapshot.files), 'document')})."
        )
        self.refresh()
        self.window.history.select_number(snapshot.number)

    def _match_files(self, rules: list[str]) -> list[str]:
        """List documents for edited rules; raise ValueError for bad rules."""
        root = self._root
        if root is None:
            return []
        return tracking.list_files(root, tracking.normalize_rules(root, rules))

    def choose_documents(self) -> None:
        """Edit tracking rules; changing them never creates a snapshot."""
        root = self._root
        if root is None:
            return
        try:
            rules = tracking.load(root)
        except _FAILURES as error:
            self.window.show_error(str(error))
            return
        edited = tracking_dialog.ask_rules(
            self.window, root, rules, self._match_files
        )
        if edited is None:
            return
        try:
            tracking.update(root, edited)
        except _FAILURES as error:
            self.window.show_error(f"Selection not saved. {error}")
            return
        self.window.show_notice("Document selection saved.")
        self.refresh()

    def compare_document(self, name: str) -> None:
        """Show how a document changed since the selected snapshot."""
        number = self.window.history.selected_number()
        if self._root is None or number is None:
            return
        try:
            snapshot, name, before = snapshot_documents.load(
                self._root, Path(name), number
            )
            current = snapshot_documents.read_current(self._root, name)
            changes = text_diff.format_diff(
                before.decode("utf-8"), (current or b"").decode("utf-8")
            )
        except UnicodeDecodeError:
            self.window.show_error("Compare works with UTF-8 text files only.")
            return
        except _FAILURES as error:
            self.window.show_error(str(error))
            return
        label = f"snapshot {snapshot.number} ({snapshot.message})"
        if current is None:
            summary = f"{name} is missing. Everything below was in {label}."
        elif before == current:
            summary, changes = f"{name} is the same as in {label}.", ""
        elif not changes:
            summary = (
                f"{name} has no line changes since {label}; only invisible "
                "characters such as line endings differ."
            )
        else:
            summary = f"Changes to {name} since {label}."
        compare_dialog.show_comparison(
            self.window, f"Compare {name}", summary, changes
        )

    def _restore(self, file: str | None) -> None:
        """Review and restore one document, or the whole selected snapshot."""
        number = self.window.history.selected_number()
        root = self._root
        if root is None or number is None:
            return
        try:
            snapshot, plan = snapshot_documents.prepare_restore(
                root, None if file is None else Path(file), number
            )
        except _FAILURES as error:
            self.window.show_error(str(error))
            return
        actions = _calc_actions(plan)
        changed = [
            name
            for name, action in actions.items()
            if action is not records.RestoreAction.UNCHANGED
        ]
        label = f"snapshot {snapshot.number}: {snapshot.message}"
        if not changed:
            self.window.show_notice(f"Already matches {label}. No changes.")
            return
        if file is None:
            heading = f"Restore documents from {label}?"
            confirm_text = f"Restore {_plural(len(changed), 'file')}"
        else:
            heading = f"Restore {changed[0]} from {label}?"
            confirm_text = "Restore file"
        if not restore_dialog.confirm_restore(
            self.window, heading, actions, confirm_text
        ):
            return
        try:
            completed = snapshot_documents.restore_files(root, plan)
        except _FAILURES as error:
            self.window.show_error(str(error))
        else:
            self.window.show_notice(
                f"Restored {_plural(len(completed), 'file')} from snapshot "
                f"{snapshot.number}. Save a snapshot to keep this as a new "
                "point in history."
            )
        self.refresh()

    def restore_document(self, name: str) -> None:
        """Restore one document from the selected snapshot after review."""
        self._restore(name)

    def restore_snapshot(self) -> None:
        """Restore every document in the selected snapshot after review."""
        self._restore(None)

"""Let a writer choose which documents snapshots include."""

from collections.abc import Callable
from pathlib import Path

from PySide6 import QtWidgets

MatchFiles = Callable[[list[str]], list[str]]

_INTRO = (
    "Snapshots save every document that matches these rules. A rule can be a "
    "single file or a pattern such as *.md; new files that match a pattern "
    "are included automatically. Removing a rule never deletes documents or "
    "saved history."
)


class TrackingDialog(QtWidgets.QDialog):
    """Edit tracking rules with a live list of the documents they match.

    The match_files callback lists matching documents for a set of rules and
    raises ValueError for a rule that cannot be used.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        root: Path,
        rules: list[str],
        match_files: MatchFiles,
    ) -> None:
        """Build the editor for the rules of one writing folder."""
        super().__init__(parent)
        self.setWindowTitle("Choose documents")
        self.resize(720, 460)
        self._root = root
        self._match_files = match_files
        self._rules = list(rules)
        intro = QtWidgets.QLabel(_INTRO)
        intro.setWordWrap(True)
        self._rule_list = QtWidgets.QListWidget()
        self._rule_list.setAccessibleName("Rules")
        self._rule_list.itemSelectionChanged.connect(self._update_remove)
        rules_label = QtWidgets.QLabel("&Rules")
        rules_label.setBuddy(self._rule_list)
        self._matches = QtWidgets.QListWidget()
        self._matches.setAccessibleName("Matching documents")
        self._matches_label = QtWidgets.QLabel()
        self._matches_label.setBuddy(self._matches)
        self._pattern = QtWidgets.QLineEdit()
        self._pattern.setPlaceholderText("*.md")
        self._pattern.setAccessibleName("Pattern")
        self._pattern.returnPressed.connect(self._add_pattern)
        self._remove = QtWidgets.QPushButton("&Remove rule")
        self._remove.clicked.connect(self._remove_selected)
        self._problem = QtWidgets.QLabel()
        self._problem.setWordWrap(True)
        self._problem.hide()
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(
            "Save selection"
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lists = QtWidgets.QHBoxLayout()
        lists.addLayout(self._build_rules_column(rules_label), 1)
        matches_column = QtWidgets.QVBoxLayout()
        matches_column.addWidget(self._matches_label)
        matches_column.addWidget(self._matches, 1)
        lists.addLayout(matches_column, 1)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(lists, 1)
        layout.addWidget(self._problem)
        layout.addWidget(buttons)
        self._refresh()

    def _build_rules_column(
        self, rules_label: QtWidgets.QLabel
    ) -> QtWidgets.QVBoxLayout:
        """Arrange the rule list with its add and remove controls."""
        add_files = QtWidgets.QPushButton("Add &files…")
        add_files.clicked.connect(self._add_files)
        add_folder = QtWidgets.QPushButton("Add f&older…")
        add_folder.clicked.connect(self._add_folder)
        add_pattern = QtWidgets.QPushButton("Add &pattern")
        add_pattern.clicked.connect(self._add_pattern)
        pattern_row = QtWidgets.QHBoxLayout()
        pattern_row.addWidget(self._pattern, 1)
        pattern_row.addWidget(add_pattern)
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(add_files)
        buttons.addWidget(add_folder)
        buttons.addStretch(1)
        buttons.addWidget(self._remove)
        column = QtWidgets.QVBoxLayout()
        column.addWidget(rules_label)
        column.addWidget(self._rule_list, 1)
        column.addLayout(pattern_row)
        column.addLayout(buttons)
        return column

    def _show_problem(self, message: str) -> None:
        """Explain why the last change could not be used."""
        self._problem.setText(f"Problem: {message}")
        self._problem.show()

    def _refresh(self) -> None:
        """Redraw both lists from the current rules."""
        self._rule_list.clear()
        self._rule_list.addItems(self._rules)
        matches = self._match_files(self._rules)
        self._matches.clear()
        self._matches.addItems(matches)
        noun = "document" if len(matches) == 1 else "documents"
        self._matches_label.setText(f"&Matching {noun} ({len(matches)})")
        self._update_remove()

    def _update_remove(self) -> None:
        """Enable Remove only while a rule is selected."""
        self._remove.setEnabled(bool(self._rule_list.selectedItems()))

    def _relative_rule(self, chosen: Path) -> str | None:
        """Convert a chosen path to a rule, or report one outside the folder."""
        try:
            return chosen.resolve().relative_to(self._root.resolve()).as_posix()
        except ValueError:
            self._show_problem(f"Choose files inside {self._root}.")
            return None

    def add_rules(self, new_rules: list[str]) -> bool:
        """Add rules and refresh matches; report and drop unusable rules."""
        candidate = list(dict.fromkeys([*self._rules, *new_rules]))
        try:
            self._match_files(candidate)
        except ValueError as error:
            self._show_problem(str(error))
            return False
        self._rules = candidate
        self._problem.hide()
        self._refresh()
        return True

    def _add_files(self) -> None:
        """Add one rule per file chosen in the writing folder."""
        chosen, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Add documents", str(self._root)
        )
        rules = [self._relative_rule(Path(path)) for path in chosen]
        if chosen and None not in rules:
            self.add_rules([rule for rule in rules if rule is not None])

    def _add_folder(self) -> None:
        """Add a rule covering every file inside a chosen folder."""
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Add every document in a folder", str(self._root)
        )
        if not chosen:
            return
        relative = self._relative_rule(Path(chosen))
        if relative is not None:
            self.add_rules(["**/*" if relative == "." else f"{relative}/**/*"])

    def _add_pattern(self) -> None:
        """Add the typed pattern and clear the field on success."""
        pattern = self._pattern.text().strip()
        if pattern and self.add_rules([pattern]):
            self._pattern.clear()

    def _remove_selected(self) -> None:
        """Remove the selected rules from the list."""
        selected = {entry.text() for entry in self._rule_list.selectedItems()}
        self._rules = [rule for rule in self._rules if rule not in selected]
        self._refresh()

    def rules(self) -> list[str]:
        """Return the rules as currently edited."""
        return list(self._rules)


def ask_rules(
    parent: QtWidgets.QWidget | None,
    root: Path,
    rules: list[str],
    match_files: MatchFiles,
) -> list[str] | None:
    """Show the rule editor; return the edited rules, or None if canceled."""
    dialog = TrackingDialog(parent, root, rules, match_files)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.rules()
    return None

"""Show how a saved document differs from its current contents."""

import re

from PySide6 import QtGui, QtWidgets

_ADDED = QtGui.QColor(46, 160, 67, 90)
_REMOVED = QtGui.QColor(248, 81, 73, 90)
_HUNK = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@.*")
_FILE_HEADERS = ("--- ", "+++ ")


def format_changes(diff_text: str) -> str:
    """Rewrite a unified diff into lines a writer can read.

    - Drop the before/after file header lines.
    - Replace each hunk header with "Near line N:" for the current file.
    - Mark lines with "- ", "+ ", or two spaces for unchanged context.
    """
    lines = diff_text.splitlines()
    while lines and lines[0].startswith(_FILE_HEADERS):
        lines.pop(0)
    formatted: list[str] = []
    for line in lines:
        hunk = _HUNK.fullmatch(line)
        if hunk:
            if formatted:
                formatted.append("")
            # An emptied file reports line 0; writers count from 1.
            formatted.append(f"Near line {max(1, int(hunk.group(1)))}:")
        else:
            formatted.append(f"{line[:1] or ' '} {line[1:]}")
    return "\n".join(formatted)


class _ChangeHighlighter(QtGui.QSyntaxHighlighter):
    """Tint added and removed lines; the +/- marks carry the meaning too."""

    def highlightBlock(self, text: str) -> None:
        """Style one line of formatted changes."""
        style = QtGui.QTextCharFormat()
        if text.startswith("Near line "):
            style.setFontWeight(QtGui.QFont.Weight.Bold)
        elif text.startswith("+ "):
            style.setBackground(_ADDED)
        elif text.startswith("- "):
            style.setBackground(_REMOVED)
        else:
            return
        self.setFormat(0, len(text), style)


class CompareDialog(QtWidgets.QDialog):
    """Show a summary and the formatted line changes, read-only."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        title: str,
        summary: str,
        diff_text: str,
    ) -> None:
        """Build the comparison; an empty diff shows only the summary."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(820, 560)
        heading = QtWidgets.QLabel(summary)
        heading.setWordWrap(True)
        self.changes = QtWidgets.QPlainTextEdit(format_changes(diff_text))
        self.changes.setReadOnly(True)
        self.changes.setAccessibleName("Changes")
        self._highlighter = _ChangeHighlighter(self.changes.document())
        # Qt defers the first pass to the event loop; apply it now instead.
        self._highlighter.rehighlight()
        legend = QtWidgets.QLabel(
            "Lines marked - were in the snapshot. "
            "Lines marked + are in the current file."
        )
        legend.setWordWrap(True)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(heading)
        if diff_text:
            layout.addWidget(legend)
            layout.addWidget(self.changes, 1)
        layout.addWidget(buttons)


def show_comparison(
    parent: QtWidgets.QWidget | None,
    title: str,
    summary: str,
    diff_text: str,
) -> None:
    """Show the comparison until the writer closes it."""
    CompareDialog(parent, title, summary, diff_text).exec()

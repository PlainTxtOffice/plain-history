"""Drive the desktop window through its session without opening dialogs."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtCore, QtWidgets

from plain_history.adapters import repository, snapshots, tracking
from plain_history.domains.snapshots import records
from plain_history.ui.gui.app import build_session
from plain_history.ui.gui.events import session as session_module
from plain_history.ui.gui.views import (
    compare_dialog,
    restore_dialog,
    save_dialog,
    tracking_dialog,
    timestamps,
)


@pytest.fixture(scope="module")
def qapp():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def settings(tmp_path):
    return QtCore.QSettings(
        str(tmp_path / "settings.ini"), QtCore.QSettings.Format.IniFormat
    )


@pytest.fixture
def folder(tmp_path):
    root = tmp_path / "writing"
    root.mkdir()
    (root / "chapter1.md").write_text("one\n", encoding="utf-8")
    (root / "chapter2.md").write_text("two\n", encoding="utf-8")
    repository.init(root)
    tracking.add(root, ["*.md"])
    return root


@pytest.fixture
def session(qapp, settings, folder):
    opened = build_session(settings)
    opened.open_folder(folder)
    return opened


def _save(root, message, version=None):
    count = len(snapshots.load(root))
    return snapshots.save(root, message, version, count)


def _texts(widget):
    return [widget.item(row).text() for row in range(widget.count())]


def test_calc_restore_action():
    action = records.calc_restore_action
    assert action(b"a", b"a") is records.RestoreAction.UNCHANGED
    assert action(b"a", None) is records.RestoreAction.RECREATE
    assert action(b"a", b"b") is records.RestoreAction.REPLACE


def test_saved_at_is_readable_and_tolerates_bad_text():
    assert " at " in timestamps.format_saved_at("2026-10-14T19:02:00+00:00")
    assert timestamps.format_saved_at("not a time") == "not a time"


def test_welcome_without_remembered_folder(qapp, settings):
    opened = build_session(settings)
    opened.open_last_folder()
    assert opened.root is None


def test_reopens_remembered_folder(qapp, settings, folder):
    build_session(settings).open_folder(folder)
    reopened = build_session(settings)
    reopened.open_last_folder()
    assert reopened.root == folder.resolve()


def test_new_folder_asks_before_starting_history(qapp, settings, tmp_path):
    root = tmp_path / "fresh"
    root.mkdir()
    opened = build_session(settings)
    opened.window.ask_yes_no = lambda *_: False
    opened.open_folder(root)
    assert not (root / ".plain_history").exists()
    assert opened.root is None


def test_new_folder_starts_history_then_chooses_documents(
    qapp, settings, tmp_path, monkeypatch
):
    root = tmp_path / "fresh"
    root.mkdir()
    (root / "notes.txt").write_text("idea", encoding="utf-8")
    asked = []

    def choose(_parent, _root, rules, match_files):
        asked.append(rules)
        assert match_files(["*.txt"]) == ["notes.txt"]
        return ["*.txt"]

    monkeypatch.setattr(tracking_dialog, "ask_rules", choose)
    opened = build_session(settings)
    opened.window.ask_yes_no = lambda *_: True
    opened.open_folder(root)
    assert asked == [[]]
    assert tracking.load(root) == ["*.txt"]
    assert opened.window.banner_text() == "Document selection saved."


def test_save_snapshot_records_message_and_keeps_version(
    session, folder, monkeypatch
):
    _save(folder, "first", "0.1.0")
    seen = {}

    def details(_parent, current, documents):
        seen.update(current=current, documents=documents)
        return "second", current

    monkeypatch.setattr(save_dialog, "ask_details", details)
    session.save_snapshot()
    saved = snapshots.load(folder)
    assert seen == {
        "current": "0.1.0",
        "documents": ["chapter1.md", "chapter2.md"],
    }
    assert [s.message for s in saved] == ["first", "second"]
    assert saved[-1].version == "0.1.0"
    assert session.window.history.selected_number() == 2
    assert "Saved snapshot 2" in session.window.banner_text()


def test_canceled_save_writes_nothing(session, folder, monkeypatch):
    monkeypatch.setattr(save_dialog, "ask_details", lambda *_: None)
    session.save_snapshot()
    assert snapshots.load(folder) == []


def test_save_without_documents_offers_to_choose(
    qapp, settings, tmp_path, monkeypatch
):
    root = tmp_path / "empty"
    root.mkdir()
    repository.init(root)
    opened = build_session(settings)
    opened.open_folder(root)
    questions = []
    opened.window.ask_yes_no = lambda title, _: questions.append(title)
    monkeypatch.setattr(
        save_dialog, "ask_details", pytest.fail
    )
    opened.save_snapshot()
    assert questions == ["Choose documents"]


def test_history_lists_newest_first_and_shows_changes(session, folder):
    _save(folder, "first")
    (folder / "chapter2.md").write_text("two, revised\n", encoding="utf-8")
    (folder / "chapter1.md").unlink()
    session.refresh()
    entries = _texts(session.window.history)
    assert entries[0].startswith("1. first")
    documents = session.window.snapshot._documents
    states = {
        documents.topLevelItem(row).text(0): documents.topLevelItem(row).text(1)
        for row in range(documents.topLevelItemCount())
    }
    assert states == {
        "chapter1.md": "Missing from the folder",
        "chapter2.md": "Edited since this snapshot",
    }


def test_compare_shows_line_changes(session, folder, monkeypatch):
    _save(folder, "first")
    (folder / "chapter2.md").write_text("two, revised\n", encoding="utf-8")
    session.refresh()
    shown = {}
    monkeypatch.setattr(
        compare_dialog,
        "show_comparison",
        lambda _parent, title, summary, changes: shown.update(
            title=title, summary=summary, changes=changes
        ),
    )
    session.compare_document("chapter2.md")
    assert shown["title"] == "Compare chapter2.md"
    assert "-two" in shown["changes"]
    assert "+two, revised" in shown["changes"]


def test_compare_rejects_binary_documents(session, folder, monkeypatch):
    (folder / "chapter1.md").write_bytes(b"\xff\xfe")
    _save(folder, "binary")
    session.refresh()
    monkeypatch.setattr(compare_dialog, "show_comparison", pytest.fail)
    session.compare_document("chapter1.md")
    assert "UTF-8" in session.window.banner_text()


def test_restore_snapshot_after_confirmation(session, folder, monkeypatch):
    _save(folder, "first")
    (folder / "chapter1.md").unlink()
    (folder / "chapter2.md").write_text("changed\n", encoding="utf-8")
    session.refresh()
    reviewed = {}

    def confirm(_parent, heading, actions, confirm_text):
        reviewed.update(heading=heading, actions=actions, button=confirm_text)
        return True

    monkeypatch.setattr(restore_dialog, "confirm_restore", confirm)
    session.restore_snapshot()
    assert reviewed["button"] == "Restore 2 files"
    assert reviewed["actions"] == {
        "chapter1.md": records.RestoreAction.RECREATE,
        "chapter2.md": records.RestoreAction.REPLACE,
    }
    assert (folder / "chapter1.md").read_text(encoding="utf-8") == "one\n"
    assert (folder / "chapter2.md").read_text(encoding="utf-8") == "two\n"
    assert "Restored 2 files" in session.window.banner_text()


def test_declined_restore_changes_nothing(session, folder, monkeypatch):
    _save(folder, "first")
    (folder / "chapter2.md").write_text("changed\n", encoding="utf-8")
    session.refresh()
    monkeypatch.setattr(restore_dialog, "confirm_restore", lambda *_: False)
    session.restore_document("chapter2.md")
    assert (folder / "chapter2.md").read_text(encoding="utf-8") == "changed\n"


def test_restore_reports_when_nothing_differs(session, folder, monkeypatch):
    _save(folder, "first")
    session.refresh()
    monkeypatch.setattr(restore_dialog, "confirm_restore", pytest.fail)
    session.restore_snapshot()
    assert "Already matches" in session.window.banner_text()


def test_save_dialog_validates_inside_the_form(qapp):
    dialog = save_dialog.SaveDialog(None, "1.0.0", ["a.md"])
    save = dialog._buttons.button(
        QtWidgets.QDialogButtonBox.StandardButton.Save
    )
    assert not save.isEnabled()
    dialog._message.setText("  revised  ")
    dialog._change_version.setChecked(True)
    dialog._version.setText("1.0")
    dialog.accept()
    assert dialog.details() is None
    assert dialog._problem.text().startswith("Problem: Use a semantic version")
    dialog._version.setText("1.1.0")
    dialog.accept()
    assert dialog.details() == ("revised", "1.1.0")


def test_save_dialog_keeps_version_when_unchecked(qapp):
    dialog = save_dialog.SaveDialog(None, "1.0.0", ["a.md"])
    dialog._message.setText("draft")
    dialog.accept()
    assert dialog.details() == ("draft", "1.0.0")


def test_tracking_dialog_reports_unusable_rules(qapp, folder):
    (folder / "notes").mkdir()

    def match(rules):
        return tracking.list_files(folder, tracking.normalize_rules(folder, rules))

    dialog = tracking_dialog.TrackingDialog(None, folder, ["*.md"], match)
    assert _texts(dialog._matches) == ["chapter1.md", "chapter2.md"]
    assert not dialog.add_rules(["../outside.md"])
    assert not dialog.add_rules(["notes"])
    assert "notes/**/*" in dialog._problem.text()
    assert dialog.rules() == ["*.md"]
    dialog._rule_list.setCurrentRow(0)
    dialog._remove_selected()
    assert dialog.rules() == []
    assert _texts(dialog._matches) == []


def test_restore_confirmation_defaults_to_cancel(qapp):
    dialog = restore_dialog.build_confirmation(
        None, "Restore?", {"a.md": records.RestoreAction.REPLACE}, "Restore file"
    )
    buttons = dialog.findChild(QtWidgets.QDialogButtonBox)
    cancel = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    assert cancel.isDefault()


def test_session_ignores_requests_before_a_folder_opens(qapp, settings):
    opened = build_session(settings)
    opened.save_snapshot()
    opened.choose_documents()
    opened.restore_snapshot()
    assert opened.root is None
    assert session_module.LAST_FOLDER_KEY not in settings.allKeys()


def test_changes_read_without_diff_jargon():
    raw = "--- before\n+++ after\n@@ -1,2 +1,2 @@\n-old\n+new\n same\n@@ -0,0 +0,0 @@"
    assert compare_dialog.format_changes(raw) == (
        "Near line 1:\n- old\n+ new\n  same\n\nNear line 1:"
    )

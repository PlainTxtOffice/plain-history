"""Verify comparisons and confirmed restorations against saved document bytes."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.adapters import repository, snapshots, tracking
from src.cli.app import app


@pytest.fixture
def writing(tmp_path, monkeypatch):
    repository.init(tmp_path)
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters/draft.md").write_bytes(b"Original\r\n")
    tracking.add(tmp_path, ["**/*.md"])
    snapshots.save(tmp_path, "Original draft", "0.1.0", 0)
    (tmp_path / "chapters/draft.md").write_bytes(b"Revised\n")
    snapshots.save(tmp_path, "Revised draft", "0.2.0", 1)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def state(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_diff_latest_and_selected_read_only(writing):
    runner = CliRunner()
    before = state(writing)
    result = runner.invoke(app, ["diff", "chapters/draft.md"])
    assert result.exit_code == 0, result.output
    assert "snapshot 2" in result.output
    assert "No changes." in result.output
    result = runner.invoke(app, ["diff", r"chapters\draft.md", "--version", "1"])
    assert result.exit_code == 0, result.output
    assert "-Original" in result.output
    assert "+Revised" in result.output
    assert state(writing) == before


def test_diff_line_endings_and_deleted_file(writing):
    file = writing / "chapters/draft.md"
    file.write_bytes(b"Revised\r\n")
    result = CliRunner().invoke(app, ["diff", "chapters/draft.md"])
    assert result.exit_code == 0
    assert "file bytes differ" in result.output
    file.unlink()
    result = CliRunner().invoke(app, ["diff", "chapters/draft.md"])
    assert result.exit_code == 0
    assert "Current file is missing" in result.output
    assert "-Revised" in result.output
    assert not file.exists()


@pytest.mark.parametrize("input_text", ["n\n", "\n", ""])
def test_restore_declined_or_aborted_preserves_files(writing, input_text):
    before = state(writing)
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "1"], input=input_text)
    assert result.exit_code == (1 if input_text == "" else 0), result.output
    assert state(writing) == before


def test_restore_confirmed_exact_bytes_without_history_change(writing):
    before = state(writing / ".plain_history")
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "1"], input="y\n")
    assert result.exit_code == 0, result.output
    assert "Replace the current file? [y/N]" in result.output
    assert "Restored chapters/draft.md from snapshot 1" in result.output
    assert (writing / "chapters/draft.md").read_bytes() == b"Original\r\n"
    assert state(writing / ".plain_history") == before
    assert "Use phist save" in result.output


def test_restore_missing_parents_and_explicit_root(writing, monkeypatch):
    (writing / "chapters/draft.md").unlink()
    (writing / "chapters").rmdir()
    child = writing / "elsewhere"
    child.mkdir()
    monkeypatch.chdir(child)
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "1", "--path", str(writing), "--yes"])
    assert result.exit_code == 0, result.output
    assert (writing / "chapters/draft.md").read_bytes() == b"Original\r\n"
    assert list(child.iterdir()) == []


def test_restore_already_matching_does_not_prompt(writing):
    before = state(writing)
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "2"])
    assert result.exit_code == 0
    assert "Already matches" in result.output
    assert state(writing) == before


@pytest.mark.parametrize("command", ["diff", "restore"])
@pytest.mark.parametrize("name,number", [("chapters/draft.md", "9"), ("never.md", "1"), ("../outside.md", "1"), (".plain_history/config.toml", "1")])
def test_invalid_selection_preserved(writing, command, name, number):
    before = state(writing)
    result = CliRunner().invoke(app, [command, name, "--version", number])
    assert result.exit_code == 1, result.output
    assert "Traceback" not in result.output
    assert state(writing) == before


@pytest.mark.parametrize("command", ["diff", "restore"])
@pytest.mark.parametrize("damage", ["changed", "missing"])
def test_damaged_saved_content_preserves_current(writing, command, damage):
    record = snapshots.load(writing)[0]
    object_path = writing / ".plain_history/objects" / record.files["chapters/draft.md"]
    if damage == "changed":
        object_path.write_bytes(b"damaged")
    else:
        object_path.unlink()
    before = state(writing)
    result = CliRunner().invoke(app, [command, "chapters/draft.md", "--version", "1"], input="y\n")
    assert result.exit_code == 1
    assert state(writing) == before


def test_binary_diff_rejected_but_restore_exact(writing):
    file = writing / "chapters/draft.md"
    file.write_bytes(b"\x00\xffSaved")
    snapshots.save(writing, "Binary content", None, 2)
    file.write_bytes(b"changed")
    result = CliRunner().invoke(app, ["diff", "chapters/draft.md"])
    assert result.exit_code == 1
    assert "UTF-8 text" in result.output
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "3", "-y"])
    assert result.exit_code == 0, result.output
    assert file.read_bytes() == b"\x00\xffSaved"


def test_restore_changed_during_prompt(writing, monkeypatch):
    file = writing / "chapters/draft.md"
    def confirm(*args, **kwargs):
        file.write_bytes(b"Changed during prompt")
        return True
    monkeypatch.setattr("src.cli.documents.typer.confirm", confirm)
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "1"])
    assert result.exit_code == 1
    assert "Document changed" in result.output
    assert file.read_bytes() == b"Changed during prompt"


def test_restore_failed_replace_preserves_current(writing, monkeypatch):
    before = state(writing)
    def fail_replace(self, destination):
        raise PermissionError("cannot replace")
    monkeypatch.setattr(Path, "replace", fail_replace)
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "1", "--yes"])
    assert result.exit_code == 1
    assert state(writing) == before


@pytest.mark.parametrize("command", ["diff", "restore"])
def test_linked_documents_rejected(writing, command):
    file = writing / "chapters/draft.md"
    file.unlink()
    target = writing / "other.md"
    target.write_bytes(b"keep")
    try:
        file.symlink_to(target)
    except OSError:
        pytest.skip("Creating symlinks requires platform privileges")
    result = CliRunner().invoke(app, [command, "chapters/draft.md", "--version", "1"], input="y\n")
    assert result.exit_code == 1
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("initialized", [False, True])
@pytest.mark.parametrize("command", ["diff", "restore"])
def test_no_history_or_setup(tmp_path, initialized, command):
    if initialized:
        repository.init(tmp_path)
    before = state(tmp_path)
    result = CliRunner().invoke(app, [command, "draft.md", "--version", "1", "-p", str(tmp_path)])
    assert result.exit_code == 1
    assert state(tmp_path) == before


def test_diff_does_not_fall_back_to_older_snapshot(writing):
    (writing / "chapters/draft.md").unlink()
    (writing / "other.md").write_bytes(b"other")
    snapshots.save(writing, "Different selection", None, 2)
    result = CliRunner().invoke(app, ["diff", "chapters/draft.md"])
    assert result.exit_code == 1
    assert "Snapshot 3 does not contain" in result.output
    result = CliRunner().invoke(app, ["diff", "chapters/draft.md", "--version", "1"])
    assert result.exit_code == 0
    assert "-Original" in result.output


@pytest.mark.parametrize("number", ["0", "-1", "0.1.0"])
@pytest.mark.parametrize("command", ["diff", "restore"])
def test_snapshot_number_validation(writing, command, number):
    before = state(writing)
    result = CliRunner().invoke(app, [command, "chapters/draft.md", "--version", number])
    assert result.exit_code == 2
    assert state(writing) == before


def test_restore_ctrl_c_during_confirmation(writing, monkeypatch):
    before = state(writing)
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt
    monkeypatch.setattr("src.cli.documents.typer.confirm", interrupt)
    result = CliRunner().invoke(app, ["restore", "chapters/draft.md", "--version", "1"])
    assert result.exit_code == 130
    assert state(writing) == before

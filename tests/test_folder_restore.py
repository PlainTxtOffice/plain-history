"""Exercise prompted and explicit whole-snapshot restoration."""

import pytest
from typer.testing import CliRunner

from src.adapters import repository, snapshot_content, snapshots, tracking
from src.cli.app import app


@pytest.fixture
def writing(tmp_path, monkeypatch):
    repository.init(tmp_path)
    for name in ["a.md", "b.md"]:
        (tmp_path / name).write_bytes(name.encode())
    tracking.add(tmp_path, ["*.md"])
    snapshots.save(tmp_path, "Original", "0.1.0", 0)
    (tmp_path / "a.md").write_bytes(b"New draft")
    (tmp_path / "b.md").unlink()
    (tmp_path / "extra.txt").write_bytes(b"keep extra")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def state(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_bare_restore_prompts_and_preserves_extras(writing):
    history_before = state(writing / ".plain_history")
    result = CliRunner().invoke(app, ["restore"], input="\ny\n")
    assert result.exit_code == 0, result.output
    assert "Snapshot number to restore [1]" in result.output
    assert "Replace: a.md" in result.output
    assert "Recreate: b.md" in result.output
    assert "Restore these files? [y/N]" in result.output
    assert "Restored 2 files from snapshot 1" in result.output
    assert (writing / "a.md").read_bytes() == b"a.md"
    assert (writing / "b.md").read_bytes() == b"b.md"
    assert (writing / "extra.txt").read_bytes() == b"keep extra"
    assert state(writing / ".plain_history") == history_before


@pytest.mark.parametrize("input_text", ["", "1\n", "1\n\n", "1\nn\n"])
def test_folder_restore_cancel_preserves_all(writing, input_text):
    before = state(writing)
    result = CliRunner().invoke(app, ["restore"], input=input_text)
    assert result.exit_code == (1 if input_text in ["", "1\n"] else 0)
    assert state(writing) == before


def test_prompt_retries_invalid_snapshot(writing):
    result = CliRunner().invoke(app, ["restore"], input="bad\n0\n9\n1\ny\n")
    assert result.exit_code == 0, result.output
    assert "No saved snapshot numbered 0" in result.output
    assert "No saved snapshot numbered 9" in result.output
    assert (writing / "a.md").read_bytes() == b"a.md"


def test_restore_one_file_prompts_for_snapshot(writing):
    result = CliRunner().invoke(app, ["restore", "a.md"], input="1\ny\n")
    assert result.exit_code == 0, result.output
    assert "Snapshot number to restore" in result.output
    assert "Restored a.md from snapshot 1" in result.output
    assert not (writing / "b.md").exists()


def test_explicit_folder_restore_can_skip_confirmation(writing):
    result = CliRunner().invoke(app, ["restore", "--version", "1", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Snapshot number to restore" not in result.output
    assert "Restore these files?" not in result.output
    assert (writing / "b.md").read_bytes() == b"b.md"


def test_yes_requires_explicit_snapshot(writing):
    before = state(writing)
    result = CliRunner().invoke(app, ["restore", "--yes"])
    assert result.exit_code == 1
    assert "Supply --version" in result.output
    assert state(writing) == before


def test_corrupt_later_object_fails_before_any_write(writing):
    record = snapshots.load(writing)[0]
    object_path = writing / ".plain_history/objects" / record.files["b.md"]
    object_path.write_bytes(b"damaged")
    before = state(writing)
    result = CliRunner().invoke(app, ["restore", "--version", "1"], input="y\n")
    assert result.exit_code == 1
    assert "damaged" in result.output
    assert state(writing) == before
    assert "Restore these files?" not in result.output


def test_all_destinations_rechecked_before_writing(writing, monkeypatch):
    def confirm(*args, **kwargs):
        (writing / "b.md").write_bytes(b"New edits")
        return True
    monkeypatch.setattr("src.cli.documents.typer.confirm", confirm)
    result = CliRunner().invoke(app, ["restore", "--version", "1"])
    assert result.exit_code == 1
    assert "Document changed" in result.output
    assert (writing / "a.md").read_bytes() == b"New draft"
    assert (writing / "b.md").read_bytes() == b"New edits"


def test_later_write_failure_reports_partial_result(writing, monkeypatch):
    original = snapshot_content.write_atomic
    def fail_second(path, content):
        if path.name == "b.md":
            raise PermissionError("cannot replace b.md")
        original(path, content)
    monkeypatch.setattr(snapshot_content, "write_atomic", fail_second)
    result = CliRunner().invoke(app, ["restore", "--version", "1", "--yes"])
    assert result.exit_code == 1
    assert "Files restored: 1 (a.md)" in result.output
    assert (writing / "a.md").read_bytes() == b"a.md"
    assert not (writing / "b.md").exists()


def test_empty_history_does_not_prompt(tmp_path, monkeypatch):
    repository.init(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["restore"])
    assert result.exit_code == 1
    assert "No snapshots saved yet" in result.output
    assert "Snapshot number to restore" not in result.output


def test_folder_restore_skips_matching_files(writing):
    (writing / "a.md").write_bytes(b"a.md")
    result = CliRunner().invoke(app, ["restore", "--version", "1"], input="y\n")
    assert result.exit_code == 0, result.output
    assert "Unchanged: a.md" in result.output
    assert "Restored 1 file from snapshot 1." in result.output

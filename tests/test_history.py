"""Verify history reporting and document filtering from saved records."""

import pytest
from typer.testing import CliRunner

from src.adapters import repository, snapshots, tracking
from src.cli.app import app


@pytest.fixture
def writing(tmp_path, monkeypatch):
    repository.init(tmp_path)
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters/one.md").write_bytes(b"first")
    tracking.add(tmp_path, ["**/*.md"])
    snapshots.save(tmp_path, "First draft", None, 0)
    (tmp_path / "other.md").write_bytes(b"other")
    snapshots.save(tmp_path, "More chapters", "0.1.0", 1)
    (tmp_path / "chapters/one.md").unlink()
    snapshots.save(tmp_path, "Latest draft", "1.0.0", 2)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_history_newest_first_and_read_only(writing):
    (writing / ".plain_history/tracking.json").write_text("invalid", encoding="utf-8")
    before = {p.relative_to(writing): p.read_bytes()
              for p in writing.rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, ["history"])
    assert result.exit_code == 0, result.output
    assert result.output.index("Snapshot 3") < result.output.index("Snapshot 2")
    assert result.output.index("Snapshot 2") < result.output.index("Snapshot 1")
    for record in snapshots.load(writing):
        assert f"Snapshot {record.number}: {record.message}" in result.output
        assert f"Saved at (UTC): {record.created_at}" in result.output
    assert "Version: none" in result.output
    assert "Version: 0.1.0" in result.output
    assert "Version: 1.0.0" in result.output
    assert "Files saved: 2" in result.output
    assert before == {p.relative_to(writing): p.read_bytes()
                      for p in writing.rglob("*") if p.is_file()}


@pytest.mark.parametrize("name", ["chapters/one.md", r"chapters\one.md", "./chapters/one.md"])
def test_history_deleted_file_and_unchanged_saves(writing, name):
    result = CliRunner().invoke(app, ["history", name])
    assert result.exit_code == 0, result.output
    assert "Snapshot 2: More chapters" in result.output
    assert "Snapshot 1: First draft" in result.output
    assert "Snapshot 3" not in result.output
    assert "Files saved: 2" in result.output


def test_history_no_matching_file(writing):
    result = CliRunner().invoke(app, ["history", "never-saved.md"])
    assert result.exit_code == 0
    assert "No saved snapshots contain: never-saved.md" in result.output
    assert "Snapshot 1" not in result.output


def test_history_explicit_root_and_empty_history(tmp_path, monkeypatch):
    metadata = repository.init(tmp_path)
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    runner = CliRunner()
    assert runner.invoke(app, ["history"]).exit_code == 1
    result = runner.invoke(app, ["history", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "No snapshots saved yet" in result.output
    assert not (metadata / "history.json").exists()


@pytest.mark.parametrize("name", ["../one.md", "C:/outside.md", ".plain_history/history.json"])
def test_history_rejects_outside_paths(writing, name):
    result = CliRunner().invoke(app, ["history", name])
    assert result.exit_code == 1
    assert "Use a relative file" in result.output


@pytest.mark.parametrize("payload", ["[", "{}", "[{}]"])
def test_history_invalid_records_preserved(tmp_path, payload):
    metadata = repository.init(tmp_path)
    file = metadata / "history.json"
    file.write_text(payload, encoding="utf-8")
    result = CliRunner().invoke(app, ["history", "-p", str(tmp_path)])
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert file.read_text(encoding="utf-8") == payload

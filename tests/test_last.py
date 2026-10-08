"""Verify latest snapshot reporting uses saved records without mutations."""

import pytest
from typer.testing import CliRunner

from src.adapters import repository, snapshots, tracking
from src.cli.app import app


def test_last_reports_saved_selection(tmp_path, monkeypatch):
    metadata = repository.init(tmp_path)
    (tmp_path / "old.md").write_bytes(b"old")
    tracking.add(tmp_path, ["*.md"])
    snapshots.save(tmp_path, "First", "0.1.0", 0)
    (tmp_path / "old.md").unlink()
    for name in ["z.md", "a.md"]:
        (tmp_path / name).write_bytes(b"latest")
    latest = snapshots.save(tmp_path, "Revised draft", "1.0.0", 1)
    (tmp_path / "a.md").unlink()
    (tmp_path / "new.md").write_bytes(b"not saved")
    (metadata / "tracking.json").write_text("invalid", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, ["last"])
    assert result.exit_code == 0, result.output
    assert "Last saved snapshot 2: Revised draft" in result.output
    assert f"Saved at (UTC): {latest.created_at}" in result.output
    assert "Version: 1.0.0" in result.output
    assert "Files saved: 2\n  a.md\n  z.md" in result.output
    assert "old.md" not in result.output
    assert "new.md" not in result.output
    assert before == {p.relative_to(tmp_path): p.read_bytes()
                      for p in tmp_path.rglob("*") if p.is_file()}


def test_last_explicit_root_without_version(tmp_path, monkeypatch):
    repository.init(tmp_path)
    (tmp_path / "draft.txt").write_bytes(b"draft")
    tracking.add(tmp_path, ["draft.txt"])
    snapshots.save(tmp_path, "Draft", None, 0)
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    runner = CliRunner()
    assert runner.invoke(app, ["last"]).exit_code == 1
    result = runner.invoke(app, ["last", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Version: none" in result.output
    assert "  draft.txt" in result.output


def test_last_no_snapshots(tmp_path):
    repository.init(tmp_path)
    result = CliRunner().invoke(app, ["last", "-p", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "No snapshots saved yet" in result.output
    assert not (tmp_path / ".plain_history/history.json").exists()


@pytest.mark.parametrize("payload", ["[", "{}", "[{}]"])
def test_last_invalid_history_preserved(tmp_path, payload):
    metadata = repository.init(tmp_path)
    file = metadata / "history.json"
    file.write_text(payload, encoding="utf-8")
    result = CliRunner().invoke(app, ["last", "-p", str(tmp_path)])
    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert file.read_text(encoding="utf-8") == payload

"""Exercise persistent document selection through the writer-facing CLI."""

import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.adapters import repository, tracking
from src.cli.app import app


def test_track_persists_and_matches(tmp_path, monkeypatch):
    metadata = repository.init(tmp_path)
    config = (metadata / "config.toml").read_bytes()
    (tmp_path / "chapter.md").write_text("draft", encoding="utf-8")
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "first.txt").write_text("note", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["track", "chapter.md", "notes/**/*.txt",
                                 "chapter.md", "future/*.md"])
    assert result.exit_code == 0, result.output
    assert "Matching files: 2" in result.output
    assert "No snapshot created" in result.output
    assert tracking.load(tmp_path) == ["chapter.md", "notes/**/*.txt", "future/*.md"]
    saved = (metadata / "tracking.json").read_bytes()
    assert runner.invoke(app, ["track", "chapter.md"]).exit_code == 0
    assert (metadata / "tracking.json").read_bytes() == saved
    (notes / "later.txt").write_text("new", encoding="utf-8")
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Matching files: 3" in result.output
    assert "notes/later.txt" in result.output
    assert (metadata / "tracking.json").read_bytes() == saved
    assert (metadata / "config.toml").read_bytes() == config
    assert list((metadata / "objects").iterdir()) == []


def test_globs_metadata_and_overlap(tmp_path):
    repository.init(tmp_path)
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.md").write_text("b", encoding="utf-8")
    assert tracking.list_files(tmp_path, ["*.md"]) == ["a.md"]
    assert tracking.list_files(tmp_path, ["**/*", "*.md"]) == ["a.md", "nested/b.md"]
    assert tracking.add(tmp_path, [r"nested\*.md"]) == ["nested/*.md"]


@pytest.mark.parametrize("pattern", ["../outside.md", "/outside.md",
    "C:outside.md", r"C:\outside.md", ".plain_history/config.toml",
    "nested/../a.md", "", ".", "bad**glob", "bad\x00file"])
def test_invalid_batch_is_not_saved(tmp_path, pattern):
    metadata = repository.init(tmp_path)
    tracking.add(tmp_path, ["old.md"])
    before = (metadata / "tracking.json").read_bytes()
    result = CliRunner().invoke(app, ["track", "new.md", pattern,
                                    "--path", str(tmp_path)])
    assert result.exit_code == 1, result.output
    assert (metadata / "tracking.json").read_bytes() == before


def test_explicit_root_and_missing_setup(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["track", "*.md", "-p", str(tmp_path)])
    assert result.exit_code == 1
    assert "phist init" in result.output
    assert list(tmp_path.iterdir()) == []
    repository.init(tmp_path)
    assert runner.invoke(app, ["track", "*.md", "-p", str(tmp_path)]).exit_code == 0
    assert tracking.load(tmp_path) == ["*.md"]
    assert runner.invoke(app, ["track", "-p", str(tmp_path)]).exit_code == 2


@pytest.mark.parametrize("content", ['[', '{}', '[1]', '["../outside"]'])
def test_invalid_tracking_is_preserved(tmp_path, content):
    metadata = repository.init(tmp_path)
    config = metadata / "tracking.json"
    config.write_text(content, encoding="utf-8")
    for command in [["check"], ["track", "*.md"]]:
        result = CliRunner().invoke(app, [*command, "-p", str(tmp_path)])
        assert result.exit_code == 1
        assert config.read_text(encoding="utf-8") == content


def test_directory_rule_is_rejected(tmp_path):
    metadata = repository.init(tmp_path)
    (tmp_path / "chapters").mkdir()
    with pytest.raises(ValueError, match="select files"):
        tracking.add(tmp_path, ["chapters"])
    assert not (metadata / "tracking.json").exists()


def test_symlinks_are_excluded(tmp_path):
    root = tmp_path / "writing"
    root.mkdir()
    repository.init(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("outside", encoding="utf-8")
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symlinks requires platform privileges")
    assert tracking.list_files(root, ["linked/*.md", "**/*"]) == []


def test_installed_cli_keeps_globs(tmp_path):
    repository.init(tmp_path)
    (tmp_path / "first.md").write_text("first", encoding="utf-8")
    executable = Path(sys.executable).with_name("phist.exe" if sys.platform == "win32" else "phist")
    result = subprocess.run([str(executable), "track", "*.md"], cwd=tmp_path,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert tracking.load(tmp_path) == ["*.md"]
    (tmp_path / "later.md").write_text("later", encoding="utf-8")
    assert tracking.list_files(tmp_path, tracking.load(tmp_path)) == ["first.md", "later.md"]

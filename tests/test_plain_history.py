"""Verify the starter's real behavior and explicit stub boundaries."""

import pytest
from typer.testing import CliRunner

from src.cli.app import app
from src.adapters import repository
from src.domains import diff


def test_init_preserves_documents_and_metadata(tmp_path):
    document = tmp_path / "chapter.md"
    document.write_text("Draft", encoding="utf-8")
    metadata = repository.init(tmp_path)
    marker = metadata / "objects" / "existing"
    marker.write_bytes(b"saved content")
    assert repository.init(tmp_path) == metadata
    assert document.read_text(encoding="utf-8") == "Draft"
    assert marker.read_bytes() == b"saved content"


def test_unknown_metadata_is_preserved(tmp_path):
    metadata = tmp_path / ".plain_history"
    metadata.mkdir()
    with pytest.raises(ValueError, match="No repository"):
        repository.init(tmp_path)
    assert list(metadata.iterdir()) == []


def test_cli_init_and_check(tmp_path):
    runner = CliRunner()
    assert runner.invoke(app, ["check", "-p", str(tmp_path)]).exit_code == 1
    assert runner.invoke(app, ["init", "-p", str(tmp_path)]).exit_code == 0
    result = runner.invoke(app, ["check", "-p", str(tmp_path)])
    assert result.exit_code == 0
    assert "History is set up for" in result.output
    assert str(tmp_path) in result.output


def test_text_diff():
    assert diff.format_diff("same", "same") == ""
    result = diff.format_diff("old", "new")
    assert "-old" in result
    assert "+new" in result


@pytest.mark.parametrize("initialized", [False, True])
def test_check_current_directory(tmp_path, monkeypatch, initialized):
    if initialized:
        repository.init(tmp_path)
    monkeypatch.chdir(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == (0 if initialized else 1)
    assert ("History is set up for" if initialized else "phist init") in result.output
    after = {p.relative_to(tmp_path): p.read_bytes()
             for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before
    assert (tmp_path / ".plain_history").exists() == initialized


def test_check_exact_root_and_path(tmp_path, monkeypatch):
    repository.init(tmp_path)
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    runner = CliRunner()
    assert runner.invoke(app, ["check"]).exit_code == 1
    result = runner.invoke(app, ["check", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert str(tmp_path) in result.output
    assert list(child.iterdir()) == []


@pytest.mark.parametrize("problem", ["config", "format", "objects", "toml"])
def test_check_invalid_setup(tmp_path, monkeypatch, problem):
    metadata = repository.init(tmp_path)
    config = metadata / "config.toml"
    if problem == "config":
        config.unlink()
    elif problem == "format":
        config.write_text("format_version = 2\n", encoding="utf-8")
    elif problem == "objects":
        (metadata / "objects").rmdir()
    else:
        config.write_text("format_version = [", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    result = CliRunner().invoke(app, ["check"])
    assert result.exit_code == 1
    assert result.output.strip()
    assert "Traceback" not in result.output
    assert {p.relative_to(tmp_path): p.read_bytes()
            for p in tmp_path.rglob("*") if p.is_file()} == before
    assert (metadata / "objects").exists() == (problem != "objects")

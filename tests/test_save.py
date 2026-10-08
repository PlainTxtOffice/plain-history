"""Verify interactive snapshot saves, version choices, and failed writes."""

import pytest
from typer.testing import CliRunner

from src.adapters import repository, snapshot_content, snapshots, tracking
from src.cli.app import app
from src.domains import history


@pytest.fixture
def writing(tmp_path, monkeypatch):
    repository.init(tmp_path)
    (tmp_path / "draft.md").write_bytes(b"First draft\r\n")
    tracking.add(tmp_path, ["*.md"])
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_message_then_optional_version(writing):
    result = CliRunner().invoke(app, ["save"], input="First draft\ny\n0.1.0\n")
    assert result.exit_code == 0, result.output
    assert result.output.index("Save message") < result.output.index("Apply a version")
    saved = snapshots.load(writing)
    assert len(saved) == 1
    assert saved[0].version == "0.1.0"
    assert saved[0].message == "First draft"
    content = writing / ".plain_history/objects" / saved[0].files["draft.md"]
    assert content.read_bytes() == b"First draft\r\n"
    assert (writing / "draft.md").read_bytes() == content.read_bytes()


def test_unversioned_keep_and_change(writing):
    runner = CliRunner()
    assert runner.invoke(app, ["save"], input="One\nn\n").exit_code == 0
    result = runner.invoke(app, ["save"], input="Two\ny\n1.0.0-beta.1+draft\n")
    assert result.exit_code == 0, result.output
    (writing / "draft.md").write_text("Revised", encoding="utf-8")
    result = runner.invoke(app, ["save"], input="Three\nn\n")
    assert result.exit_code == 0, result.output
    assert "Current version: 1.0.0-beta.1+draft" in result.output
    assert "Change the version number?" in result.output
    assert runner.invoke(app, ["save"], input="Four\ny\n1.0.0\n").exit_code == 0
    saved = snapshots.load(writing)
    assert [s.version for s in saved] == [None, "1.0.0-beta.1+draft", "1.0.0-beta.1+draft", "1.0.0"]
    assert [s.number for s in saved] == [1, 2, 3, 4]
    assert saved[0].files == saved[1].files
    assert saved[1].files != saved[2].files
    assert len(list((writing / ".plain_history/objects").iterdir())) == 2


def test_invalid_prompt_retries(writing):
    result = CliRunner().invoke(app, ["save"], input="   \nDraft\ny\n1.2\n01.2.3\n1.2.3\n")
    assert result.exit_code == 0, result.output
    assert "nonempty save message" in result.output
    assert result.output.count("Use a semantic version") == 2
    assert snapshots.load(writing)[0].version == "1.2.3"


@pytest.mark.parametrize("input_text", ["", "Draft\n", "Draft\ny\n"])
def test_cancel_leaves_no_snapshot(writing, input_text):
    metadata = writing / ".plain_history"
    before = {p.name: p.read_bytes() for p in metadata.iterdir() if p.is_file()}
    result = CliRunner().invoke(app, ["save"], input=input_text)
    assert result.exit_code == 1
    assert snapshots.load(writing) == []
    assert list((metadata / "objects").iterdir()) == []
    assert {p.name: p.read_bytes() for p in metadata.iterdir() if p.is_file()} == before


def test_message_argument_and_explicit_root(writing, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    result = CliRunner().invoke(app, ["save", "Given message", "-p", str(writing)], input="n\n")
    assert result.exit_code == 0, result.output
    assert "Save message:" not in result.output
    assert snapshots.load(writing)[0].message == "Given message"


@pytest.mark.parametrize("version", ["0.0.0", "1.2.3", "1.0.0-alpha.1", "1.0.0-0", "1.0.0-x-y+001", "1.0.0+001"])
def test_valid_semver(version):
    assert history.validate_version(version) == version


@pytest.mark.parametrize("version", ["1", "1.2", "v1.2.3", "01.2.3", "1.02.3", "1.2.03", "1.0.0-01", "1.0.0-a..b", "1.0.0+", "1.0.0-", "1.0.0+foo_bar", "1.0.0\n", "１.0.0"])
def test_invalid_semver(version):
    with pytest.raises(ValueError, match="semantic version"):
        history.validate_version(version)


def test_no_selection_does_not_prompt(writing):
    (writing / "draft.md").unlink()
    result = CliRunner().invoke(app, ["save"])
    assert result.exit_code == 1
    assert "No tracked files match" in result.output
    assert "Save message:" not in result.output
    assert not (writing / ".plain_history/history.json").exists()


def test_failed_history_write_preserves_prior(writing, monkeypatch):
    snapshots.save(writing, "First", "1.0.0", 0)
    metadata = writing / ".plain_history"
    before = (metadata / "history.json").read_bytes()
    (writing / "draft.md").write_bytes(b"Changed")
    original = snapshot_content.write_atomic
    def fail_history(path, content):
        if path.name == "history.json":
            raise OSError("write failed")
        original(path, content)
    monkeypatch.setattr(snapshot_content, "write_atomic", fail_history)
    result = CliRunner().invoke(app, ["save"], input="Second\ny\n2.0.0\n")
    assert result.exit_code == 1
    assert (metadata / "history.json").read_bytes() == before
    assert snapshots.load(writing)[0].version == "1.0.0"
    assert not (metadata / "save.lock").exists()


def test_lock_and_changed_history(writing):
    lock = writing / ".plain_history/save.lock"
    lock.write_text("busy", encoding="utf-8")
    with pytest.raises(ValueError, match="Another save"):
        snapshots.save(writing, "Draft", None, 0)
    assert lock.read_text(encoding="utf-8") == "busy"
    lock.unlink()
    snapshots.save(writing, "First", None, 0)
    with pytest.raises(ValueError, match="History changed"):
        snapshots.save(writing, "Stale", None, 0)
    assert len(snapshots.load(writing)) == 1
    assert not lock.exists()


@pytest.mark.parametrize("content", ["[", "{}", "[{}]", '[{"number": true}]'])
def test_corrupt_history_is_preserved(writing, content):
    file = writing / ".plain_history/history.json"
    file.write_text(content, encoding="utf-8")
    result = CliRunner().invoke(app, ["save"], input="Draft\nn\n")
    assert result.exit_code == 1
    assert file.read_text(encoding="utf-8") == content
    assert "Save message:" not in result.output


def test_later_files_and_removed_selection(writing):
    first = snapshots.save(writing, "First", None, 0)
    (writing / "later.md").write_bytes(b"\x00\xffLater")
    (writing / "ignored.txt").write_bytes(b"not selected")
    (writing / "draft.md").unlink()
    second = snapshots.save(writing, "Second", None, 1)
    assert list(first.files) == ["draft.md"]
    assert list(second.files) == ["later.md"]
    objects = writing / ".plain_history/objects"
    assert (objects / first.files["draft.md"]).read_bytes() == b"First draft\r\n"
    assert (objects / second.files["later.md"]).read_bytes() == b"\x00\xffLater"


def test_read_failure_leaves_history(writing, monkeypatch):
    saved = snapshots.save(writing, "First", None, 0)
    def fail_read(root, name):
        raise PermissionError("cannot read draft")
    monkeypatch.setattr(snapshot_content, "read_document", fail_read)
    result = CliRunner().invoke(app, ["save"], input="Second\nn\n")
    assert result.exit_code == 1
    assert snapshots.load(writing) == [saved]
    assert not (writing / ".plain_history/save.lock").exists()


def test_atomic_replace_failure(tmp_path, monkeypatch):
    path = tmp_path / "history.json"
    path.write_bytes(b"original")
    def fail_replace(self, destination):
        raise PermissionError("cannot replace")
    monkeypatch.setattr(type(path), "replace", fail_replace)
    with pytest.raises(PermissionError):
        snapshot_content.write_atomic(path, b"replacement")
    assert path.read_bytes() == b"original"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["history.json"]

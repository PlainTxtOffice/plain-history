---
last_updated: 2026-10-14
---

# Plain History

Plain History helps writers keep version history for plain-text documents. Track
the files you choose, save snapshots of your drafts, and compare or restore
previous versions.

The goal is to make version control approachable for writers with little or no
programming experience, using descriptive commands and documentation. You can
track a single document or a project organized into chapters, sections, and
subfolders.

## Download the Windows CLI

Download the CLI from
[GitHub releases](https://github.com/plaintxtoffice/plain-history/releases):

- **Installer:** `plain-history-cli-0.2.0-x64-setup.exe` installs the CLI.
  Select the option to add `phist` to PATH, then open a new terminal.
- **Portable:** `phist-0.2.0-windows-x64-portable.exe` runs without
  installation. You can rename it to `phist.exe`. From PowerShell in the folder
  containing it, run `./phist.exe --help`. Use `--path` to select a different
  writing folder.
- **License and checksums:** `LICENSE` contains the MIT license, and
  `SHA256SUMS.txt` lists checksums for the downloads.

Both CLI downloads run without a separate Python installation or a virtual
environment. The desktop window is not part of these downloads yet; run it from
source as described below.

## Quick start

Open a terminal in your writing folder, then run:

```powershell
phist init
phist track "*.md" "chapters/**/*.txt"
phist check
phist save
```

Replace the tracking patterns with files or patterns that match your documents.
Keep quotation marks around patterns. When saving, enter a short message and
choose whether to apply a version number. After editing your documents, run
`phist save` again to capture another draft.

For the portable download, replace `phist` with the path to its executable.
Every command accepts `--path FOLDER` or `-p FOLDER`; otherwise, it uses the
terminal's current folder.

## Commands

| Command | What it does |
| --- | --- |
| `phist init` | Sets up history in an existing writing folder. |
| `phist track "*.md"` | Selects files or patterns for future snapshots. |
| `phist check` | Checks setup and lists currently selected files. |
| `phist save` | Saves a snapshot with a message and an optional version label. |
| `phist last` | Shows the latest snapshot and its saved filenames. |
| `phist history` | Lists saved snapshots, newest first. |
| `phist diff "chapter.md"` | Compares a saved document with its current contents. |
| `phist restore` | Prompts for a snapshot and confirmation before restoring its files. |

Use `phist COMMAND --help` for help with any command. Run `phist save` before
restoring if you want to preserve your current draft.

## User manual

The [User Manual](docs/USER_MANUAL.md) explains the workflows in detail,
including:

- [File selection and glob patterns](docs/USER_MANUAL.md#glob-pattern-rules).
- [Prompt defaults](docs/USER_MANUAL.md#read-defaults-in-terminal-prompts).
- [Version numbering](docs/USER_MANUAL.md#choose-a-version-number).
- [Comparing documents](docs/USER_MANUAL.md#compare-a-saved-document-with-your-current-draft).
- [Restoring files](docs/USER_MANUAL.md#restore-files-from-a-saved-snapshot).
- [Troubleshooting](docs/USER_MANUAL.md#troubleshooting).

## Run or build from source

Each platform's application lives in its own folder under `platform/`. Windows
is implemented today; macOS and Linux versions are planned.

The `.venv/` setup below is for developers and anyone running or building Plain
History from source on Windows. Use Python 3.12 or newer. From the repository
folder in PowerShell:

```powershell
Set-Location platform/windows
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/phist.exe --help
```

Installing without `[dev]` installs only the application dependencies.
Virtual environment activation is optional. After activation, you can run
`phist` directly.

To open the desktop window, run `.venv/Scripts/phist-gui.exe`. Choose your
writing folder, choose the documents to keep history for, and use
**Save snapshot…** to save a draft. Select a snapshot to compare its documents
with your current draft or restore them. The window reopens your last folder
the next time it starts. See the
[User Manual](docs/USER_MANUAL.md#tour-the-desktop-window) for a tour.

See the [Nuitka build guide](platform/windows/scripts/nuitka/README.md) for
standalone and onefile CLI builds and the windowed desktop build, using the
project's virtual environment.

### Development checks

From `platform/windows/`:

```powershell
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check plain_history
.venv/Scripts/python.exe -m mypy plain_history
.venv/Scripts/rumdl.exe check
```

## License

Plain History is licensed under the [MIT License](LICENSE).
Copyright (c) 2026 Plain Text Office LLC.

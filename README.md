<!-- last_updated: 2026-11-09 -->
<!-- rumdl-disable MD033 MD041 -->
<p align="center">
  <img src="assets/icons/plain_history.svg" alt="Plain History icon: a document page with a folded corner" width="96">
</p>

<h1 align="center">Plain History</h1>

<p align="center">
  Version history for writers: save snapshots of your plain-text drafts, then
  compare or restore earlier versions.
</p>

<p align="center">
  <a href="https://github.com/PlainTxtOffice/plain-history/releases/latest"><img src="https://img.shields.io/github/v/release/PlainTxtOffice/plain-history?label=release" alt="Latest release"></a>
  <a href="#download"><img src="https://img.shields.io/badge/platform-Windows%20CLI-informational" alt="Platform: Windows command line"></a>
</p>

<p align="center">
  <a href="#download">Download</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/USER_MANUAL.md">User manual</a> ·
  <a href="docs/HISTORY_FORMAT.md">History format</a> ·
  <a href="https://plaintxtoffice.com/apps/">Website</a>
</p>
<!-- rumdl-enable MD033 MD041 -->

---

## About

Plain History helps writers keep version history for plain-text documents. Track
the files you choose, save snapshots of your drafts, and compare or restore
previous versions.

Keep a history of a single document or a project organized into chapters and
subfolders. Snapshots stay in your writing folder, so you can review earlier
drafts without an account or an online service.

Plain History is a command-line program for Windows. You run it from a
terminal; the downloads do not include a desktop window.

## Features

- Choose which files to track with file names or glob patterns.
- Save a snapshot with a message and an optional version label.
- List saved snapshots and see what the latest one contains.
- Compare a saved document with its current contents.
- Restore files from an earlier snapshot, with a confirmation first.

## Download

Plain History 0.3.0 for Windows x64:

| Download | File | Notes |
| --- | --- | --- |
| Installer | [plain-history-cli-0.3.0-x64-setup.exe](https://github.com/PlainTxtOffice/plain-history/releases/download/v0.3.0/plain-history-cli-0.3.0-x64-setup.exe) | Installs the CLI. Select the option to add `phist` to PATH, then open a new terminal. |
| Portable | [phist-0.3.0-windows-x64-portable.exe](https://github.com/PlainTxtOffice/plain-history/releases/download/v0.3.0/phist-0.3.0-windows-x64-portable.exe) | Runs without installation. You can rename it to `phist.exe`. |
| Checksums | [SHA256SUMS.txt](https://github.com/PlainTxtOffice/plain-history/releases/download/v0.3.0/SHA256SUMS.txt) | Checksums for both downloads. |

Both downloads run without a separate Python installation. macOS and Linux
downloads are not available.

The executables are unsigned. See the
[release notes](https://github.com/PlainTxtOffice/plain-history/releases/tag/v0.3.0)
for validation results and the installer limitations. To check a download,
compare the output of `Get-FileHash -Algorithm SHA256 PATH_TO_DOWNLOAD` with
`SHA256SUMS.txt`.

## Quick start

Open a terminal in your writing folder, then run:

```powershell
phist init
phist track "*.md" "chapters/**/*.txt"
phist check
phist save
```

Replace the tracking rules with files or patterns that match your documents.
Keep quotation marks around patterns. When saving, enter a short message and
choose whether to add a version label. After editing your documents, run
`phist save` again to capture another draft.

For the portable download, replace `phist` with the path to its executable,
for example `./phist.exe --help` from PowerShell in the folder containing it.
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

## User Manual

The [User Manual](docs/USER_MANUAL.md) explains the workflows in detail,
including:

- [File selection and glob patterns](docs/USER_MANUAL.md#glob-pattern-rules).
- [Prompt defaults](docs/USER_MANUAL.md#read-defaults-in-terminal-prompts).
- [Version labels](docs/USER_MANUAL.md#choose-a-version-label).
- [Comparing documents](docs/USER_MANUAL.md#compare-a-saved-document-with-your-current-draft).
- [Restoring files](docs/USER_MANUAL.md#restore-files-from-a-saved-snapshot).
- [Troubleshooting](docs/USER_MANUAL.md#troubleshooting).

The manual also describes the separately developed desktop window. Those
sections do not apply to the CLI downloads. The
[History Format](docs/HISTORY_FORMAT.md) documents how snapshots are stored in a
writing folder.

## Help and maintenance

Start with the [troubleshooting guide](docs/USER_MANUAL.md#troubleshooting) or
run `phist COMMAND --help`. For support, contact
[tripp@plaintxtoffice.com](mailto:tripp@plaintxtoffice.com). Include your
Windows version, the output of `phist --version`, the command you ran, and the
error message. Do not include private documents.

Plain History is maintained by **Plain Text Office LLC**. This repository
contains documentation and release downloads. Application source and build
scripts are not distributed here.

## License

Plain History is proprietary software. See [LICENSE](LICENSE) for terms.
Copyright (c) 2026 Plain Text Office LLC.

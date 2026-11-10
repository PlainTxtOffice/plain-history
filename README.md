---
last_updated: 2026-11-09
---

# Plain History

Plain History helps writers keep version history for plain-text documents. Track
the files you choose, save snapshots of your drafts, and compare or restore
previous versions.

Keep a history of a single document or a project organized into chapters and
subfolders. Snapshots stay in your writing folder, so you can review earlier
drafts without an account or an online service.

## Download the Windows CLI

Download **Plain History 0.3.0 for Windows x64** from the
[release page](https://github.com/plaintxtoffice/plain-history/releases/tag/v0.3.0):

- **Installer:** `plain-history-cli-0.3.0-x64-setup.exe` installs the CLI.
  Select the option to add `phist` to PATH, then open a new terminal.
- **Portable:** `phist-0.3.0-windows-x64-portable.exe` runs without
  installation. You can rename it to `phist.exe`. From PowerShell in the folder
  containing it, run `./phist.exe --help`. Use `--path` to select a different
  writing folder.
- **License and checksums:** `LICENSE` contains the proprietary license, and
  `SHA256SUMS.txt` lists checksums for the downloads.

Both downloads run without a separate Python installation. They are terminal
applications; the desktop window is not included. macOS and Linux downloads are
not available.

The executables are unsigned. See the release notes for validation results and
the installer limitations. To check a download, compare the output of
`Get-FileHash -Algorithm SHA256 PATH_TO_DOWNLOAD` with `SHA256SUMS.txt`.

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

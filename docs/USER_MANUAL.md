---
last_updated: 2026-10-07
version: 3.1.0
product_version: "0.1.0"
generated_from: "dev-docs/specs/USER_MANUAL_SPEC.instructions.md"
---

# User Manual

## Overview

Plain History is a version history program for writers and plain-text documents.
Version 0.1.0 can initialize a writing folder, remember which files you want to
track, show the current selection, save snapshots with optional semantic version
labels, browse saved history, and compare or restore documents. It offers
terminal commands and, when running from source, a small desktop status window.
Installation and environment setup are not covered here.
<!-- Verified from: pyproject.toml [project]; src/cli/app.py; src/gui/app.py -->

Tracking selects documents; `phist save` saves their contents. You can compare a
saved UTF-8 document with its current contents and restore one file or all files
recorded in a saved snapshot.
<!-- Verified from: src/cli/app.py [save, history, track]; src/cli/documents.py [diff, restore]; src/adapters/snapshots.py -->

## Starting the Program

### Open terminal help

For the installed CLI, run:

```powershell
phist --help
```

For the portable CLI, run its executable with `--help`, such as
`./phist.exe --help`. From the source project folder, you can run:

```powershell
.venv/Scripts/python.exe -m src.main --help
```

These commands display the available commands. Running without a command also
displays help. Commands finish and return you to the terminal; there is no
interactive phist session to quit. For the examples below, you can replace
`phist` with `.venv/Scripts/python.exe -m src.main` when running from the
project folder.
<!-- Verified from: pyproject.toml [project.scripts]; src/main.py; src/cli/app.py [app, main]; scripts/nuitka/onefile.ps1 -->

### Cancel a terminal command with Ctrl+C

While a phist command is running or waiting for an answer, hold **Ctrl** and
press **C** to interrupt it. At a save prompt, this cancels the command and
returns you to your terminal prompt. You can then run another command or try
`phist save` again.

If you cancel while entering the save message or choosing a version, no snapshot
is created and your existing history is unchanged. Your answers from that
attempt are discarded. Ctrl+C interrupts the running command; it does not undo
an earlier completed save.
<!-- Verified from: src/cli/save.py [read_details]; src/cli/app.py [save] -->

Each phist command is a separate run, so there is no ongoing phist session to
close after it finishes. Ctrl+C cancels the active command; it leaves the
terminal window open. Use your terminal's close button when you want to close
the window itself.
<!-- Verified from: src/cli/app.py [app, main]; src/main.py -->

### Open the desktop window

The desktop window is available when running from source. The Windows CLI
downloads do not include it. From the project folder, run:

```powershell
.venv/Scripts/python.exe -m src.gui.app
```

The equivalent command in a source installation is:

```powershell
phist-gui
```

The **plain_history** window checks the current working directory. It displays
either `Repository:` followed by the writing folder or an initialization error.
Close the window using its title-bar close button to quit.
<!-- Verified from: pyproject.toml [project.gui-scripts]; src/gui/app.py [main, build_window]; scripts/nuitka/standalone.ps1; scripts/nuitka/onefile.ps1 -->

## Getting Around

The terminal command structure is:

```text
phist COMMAND [arguments] [options]
```

Use `phist COMMAND --help` for help with one command, such as
`phist track --help`. Put `--path` after the command to select a writing folder.
Without it, phist uses your current directory; it does not search parent folders
for an existing setup.
<!-- Verified from: src/cli/options.py [Root]; src/cli/app.py [app]; src/adapters/repository.py [load, init] -->

| Interface | What you can do |
| --- | --- |
| Terminal | Initialize a writing folder, add tracking rules, review matches, save snapshots, browse saved history, compare drafts, and restore documents. |
| Desktop | Read the current folder's initialization status at launch. |

The desktop window has no document list, tracking controls, menus, or snapshot
controls. Its message reads
`Starter interface. Snapshot browsing and editing are not implemented.` Use the
terminal for the working tasks below.
<!-- Verified from: src/cli/app.py [init, track, check, save]; src/gui/app.py [build_window] -->

## Everyday Tasks

### Initialize a writing folder

Prerequisite: the writing folder already exists. In this example, it is
`C:/writing/my_book`.

1. Run `phist init --path C:/writing/my_book`.
1. Look for `Repository ready:` followed by the new `.plain_history` location.
1. Run `phist check --path C:/writing/my_book` to review the setup.

Initialization creates history metadata without changing your documents. Running
`init` again validates the existing setup and preserves it. If an existing
`.plain_history` folder is incomplete or unsupported, initialization reports an
error instead of replacing it.
<!-- Verified from: src/cli/app.py [init, check]; src/adapters/repository.py [init, load] -->

### Select documents for future snapshots

Prerequisite: initialize the writing folder first.

1. Choose individual files or glob patterns relative to the writing folder.
1. Run a command such as:

   ```powershell
   phist track "chapter.md" "notes/*.txt" "chapters/**/*.md" --path C:/writing/my_book
   ```

1. Review `Tracking rules:` and `Matching files:` in the output.
1. Look for `Selection saved. No snapshot created.`

Quote patterns so your shell passes them unchanged. Multiple files and patterns
can be added in one command. Rules persist between runs; repeating the same
normalized rule does not add another copy. A file matched by multiple rules
appears only once in the results.
<!-- Verified from: src/cli/app.py [track, _show_tracking, main]; src/adapters/tracking.py [add, list_files] -->

| Rule | Selection |
| --- | --- |
| `chapter.md` | One file in the writing folder. |
| `notes/scene 1.txt` | One file whose name includes spaces; quote the argument. |
| `*.md` | Matching files directly in the writing folder. |
| `notes/*.txt` | Matching files directly inside `notes/`. |
| `chapters/**/*.md` | Matching files in `chapters/` and its subfolders. |
| `chapters/**/*` | All matching files in `chapters/` and its subfolders. |
<!-- Verified from: src/adapters/tracking.py [list_files]; src/domains/tracking.py [normalize_pattern] -->

Rules can match any file extension. A rule that currently matches nothing is
retained, so files created later can join the selection. A bare directory such
as `chapters` is rejected by `track`; use `chapters/**/*` instead.
<!-- Verified from: src/adapters/tracking.py [add, list_files] -->

Selection rules cannot be absolute paths or contain `..` path components. The
`**` wildcard must occupy a whole path component. Empty rules, control
characters, colons, and explicit `.plain_history` path components are rejected.
History metadata, symbolic links, and junctions are excluded from the
selection. If any rule in an added batch is invalid, the saved rule list is left
unchanged.
<!-- Verified from: src/domains/tracking.py [normalize_pattern]; src/adapters/tracking.py [add, list_files] -->

### Glob pattern rules

A glob selects filenames by a pattern. Give each rule as a separate quoted
argument to `phist track`, for example:

```powershell
phist track "chapter?.md" "notes/*.txt" "chapters/**/*.md"
```

Rules start at your writing folder, selected by the current directory or
`--path`. Use `/` between folders. Windows backslashes are also accepted and
stored as `/`; they do not escape wildcard characters. A leading `./` and
repeated separators are normalized away. Spaces are part of the filename, so
quote a rule such as `"notes/scene 1.txt"`.
<!-- Verified from: src/cli/app.py [Root, track, main]; src/domains/tracking.py [normalize_pattern] -->

| Pattern syntax | Meaning | Example |
| --- | --- | --- |
| Plain filename | Select that file relative to the writing folder. | `chapter.md` selects one file. |
| `*` | Match zero or more characters within one filename or folder name. | `notes/*.txt` selects text files directly in `notes/`. |
| `?` | Match exactly one character within a name. | `chapter?.md` matches `chapter1.md` and `chapterA.md`, but not `chapter10.md`. |
| `[abc]` | Match one character from the listed choices. | `chapter[12].md` matches `chapter1.md` or `chapter2.md`. |
| `[a-z]` | Match one character in a range. | `chapter[0-9].md` matches a single digit after `chapter`. |
| `[!abc]` | Match one character outside the listed choices or range. | `chapter[!0-9].md` matches `chapterA.md`, but not `chapter1.md`. |
| `**` as a whole path component | Match zero or more levels of folders. | `chapters/**/*.md` includes Markdown files directly in `chapters/` and deeper subfolders. |
<!-- Verified from: src/adapters/tracking.py [list_files]; src/domains/tracking.py [normalize_pattern] -->

`*`, `?`, and bracket expressions never cross a folder separator. Only `**`
provides recursive matching, and it must stand alone between separators:
`chapters/**/*.md` is valid; `chapter**.md` is rejected. Use `**/*` for all
files in the writing folder and its subfolders, or `chapters/**/*` for all files
under `chapters/`. Only files enter the selection; directories themselves are
not saved.
<!-- Verified from: src/domains/tracking.py [normalize_pattern]; src/adapters/tracking.py [list_files] -->

Matching follows the platform's default case rules: on Windows, `*.md` also
matches `DRAFT.MD`; on platforms with case-sensitive matching, these differ.
Files whose names begin with a dot can match ordinary patterns: `*.md` includes
`.draft.md`. No file extension is required or automatically excluded. However,
`.plain_history` metadata, symbolic links, junctions, and files outside the
writing folder are always excluded.
<!-- Verified from: src/adapters/tracking.py [list_files] -->

Rules combine to include matching files. Repeated or overlapping rules select
each file only once. There are no exclusion rules: a leading `!` is an ordinary
filename character, not an instruction to remove matches. Brace alternatives
such as `*.{txt,md}` are not expanded; use two rules, `"*.txt" "*.md"`. A tilde
does not select your home folder. To match a literal opening bracket, use `[[]`:
`scene[[]1].txt` selects a file named `scene[1].txt`.
<!-- Verified from: src/adapters/tracking.py [add, list_files]; src/domains/tracking.py [normalize_pattern] -->

Absolute paths, drive paths, `..` components, colons, control characters, empty
rules, and explicit `.plain_history` components are rejected. An existing folder
name supplied by itself is also rejected; add a glob such as `/**/*`. Rules that
match nothing are retained for future files. Run `phist check` to preview the
combined selection before `phist save` captures the currently matching files.
<!-- Verified from: src/domains/tracking.py [normalize_pattern]; src/adapters/tracking.py [add, list_files]; src/cli/app.py [check, save] -->

### Check setup and review the selection

1. Run `phist check --path C:/writing/my_book`.
1. Confirm the folder shown after `History is set up for:`.
1. Review the saved rules, matching-file count, and file list.

With no tracking rules, phist displays
`None yet. Use phist track "*.md" to select documents.` Matching files are
listed relative to the writing folder in sorted order. The list is recalculated
each time, including new files that match saved rules. Checking does not change
documents or history metadata, and it does not identify edits since a previous
snapshot.
<!-- Verified from: src/cli/app.py [check, _show_tracking]; src/adapters/tracking.py [load, list_files] -->

### Save a snapshot with a message and optional version

Prerequisite: initialize your writing folder and use `track` to select at least
one currently matching file.

1. Run `phist save --path C:/writing/my_book`.
1. At `Save message:`, describe the draft, for example `Reworked the opening`.
1. If no version exists, answer `Apply a version number?`. Otherwise, read
   `Current version:` and answer `Change the version number?`.
1. Answer yes to enter a version at `Version (MAJOR.MINOR.PATCH)`. Answer no or
   press Enter to keep the existing version, or to leave the snapshot without a
   version label if none exists.
1. Look for `Saved snapshot` followed by its number and message, then
   `Files saved:` and `Version:`.
<!-- Verified from: src/cli/app.py [save]; src/cli/save.py [read_details, _read_message, _read_version]; src/adapters/snapshots.py [save, list_selection] -->

A message cannot be empty or contain only whitespace. If the message is invalid,
the command asks you to enter it again.
`phist save "Reworked the opening"` supplies the message directly and proceeds
to the version question. A folder with no matching files is rejected before the
prompts.
<!-- Verified from: src/domains/history.py [validate_message]; src/cli/save.py [_read_message]; src/cli/app.py [save]; src/adapters/snapshots.py [list_selection] -->

Version labels use `MAJOR.MINOR.PATCH`, such as `0.1.0` or `1.2.3`. Each
component is a nonnegative integer without leading zeroes. Optional prerelease
and build labels are accepted, such as `1.0.0-beta.1+draft`. Numeric prerelease
identifiers cannot have leading zeroes. `1.2`, `v1.2.3`, and `01.2.3` are
invalid. See [Semantic Versioning 2.0.0](https://semver.org/) for the version
syntax.
<!-- Verified from: src/domains/history.py [validate_version] -->

The default version is `0.1.0` when assigning a version for the first time, or
the current version when one exists. If a version is invalid, the command asks
you to enter it again. Plain History does not automatically increment the label.
The label belongs to the whole snapshot; it does not edit version text inside
documents or change the program's own version.
<!-- Verified from: src/cli/save.py [_read_version]; src/adapters/snapshots.py [_write_snapshot]; src/domains/history.py [Snapshot] -->

Every successful save has a separate snapshot number, even if the message,
version, or file contents are unchanged. The current version comes from the last
successful save. Each snapshot retains its own version label and selected files.
A later save captures the current tracked selection and leaves earlier snapshots
unchanged.
<!-- Verified from: src/cli/app.py [save]; src/adapters/snapshots.py [load, _write_snapshot]; src/adapters/snapshot_content.py [write_objects] -->

On Windows, press **Ctrl+C** to cancel while answering prompts; end-of-input
also cancels. No snapshot is created until the prompts finish. Saving copies
exact document bytes without editing the originals. If a file cannot be read or
history cannot be written, the command reports an error rather than a successful
save; existing history remains unchanged.
<!-- Verified from: src/cli/save.py [read_details]; src/cli/app.py [save]; src/adapters/snapshots.py [save, _write_snapshot]; src/adapters/snapshot_content.py [read_document, write_atomic] -->

### View the last saved snapshot

Run `phist last` from your writing folder, or select another folder with
`phist last --path C:/writing/my_book`.

The command shows the latest successful snapshot's number, save message,
save date and time in UTC, optional version label, and file count. It then
lists the saved filenames in alphabetical order, relative to the writing folder.
`Version: none` means the snapshot has no version label.
<!-- Verified from: src/cli/app.py [last]; src/adapters/snapshots.py [load] -->

These are the files recorded when that snapshot was saved. A file still appears
if you have since renamed or deleted it. Newly created files appear only after
a later save includes them. Use `phist check` to see the current tracked
selection; use `phist last` to see what the most recent save captured.
<!-- Verified from: src/cli/app.py [last, check]; src/adapters/snapshots.py [load] -->

If there are no snapshots, the command reports
`No snapshots saved yet. Use phist save to save a draft.` Missing setup or
unreadable history produces an error. The command reads saved records without
changing your documents or history. It lists filenames, not document contents.
<!-- Verified from: src/cli/app.py [last, _repository_path]; src/adapters/snapshots.py [load] -->

### Browse saved history

Run `phist history` from your writing folder to list every saved snapshot,
newest first. Each entry shows its snapshot number, save message, date and time
in UTC, optional version label, and the total number of files in that snapshot.
`Version: none` means that save has no version label.
<!-- Verified from: src/cli/app.py [history]; src/cli/history.py [show] -->

To find saves containing one document, pass its relative filename:

```powershell
phist history "chapters/one.md"
phist history "chapters/one.md" --path C:/writing/my_book
```

The filename is relative to the writing folder, even when you use `--path`.
Forward slashes and Windows backslashes are accepted. Match a specific saved
path; glob patterns are not expanded here. Filename comparison follows the
platform's path case rules, so it ignores case on Windows.
<!-- Verified from: src/cli/app.py [history, Root]; src/cli/history.py [show]; src/domains/tracking.py [normalize_pattern] -->

Filtered history includes every snapshot containing that filename, including
saves where its contents were unchanged. You can look up a file that has since
been deleted. Renamed files have separate paths; use the old name to find saves
under that name. The file count still describes the entire snapshot, not just
the document used as a filter.
<!-- Verified from: src/cli/history.py [show]; src/adapters/snapshots.py [load] -->

With no saves, the command reports `No snapshots saved yet.` With no matching
saved filename, it reports `No saved snapshots contain:` followed by the path.
Both are successful read-only results. Missing setup, invalid paths, or
unreadable history produce an error. Your documents and history are unchanged.
<!-- Verified from: src/cli/app.py [history, _repository_path]; src/cli/history.py [show] -->

Use `phist last` when you want the latest snapshot's full file list. `history`
shows snapshot summaries. Use the snapshot numbers it displays with `diff` and
`restore`; these numbers are separate from semantic version labels.
<!-- Verified from: src/cli/app.py [last, history]; src/cli/history.py [show]; src/cli/documents.py [diff, restore] -->

### Compare a saved document with your current draft

Run `phist diff "chapter.md"` from your writing folder. It compares the file in
the latest whole-folder snapshot with the file currently on disk. To choose an
earlier save, run `phist diff "chapter.md" --version 2`. Here, `2` is a snapshot
number from `phist history`, not a semantic label such as `0.1.0`.
<!-- Verified from: src/cli/documents.py [diff]; src/adapters/snapshot_documents.py [load] -->

The output identifies the file and snapshot being compared. In the comparison:

- `--- before` identifies the saved text, and `+++ after` identifies current
  text.
- Lines beginning with `-` were removed from the saved text.
- Lines beginning with `+` were added in the current draft.
- Lines beginning with a space provide unchanged context.
- Lines beginning with `@@` identify the line ranges shown.
<!-- Verified from: src/domains/diff.py [format_diff]; src/cli/documents.py [diff] -->

`No changes.` means the current bytes match the saved bytes. Comparison is
line-based and ignores line terminators. If only line endings or the final
newline differ, phist reports that there are no text line changes but the file
bytes differ. A missing current file is reported and compared as empty text,
showing the saved text as removed. An empty saved file that is now missing is
also reported as missing.
<!-- Verified from: src/cli/documents.py [diff]; src/domains/diff.py [format_diff] -->

Diff requires UTF-8 text on both sides. Other encodings produce an error rather
than a comparison. It does not change your documents or history. The filename
must exist in the selected snapshot; phist does not fall back to an earlier save
when the latest snapshot does not contain it. Use `history "chapter.md"` to
find a suitable snapshot number.
<!-- Verified from: src/cli/documents.py [diff]; src/adapters/snapshot_documents.py [load] -->

### Restore files from a saved snapshot

Run `phist restore` to restore all files recorded in a saved snapshot. The
command guides you through choosing and reviewing a save:

1. Read the saved history shown, newest first.
1. At `Snapshot number to restore [2]:`, enter a snapshot number or press Enter
   to accept the displayed default. The default is the latest snapshot number;
   `2` is only an example. If a number is invalid, the command asks you to enter
   it again.
1. Review the writing folder, snapshot number, save message, version label, and
   the action listed beside each filename: `Replace`, `Recreate`, or
   `Unchanged`.
1. At `Restore these files? [y/N]:`, type `y` and press Enter to proceed. Press
   Enter or answer `n` to cancel without changing files.
1. Look for the number of files restored and the snapshot number.
<!-- Verified from: src/cli/documents.py [_choose_snapshot, _show_plan, restore]; src/adapters/snapshot_documents.py [prepare_restore, restore_files] -->

To restore just one document, run `phist restore "chapter.md"`. History is
filtered to saves containing that filename, and the command asks for a snapshot
number. You can also choose the snapshot in the command itself:

```powershell
phist restore --version 2
phist restore "chapter.md" --version 2
```

The first restores all files from snapshot `2`; the second restores only
`chapter.md`. Both show the planned actions and ask for confirmation. For one
file, the confirmation is `Replace the current file? [y/N]:` or, when missing,
`Recreate this file? [y/N]:`. If every selected file already matches, the
command reports `Already matches this snapshot. No changes.` without
confirmation.
<!-- Verified from: src/cli/documents.py [restore, _show_plan]; src/adapters/snapshot_documents.py [prepare_restore] -->

When you restore a whole snapshot, only the files recorded in it are restored.
The command does not remove extra files currently in your writing folder. Files
omitted from the snapshot, including newer chapters, are left alone. Tracking
rules do not control the restore selection. Use the old saved filename when
restoring a renamed file; this recreates the old path without deleting the new
one.
<!-- Verified from: src/adapters/snapshot_documents.py [prepare_restore, restore_files] -->

Restore preserves exact saved bytes, including encoding and line endings, and
can recreate deleted files and their parent folders. It preserves snapshot
records and creates no backup copy or new snapshot. Run `phist save` before
restoring to preserve your current draft, and afterward to record the restored
draft as a new save. Restoration does not change the version label offered by
the next save; that still comes from the latest saved snapshot.
<!-- Verified from: src/cli/documents.py [restore]; src/adapters/snapshot_documents.py [restore, restore_files]; src/adapters/snapshot_content.py [write_atomic]; src/cli/app.py [save] -->

All selected saved contents and current destinations are checked before writing.
If a document changes while you answer the confirmation, restoration stops
before any replacements. Missing or damaged saved contents also produce an
error before writing. Symbolic links, junctions, history metadata paths, and
paths outside the writing folder cannot be restored.
<!-- Verified from: src/adapters/snapshot_documents.py [prepare_restore, restore_files]; src/adapters/snapshot_content.py [document_path] -->

Each file replacement is atomic, but a folder restore is not an all-or-nothing
operation. A later write failure can leave earlier files restored. The error
reports how many files were restored and their names. Review the files and fix
the reported problem before retrying; matching files are left unchanged on the
next attempt.
<!-- Verified from: src/adapters/snapshot_documents.py [restore_files]; src/adapters/snapshot_content.py [write_atomic] -->

Ctrl+C cancels while choosing a snapshot or answering the confirmation. For use
without prompts, supply both `--version` and `--yes` (or `-y`), for example
`phist restore --version 2 --yes`. `--yes` alone produces an error, so a
snapshot cannot be chosen silently.
<!-- Verified from: src/cli/documents.py [_choose_snapshot, restore] -->

Both `diff` and `restore` accept `--path` / `-p`. Their filenames are relative
to that writing folder, and globs are not expanded. `--version` takes an integer
snapshot number of at least `1`, not a semantic label such as `0.1.0`.
<!-- Verified from: src/cli/documents.py [diff, restore]; src/cli/options.py [Root] -->

### Read defaults in terminal prompts

Square brackets show the available choices or the default value. Press
**Enter** without typing an answer to accept the default.

| Prompt | What pressing Enter does | How to choose something else |
| --- | --- | --- |
| `Save message:` | There is no default; a message is required, so the prompt asks again. | Type a description of your changes and press Enter. |
| `Apply a version number? [y/N]:` | Chooses **No** and saves without a version label. The uppercase `N` marks the default. | Type `y` or `yes` and press Enter to enter a version. |
| `Change the version number? [y/N]:` | Chooses **No** and keeps the current version label. | Type `y` or `yes` and press Enter to enter a version. |
| `Snapshot number to restore [2]:` | Uses snapshot `2`; the displayed default is the latest snapshot number. | Type another saved snapshot number and press Enter. |
| `Restore these files? [y/N]:`, `Replace the current file? [y/N]:`, or `Recreate this file? [y/N]:` | Cancels restoration without changing files. | Type `y` or `yes` and press Enter to restore the selected files. |
| `Version (MAJOR.MINOR.PATCH) [0.1.0]:` | Uses `0.1.0`, the value shown in brackets. | Type another valid version, such as `1.0.0`, and press Enter. |
<!-- Verified from: src/cli/save.py [_read_message, _read_version]; src/domains/history.py [validate_message, validate_version]; src/cli/documents.py [restore] -->

For a yes/no question, you can also type `n` or `no`. The `y` and `N` in
`[y/N]` are choices, not text you need to copy. For a version prompt, the
bracketed value is a suggestion; do not type the brackets. If a version already
exists, the suggestion is that current version instead of `0.1.0`.
<!-- Verified from: src/cli/save.py [_read_version] -->

For example, with two matching files and no previous snapshots:

```text
Save message: initial save
Apply a version number? [y/N]: y
Version (MAJOR.MINOR.PATCH) [0.1.0]:
Saved snapshot 1: initial save
Files saved: 2
Version: 0.1.0
```

Here, you typed `initial save`, answered `y`, and then pressed Enter at the
version prompt without typing a number. That accepted `0.1.0`. The final three
lines report the saved snapshot; they do not ask for more input. Pressing Enter
at `Apply a version number?` instead would skip the version prompt and report
`Version: none`. On later saves, pressing Enter at `Change the version number?`
keeps the version already assigned.
<!-- Verified from: src/cli/save.py [read_details, _read_version]; src/cli/app.py [save] -->

### Choose a version number

A semantic version is a label made of three whole numbers separated by dots:
`MAJOR.MINOR.PATCH`. In `1.2.3`, the major number is `1`, the minor number is
`2`, and the patch number is `3`. Think of the three positions as a way to
describe the size of a change.
<!-- Verified from: src/domains/history.py [validate_version] -->

Semantic versioning comes from software, where the numbers describe changes to
compatibility and functionality. For writing, the following is a suggested
convention, not a rule phist enforces. You decide which changes mark a milestone
in your work. [The SemVer specification](https://semver.org/) explains the
original software rules.

| Kind of change | Suggested use for writing | Example |
| --- | --- | --- |
| Patch: small corrections | Fix typos, punctuation, or a few words. | `1.2.3` becomes `1.2.4`. |
| Minor: a meaningful revision | Add a section or revise a chapter while keeping the same overall edition. | `1.2.3` becomes `1.3.0`. |
| Major: a new edition | Complete a substantial rewrite or reorganize the work into a new edition. | `1.2.3` becomes `2.0.0`. |
<!-- Verified from: src/domains/history.py [validate_version]; src/cli/save.py [_read_version]. Writing examples are suggested conventions, not automatic classifications. -->

When increasing the minor number, reset the patch number to `0`. When increasing
the major number, reset both later numbers to `0`. The numbers are separate
counters, not decimals: after `1.0.9`, the next patch is `1.0.10`.

To get started:

1. Use `0.1.0` for an early working draft; phist suggests this when you first
   choose a version.
1. Choose `1.0.0` when you decide the work has reached its first complete
   edition.
1. For later milestones, use the table above to choose a number and enter the
   full label when `save` asks.
<!-- Verified from: src/cli/save.py [_read_version]; src/domains/history.py [validate_version]. Draft and edition milestones are optional writing conventions. -->

You can skip version numbering entirely, or keep the same label for several
saves. Each save still creates its own numbered snapshot. For example, snapshots
`5` and `6` can both carry version `0.1.0` but contain different drafts. The
snapshot number identifies the individual save; the version label marks a
milestone you chose. phist does not choose a larger version automatically or
judge how much your writing changed.
<!-- Verified from: src/cli/save.py [_read_version]; src/adapters/snapshots.py [_write_snapshot]; src/domains/history.py [Snapshot] -->

Use all three numbers, with no leading zeroes: enter `1.2.0`, not `1.2` or
`01.2.0`. Optional labels such as `1.0.0-beta.1` can mark a draft before
`1.0.0`; you can ignore these extra labels when starting out.
<!-- Verified from: src/domains/history.py [validate_version] -->

### Change or remove a selection rule

There is no removal command. You can edit the saved rule list directly.

1. Open `C:/writing/my_book/.plain_history/tracking.json` as a text file.
1. Change or remove the relevant quoted entry, keeping a valid JSON array.
1. Save the file as UTF-8.
1. Run `phist check --path C:/writing/my_book` to review the new selection.

For example, this file selects only Markdown files under `chapters/`:

```json
[
  "chapters/**/*.md"
]
```

Use `[]` for an empty selection. Edits take effect the next time a command reads
the tracking rules, including `check`, `track`, or `save`. Removing a rule does
not delete a document. The file may not exist until you first add rules; a
missing file means an empty selection.
<!-- Verified from: src/adapters/tracking.py [load, add, list_files]; src/cli/app.py [check, track] -->

### View setup in the desktop window

1. Start `phist-gui` with your writing folder as the current directory.
1. Read the folder status in the **plain_history** window.
1. If it reports that no repository exists, close it and use `phist init` in
   that folder.
1. Reopen the window to read the updated status.

The desktop view reads setup when it opens. It does not show tracking rules or
automatically refresh after a terminal command.
<!-- Verified from: src/gui/app.py [main, build_window]; src/adapters/repository.py [load] -->

## Settings and Preferences

Tracking rules are the current user-editable selection setting. There is no
preferences screen.

| Setting | Default | Accepted values | How to change it |
| --- | --- | --- | --- |
| Tracking rules | Empty list when `tracking.json` is absent | JSON array of relative file paths or glob strings | Add with `phist track`; edit `.plain_history/tracking.json` to revise or remove rules. |
| Snapshot version | No version before one is assigned | SemVer label, such as `0.1.0` or `1.0.0-beta.1` | Choose whether to add or change it during `save`; retained after a successful save. |
| Writing folder for a terminal command | Current directory | Folder path; `init` requires an existing directory, and `track`/`check`/`save` require initialized history | Supply `--path` or `-p` after the command. |

Tracking rules persist and take effect the next time a command reads them,
including `check`, `track`, or `save`.
The `--path` choice applies only to that invocation and is not saved as a
preference. A tracking rule is interpreted relative to that selected folder.
<!-- Verified from: src/cli/save.py [_read_version]; src/cli/app.py [Root, init, check, track, save]; src/adapters/tracking.py [load, add]; src/adapters/repository.py [init, load] -->

## Importing and Exporting

Not applicable.
<!-- Verified from: src/cli/app.py; src/gui/app.py -->

## Commands and Shortcuts

These are Windows terminal examples. Replace the sample filenames and folder
paths with your own.

| Command or option | Accepted values | What it does |
| --- | --- | --- |
| `phist init` | Optional `--path` / `-p` | Initializes history in an existing folder. |
| `phist track "*.md"` | One or more file paths or glob strings; optional `--path` / `-p` | Adds persistent selection rules and lists current matches. |
| `phist save` | Optional message; optional `--path` / `-p` | Prompts for a message if omitted and an optional version, then saves currently selected files. |
| `phist history` | Optional relative document path; optional `--path` / `-p` | Lists saved snapshot summaries, newest first; optionally filters for snapshots containing one file. |
| `phist last` | Optional `--path` / `-p` | Shows the latest snapshot details and saved filenames. |
| `phist diff chapter.md` | Optional integer `--version`, default latest snapshot; optional `--path` / `-p` | Compares saved UTF-8 text with the current document. |
| `phist restore` | Optional relative filename and integer `--version`; optional `--path` / `-p`; `--yes` / `-y` requires `--version` | Prompts for a snapshot if none is specified, shows the plan, and restores one file or all recorded files after confirmation. |
| `phist check` | Optional `--path` / `-p` | Validates setup and lists rules and matches. |
| `phist --help` | No arguments | Shows command help. |
| `phist track --help` | `--help` also works with other commands | Shows a command's arguments and options. |
| `--path FOLDER` / `-p FOLDER` | Path, default `.` | Selects the writing folder for that command. |
| `phist --show-completion` | No arguments | Shows completion code for the current shell. |
| `phist --install-completion` | No arguments | Requests completion installation for the current shell. |
<!-- Verified from: src/cli/app.py [app, init, track, check, save, last, history]; src/cli/options.py [Root]; src/cli/documents.py [diff, restore]; src/cli/history.py [show]; pyproject.toml [project.scripts] -->

Successful commands, empty history results, unchanged comparisons, and declined
restore confirmations return exit code `0`. Handled setup, file-access, and
validation errors return `1`; invalid command arguments return `2`. Use `check`
to review setup; there is no `status` command.
<!-- Verified from: src/cli/app.py [_repository_path, init, track, check]; src/cli/documents.py [diff, restore] -->

**Ctrl+C** cancels a terminal save during its prompts or a restore confirmation.
No application-specific keyboard shortcuts are defined for the Windows desktop
window.
<!-- Verified from: src/gui/app.py [build_window, main]; src/cli/save.py [read_details]; src/cli/documents.py [restore] -->

## Your Data Files

Each initialized writing folder contains its own `.plain_history` directory.

| File or folder | Purpose | Hand editing |
| --- | --- | --- |
| Your selected documents | Original writing files; tracking selects paths and saving copies their contents | Continue editing normally in your writing application. |
| `.plain_history/config.toml` | Identifies the supported history format | Leave the generated format value unchanged. |
| `.plain_history/tracking.json` | Persistent list of files and glob rules | Editable as a UTF-8 JSON array of strings. |
| `.plain_history/history.json` | Ordered snapshot records containing number, timestamp, message, optional version, and file identifiers | Program-managed UTF-8 JSON; do not edit by hand. |
| `.plain_history/save.lock` | Temporary marker preventing overlapping saves | Normally removed when saving finishes; see troubleshooting if it remains. |
| `.plain_history/objects/` | Stored snapshot contents, named by content identifiers | Keep this directory and its contents intact; do not edit stored objects. |
<!-- Verified from: src/adapters/repository.py [init, load]; src/adapters/tracking.py [load, add, list_files]; src/cli/app.py [save]; src/adapters/snapshots.py; src/adapters/snapshot_content.py -->

The generated `config.toml` contains:

```toml
format_version = 1
```

Only integer format version `1` is accepted. A different value, missing value,
or invalid TOML prevents the folder from passing setup validation. Tracking
rules belong in the separate `tracking.json` file described above.
<!-- Verified from: src/adapters/repository.py [init, load]; src/domains/repository.py [validate_format]; src/adapters/tracking.py [load] -->

Choose a different writing folder using `--path`, and initialize that folder if
needed. This does not move an existing history folder. The current terminal and
desktop entry points do not configure application log files; read terminal
output or the desktop status message for errors.
<!-- Verified from: src/cli/app.py [Root, main, init]; src/gui/app.py [main]; src/adapters/repository.py [init] -->

## Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Message says to run `phist init` | The selected folder has no readable history configuration | Check the folder path. For a folder without existing metadata, run `phist init --path FOLDER`. An existing incomplete setup is not repaired by rerunning `init`. |
| `Repository root is not a directory:` | The initialization target does not exist or is a file | Select an existing writing folder. |
| `Unsupported repository format.` | The configuration's format value is missing or not integer `1` | Check that you selected the intended history folder. Automatic repair or migration is not available. |
| `Repository objects directory is missing.` | Existing history setup is incomplete | Check the selected folder and inspect its `.plain_history` contents. Automatic repair is not available. |
<!-- Verified from: src/adapters/repository.py [init, load]; src/domains/repository.py [validate_format] -->

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `Matching files: 0` | No saved rules or no current files match | Review `Tracking rules:` and the selected root; use `**` for subfolders. Unmatched rules can remain for future files. |
| Message asks for a relative file or glob | A rule contains an absolute path, parent traversal, or another invalid component | Use a rule such as `chapters/**/*.md`; use `--path` to choose the writing folder. |
| Message suggests a rule ending in `/**/*` | A bare directory was supplied to `track` | Use the suggested glob to select files inside that directory. |
| Error while reading `tracking.json` | Invalid JSON or a value other than an array of valid rule strings | Correct the UTF-8 JSON file and run `check` again. Use `[]` if you intend to clear the selection. |
| Save asks again for a message | Empty or whitespace-only message | Enter a description of the draft. |
| Save asks again for a version | The entered label is not valid SemVer | Enter a label such as `0.1.0` or `1.0.0-beta.1`. |
| Save reports no tracked files | The selection currently matches no files | Use `track` to add rules and `check` to review matches. |
| Message mentions `save.lock` | Another save is active or was interrupted | Wait for active saves. If you have confirmed no save is running, remove only `.plain_history/save.lock` and retry. |
| `History changed while answering prompts` | Another save completed during your prompts | Run `phist save` again to use the latest version. |
| Diff reports that the snapshot does not contain the file | That path was not included in the chosen save | Use `phist history "chapter.md"` to find a snapshot containing that filename. |
| Diff reports UTF-8 text only | Saved or current bytes cannot be decoded as UTF-8 | Use UTF-8 documents for comparison; restore still supports exact saved bytes. |
| Restore reports that some files were restored before an error | A later file replacement failed | Review the reported restored filenames, fix the problem, and retry; matching files are skipped. |
| Restore reports that the document changed during prompts | The file changed after the confirmation was displayed | Review the new edits and retry when ready. |
| Error reading `history.json` or damaged stored content | Saved history is unreadable or inconsistent | Stop saving into this history folder and inspect the reported file; automatic repair is not available. |
| Desktop still shows an earlier setup message | The desktop reads setup only when opened | Close and reopen the window from the intended writing folder. |
<!-- Verified from: src/adapters/tracking.py [load, add, list_files]; src/domains/tracking.py [normalize_pattern]; src/cli/app.py [save]; src/cli/save.py; src/adapters/snapshots.py; src/adapters/snapshot_content.py; src/adapters/snapshot_documents.py; src/cli/documents.py; src/gui/app.py [main, build_window] -->

## FAQ

### Does tracking save my draft?

No. It saves selection rules. Run `phist save` to save the contents of the
currently matching files.
<!-- Verified from: src/adapters/tracking.py [add]; src/cli/app.py [save, track] -->

### Will a new chapter be selected automatically?

Yes, if it matches a saved rule. Run `phist check` to see the refreshed
selection. This does not create a snapshot or automatically monitor edits.
<!-- Verified from: src/adapters/tracking.py [list_files]; src/cli/app.py [check] -->

### Can I track extensions other than .txt and .md?

Yes. File selection does not restrict extensions. Saving stores their exact
bytes. Diff supports UTF-8 text; restore copies the exact bytes of any saved
file, without interpreting its document format.
<!-- Verified from: src/adapters/tracking.py [list_files]; src/cli/app.py [save]; src/cli/documents.py [diff, restore] -->

### Does check find a setup in the parent folder?

No. Run the command from the initialized folder or pass its path explicitly
with `--path`.
<!-- Verified from: src/cli/app.py [Root]; src/adapters/repository.py [load] -->

### What happens if I repeat init or track?

`init` validates and preserves existing metadata. `track` retains existing rules
and adds only new normalized rules. Overlapping rules do not duplicate files in
the match list.
<!-- Verified from: src/adapters/repository.py [init]; src/adapters/tracking.py [add, list_files] -->

## Glossary

| Term | Meaning |
| --- | --- |
| Writing folder | The folder selected for initialization or checking; paths in tracking rules start here. |
| Current directory | The terminal's working folder, used when `--path` is omitted. |
| Repository | The writing folder together with its `.plain_history` setup. |
| Tracking rule | A stored relative filename or glob that selects documents. |
| Glob | A filename pattern; `*` matches within one path component and `**` covers subfolders. |
| Snapshot | A saved version of the tracked documents, with a message and optional version label. |
| Metadata | Supporting history files stored under `.plain_history`. |
<!-- Verified from: src/cli/app.py [Root, save]; src/adapters/repository.py; src/adapters/tracking.py; src/domains/tracking.py -->

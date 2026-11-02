---
last_updated: 2026-11-01
version: 1.0.0
description: On-disk format of a writing folder's .plain_history directory, format version 1.
---

# History Format

Plain History keeps a writing folder's history in a hidden `.plain_history`
directory at the root of that folder. This document defines that directory so
every platform's application reads and writes the same history. A folder saved
on one platform must open, compare, and restore on every other.

This describes format version 1, as written by the Windows application. Change
this document together with every implemented platform.

## Layout

```text
writing-folder/
  .plain_history/
    config.toml       required: format version
    objects/          required: saved document contents
      <sha-256>       one file per distinct document content
    tracking.json     optional: tracking rules
    history.json      optional: saved snapshots
    save.lock         present only while a save runs
  chapter1.md         the writer's documents, never modified by a save
```

The writing folder is the directory that contains `.plain_history`. Every
relative path below is relative to it.

## Text files

`config.toml`, `tracking.json`, and `history.json` are UTF-8 with LF line
endings and end with a newline. JSON files are written with two-space
indentation, with non-ASCII characters left unescaped. Readers must accept any
valid UTF-8 JSON with the same structure, regardless of whitespace.

Document paths stored in these files use `/` as the separator on every
platform.

## config.toml

```toml
format_version = 1
```

`format_version` must be the integer `1`. Reject the folder when the file is
missing, when the value is any other number, or when it is not an integer, such
as `true` or `"1"`. Also reject it when `objects/` is missing. A rejected folder
is left unchanged.

Initializing a folder creates `.plain_history/`, `objects/`, and this file, and
nothing else. Initializing a folder that already has `.plain_history` only
validates it.

## objects/

Each saved document content is stored once, in a file named by the lowercase
hexadecimal SHA-256 digest of its exact bytes: 64 characters from `0-9a-f`. The
file holds those bytes unchanged, with no newline or encoding conversion.

- Write a new object to a temporary file in `objects/`, flush it to disk, then
  rename it into place, so a reader never sees a partial object.
- When an object already exists, reuse it only if its bytes equal the new
  content. Otherwise stop: the stored content is damaged.
- Before using an object for comparison or restore, recompute its digest and
  stop if it differs from the file name.
- Objects are never modified or deleted. A failed save may leave unused
  objects behind; they are harmless.

## tracking.json

A JSON array of tracking rules, in the order they were added:

```json
[
  "*.md",
  "chapters/**/*.txt"
]
```

A missing file means no rules. Anything other than an array of strings is
invalid. Duplicate rules are dropped, keeping the first.

### Rule normalization

Normalize every rule before storing or matching it:

1. Replace each `\` with `/`.
1. Reject the rule if it is empty, starts with `/`, has a drive such as `C:`,
   contains `:` anywhere, or has a `..` segment.
1. Reject it if `**` appears in a segment with other characters, such as
   `a**`; `**` must be a whole segment.
1. Reject it if any segment equals `.plain_history`, ignoring case.
1. Reject it if it contains a character below U+0020.
1. Collapse repeated `/` and `.` segments and drop a trailing `/`, as
   `chapters//./one.md` becomes `chapters/one.md`.

When adding rules, reject a rule that names an existing folder, such as
`chapters`, and ask for `chapters/**/*` instead. Validate a whole batch before
writing any of it.

### Matching

Rules are glob patterns evaluated against the folder each time a selection is
needed, so new documents that match are included automatically:

- `*` matches any run of characters within one path segment, including a
  leading `.`. `?` matches one character, and `[...]` matches a character set.
- `**` as a whole segment matches zero or more directories.
- Case follows the platform's default rules: case-insensitive on Windows and
  case-sensitive on Linux. A macOS implementation must decide and document its
  rule here before release.

The selection is the sorted, de-duplicated set of matching regular files,
written as relative `/` paths. Leave out anything inside `.plain_history`,
anything reached through a symbolic link or junction at any level of its path,
and anything that resolves outside the writing folder.

## history.json

A JSON array of snapshots in save order. A missing file means no snapshots.

```json
[
  {
    "number": 1,
    "created_at": "2026-11-01T04:15:30.123456+00:00",
    "message": "First draft",
    "version": "0.1.0",
    "files": {
      "chapter1.md": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    }
  }
]
```

| Field | Type | Rule |
| --- | --- | --- |
| `number` | integer | Equals the snapshot's 1-based position in the array. |
| `created_at` | string | Nonempty UTC timestamp in ISO 8601 form with an offset, as in the example. |
| `message` | string | Stored trimmed of surrounding whitespace; must not be empty. |
| `version` | string or `null` | A Semantic Versioning 2.0.0 label without leading zeroes in numeric parts or numeric prerelease identifiers, or `null` for none. |
| `files` | object | Nonempty. Each key is a normalized relative path as stored in tracking rules; each value is the digest of an object in `objects/`. |

Write the fields in the order shown. Format version 1 defines no other fields,
and writers replace the whole array on every save, so a reader must not rely on
extra fields surviving. Adding a field requires a new format version.

Reject the history when any record breaks these rules.

## Saving a snapshot

1. Validate the message and the optional version label.
1. Create `save.lock` exclusively, failing if it already exists. Its presence
   means another save is running or an interrupted save left it behind; refuse
   to save until the writer removes it.
1. Reload `history.json` and confirm it still has the number of snapshots seen
   before the writer was prompted. If not, stop and ask them to save again.
1. Compute the selection. Stop if it is empty.
1. Read every selected document's bytes, then write its objects.
1. Append the new snapshot with the next `number` and the current UTC time.
1. Write the complete `history.json` to a temporary file in `.plain_history`,
   flush it, and rename it over the old file.
1. Remove `save.lock`, including when an earlier step fails.

A save never changes the writer's documents.

## Restoring documents

A restore writes saved bytes back to documents. It never changes history.

1. Choose a snapshot and either one of its files or all of them. Match a
   requested file name using the platform's path case rules.
1. Read each chosen object, verify its digest, and record each document's
   current bytes, or that it is missing.
1. Before writing, check that every document still has the recorded bytes. If
   one changed, stop without writing anything.
1. For each document whose bytes differ, create missing parent folders and
   replace the file with a temporary file plus rename. Never write through a
   symbolic link or junction, or outside the writing folder.

Each file is replaced atomically. A restore of several files is not a
transaction: a failure reports the files already restored and keeps no backup
copies.

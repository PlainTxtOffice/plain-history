# Windows builds

Run these commands from `platform/windows/` in PowerShell 7:

```powershell
.\scripts\nuitka\standalone.ps1
.\scripts\nuitka\onefile.ps1
.\scripts\nuitka\standalone-debug.ps1
.\scripts\nuitka\gui.ps1
```

Each command works without arguments. The selected interpreter defaults to
`.venv/Scripts/python.exe`; install the application and Nuitka into that
environment first, with `.venv/Scripts/python.exe -m pip install -e .` and
`.venv/Scripts/python.exe -m pip install "nuitka[onefile]" zstandard`.
Onefile compression needs `zstandard`, which `nuitka[onefile]` does not
install.
Builds use the latest installed MSVC compiler.

Plain History has two programs. The standard scripts build the `phist`
command-line program, which the installer and the portable download ship.
`gui.ps1` builds the `phist-gui` desktop window in the same way.

| Script | Output | Console | Distribution |
| --- | --- | --- | --- |
| `standalone.ps1` | `build/standalone/phist.dist/phist.exe` | Visible | Package the entire `.dist` folder with Advanced Installer |
| `onefile.ps1` | `build/onefile/phist.exe` | Visible | Ship the executable alone as the portable download |
| `standalone-debug.ps1` | `build/standalone-debug/phist.dist/phist.exe` | Visible | Local troubleshooting only |
| `gui.ps1` | `build/gui/phist-gui.dist/phist-gui.exe` | Hidden | Desktop window; not yet part of a download |

`phist` is a terminal program, so every CLI variant keeps its console. The
debug script forwards to `standalone.ps1` and differs only by leaving out the
anti-debugger and signing, so a debugger can attach, and by writing to its own
folder. It does not enable Nuitka's compiler debug option.

## Optional overrides

The build scripts accept `PythonExecutable`, `OutputDirectory`, and
`OutputFilename`. Relative paths resolve from `platform/windows/`, whatever the
caller's working directory; absolute paths are honored.

```powershell
.\scripts\nuitka\standalone-debug.ps1 -OutputDirectory 'build/debug trial'
.\scripts\nuitka\onefile.ps1 -PythonExecutable 'C:\build-env\Scripts\python.exe'
```

They also accept `UseCurrentDefaultPaths` and `ResetRuntimeDefaults`, but both
stop with an explanation: Plain History has no runtime defaults file and no
application data folder. Writing history lives in each writing folder's
`.plain_history`, and the desktop window keeps its last folder in the
registry.

## Commercial detection and signing

Each build runs `python -m nuitka --plugin-list` once with the selected
interpreter. When the list includes `data-hiding`, Nuitka Commercial is
installed and its features are turned on automatically. Free Nuitka builds
add no Commercial flags and warn that constants are not encrypted.

| Feature | `standalone.ps1`, `onefile.ps1`, `gui.ps1` | `standalone-debug.ps1` |
| --- | --- | --- |
| Constant protection | When Commercial is detected | When Commercial is detected |
| Anti-debugger | When Commercial is detected | Disabled |
| Certificate signing | Commercial plus a configured certificate | Disabled |

No bundled file is embedded: the only one is the public `LICENSE`. See Nuitka's
[constant protection](https://nuitka.net/doc/commercial/protect-constants-data.html)
documentation.

To sign release builds, install the code-signing certificate in the Windows
certificate store, then save its SHA-1 thumbprint once per machine:

```powershell
[Environment]::SetEnvironmentVariable('WINDOWS_CERTIFICATE_SHA1', '<your certificate SHA-1 thumbprint>', 'User')
```

Replace the placeholder with the certificate's 40 hexadecimal characters. The
scripts read the current process value first, then the saved user value, so a
new terminal is not needed. They pass the thumbprint to Nuitka's `signtool`
plugin; no password is stored. Without a certificate or Commercial, each release
build warns once that it is unsigned. Sign the installer separately.

## Runtime data and release checks

The builds bundle only `LICENSE`, and set the product name, version, company,
copyright, and description from `pyproject.toml`, including the
`[tool.plain-history.packaging]` table. None of them bundles `portable.marker`,
because the programs write no application data that a portable copy would need
to keep beside itself.

After each build, the script scans the executables and text files in its `.dist`
folder for the developer's username, the absolute repository and project paths,
and the author emails, as UTF-8 and UTF-16LE. Hits are warnings to review, not
failures. The onefile build scans the uncompressed staging folder it was packed
from.

`standalone.ps1`, `standalone-debug.ps1`, and `gui.ps1` then run
`validate_release.ps1` on their `.dist` folder. It reports runtime data folders,
a `.plain_history` folder, environment files, the project's tests, links, a
portable marker, or a missing executable, and never changes the payload. Add it
as an Advanced Installer pre-build event, with `platform/windows/` as the
event's working directory:

```powershell
pwsh -NoProfile -File scripts/nuitka/validate_release.ps1
```

For another folder, pass `-DistPath`, such as
`-DistPath 'build/gui/phist-gui.dist'`. The default is
`build/standalone/phist.dist`. The check exits 1 when it finds problems and 0
for a clean folder.

The installer installs under Program Files. Because the programs keep no data
there or under `%LOCALAPPDATA%`, uninstalling has no application data to keep
or remove; writing folders and their history are never touched.

## Smoke testing and shipping

Smoke-test a **copy** of a `.dist` folder, never the installer input itself.
For the CLI, run `phist.exe --help`, then `init`, `track`, `save`, and `history`
in a scratch writing folder outside the build tree. For the desktop window, open
a scratch writing folder and save a snapshot.

Ship only the portable executable or the complete release `.dist` folder. Keep
debug outputs for local troubleshooting. Keep Nuitka's `*.build/` folders and
the onefile staging `.dist` for later builds and inspection, but never ship
them, compilation reports, or crash reports.

On GitHub, the `windows-build.yml` workflow runs these scripts with free Nuitka
and keeps their outputs as workflow artifacts. Those builds are unsigned and
their constants are not encrypted; distribute local Commercial builds.

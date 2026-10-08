# Build the Windows CLI

These scripts build the `phist` terminal application from source using
`.venv/Scripts/python.exe`, Nuitka, and the latest installed MSVC compiler.
The console remains enabled for command output and interactive prompts. The
GUI entry point is not included by the CLI build.

From the repository root in PowerShell:

```powershell
./scripts/nuitka/standalone.ps1
./build/nuitka/cli/standalone/phist.dist/phist.exe --help
```

Distribute the entire `phist.dist` folder, including its executable,
supporting files, and `LICENSE`. This build runs without a separate Python
installation. Verify the standalone build before creating a single executable:

```powershell
./scripts/nuitka/onefile.ps1
./build/nuitka/cli/onefile/phist.exe --help
```

Both builds include the project MIT license. When distributing the portable
executable, also provide the repository `LICENSE` file alongside the download.

The onefile build produces `phist.exe` and requires `zstandard` in the build
interpreter. Both scripts check their dependencies and stop with an error if
Nuitka fails. If needed, install Nuitka with onefile support using
`.venv/Scripts/python.exe -m pip install "nuitka[onefile]"` and install the
project dependencies with `.venv/Scripts/python.exe -m pip install -e .`.

Both scripts resolve paths relative to the repository, so they can be invoked
from another working directory. To use another build environment or output
location:

```powershell
./scripts/nuitka/standalone.ps1 -PythonExecutable C:/Python/python.exe -OutputDirectory build/custom-cli -OutputFilename phist.exe
./scripts/nuitka/onefile.ps1 -WhatIf
```

`-WhatIf` performs environment checks and previews the build without compiling
or creating the output directory. `OutputFilename` must be a filename ending
in `.exe`. Nuitka's intermediate outputs remain in the selected build directory;
build artifacts are ignored by Git. The scripts allow Nuitka to download
required build tools when needed.

The executable acts on the terminal's current writing folder, or the folder
passed with `--path`. Writing history stays in that folder's `.plain_history`;
the build scripts do not initialize or modify document history.

The Windows installer is created from the standalone build in a separate
packaging step.

Reference:
[Nuitka User Manual](https://nuitka.net/user-documentation/user-manual.html).

# Windows application

Run these commands from `platform/windows/`:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m plain_history --help
.venv/Scripts/python.exe -m plain_history.ui.gui.app
```

Development checks:

```powershell
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m mypy plain_history
.venv/Scripts/rumdl.exe check
```

Application modules live in `plain_history/` and use imports such as
`plain_history.adapters.repository`. The installed commands are `phist` and
`phist-gui`. Add application tests under `tests/`.

See the [Nuitka build guide](scripts/nuitka/README.md) for the Windows
executables and the [repository README](../../README.md) for project-wide
documentation.

On GitHub, the CI workflow runs these checks on every push to `main`, and the
Windows build workflow compiles the three Nuitka builds and keeps them as
workflow artifacts. Start a build from the Actions tab or by pushing a tag such
as `v0.2.0`.

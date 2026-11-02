"""Define the writing-folder option shared by terminal commands."""

from pathlib import Path
from typing import Annotated

import typer

Root = Annotated[Path, typer.Option("--path", "-p", help="Repository root.")]

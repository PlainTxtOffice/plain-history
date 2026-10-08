# Build the plain_history CLI using the project's Python environment.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateNotNullOrEmpty()]
    [string]$PythonExecutable = ".venv/Scripts/python.exe",
    [ValidateNotNullOrEmpty()]
    [string]$OutputDirectory = "build/nuitka/cli/standalone",
    [ValidateNotNullOrEmpty()]
    [string]$OutputFilename = "phist.exe"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Write-Host "Building plain_history CLI (standalone)"

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw "This build script targets Windows."
}
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "../..")).Path
$pythonPath = if ([IO.Path]::IsPathRooted($PythonExecutable)) {
    $PythonExecutable
} else {
    Join-Path $repoRoot $PythonExecutable
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Build interpreter not found: $pythonPath. Create .venv or set -PythonExecutable."
}
$pythonPath = (Resolve-Path -LiteralPath $pythonPath).Path
$outputPath = if ([IO.Path]::IsPathRooted($OutputDirectory)) {
    [IO.Path]::GetFullPath($OutputDirectory)
} else {
    [IO.Path]::GetFullPath((Join-Path $repoRoot $OutputDirectory))
}
if ($OutputFilename -ne [IO.Path]::GetFileName($OutputFilename) -or
    $OutputFilename.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0 -or
    [IO.Path]::GetExtension($OutputFilename) -ne ".exe") {
    throw "OutputFilename must be a Windows filename ending in .exe, without a folder path."
}

& $pythonPath -c "import sys; sys.path.insert(0, sys.argv[1]); import nuitka; import src.cli.app" $repoRoot
if ($LASTEXITCODE -ne 0) {
    throw "Nuitka or CLI dependencies are unavailable in $pythonPath. Install them before building."
}

$nuitkaArguments = @(
    "-m", "nuitka",
    "--standalone",
    "--windows-console-mode=force",
    "--msvc=latest",
    "--output-filename=$OutputFilename",
    "--output-folder-name=$([IO.Path]::GetFileNameWithoutExtension($OutputFilename))",
    "--output-dir=$outputPath",
    "--assume-yes-for-downloads",
    "--include-data-files=$repoRoot/LICENSE=LICENSE",
    (Join-Path $repoRoot "src/main.py")
)

Write-Host "Output directory: $outputPath"
if ($PSCmdlet.ShouldProcess($outputPath, "Build plain_history CLI with Nuitka (standalone)")) {
    New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
    Push-Location -LiteralPath $repoRoot
    try {
        & $pythonPath @nuitkaArguments
        if ($LASTEXITCODE -ne 0) {
            throw "Nuitka standalone build failed with exit code $LASTEXITCODE."
        }
    } finally {
        Pop-Location
    }
}

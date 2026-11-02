#requires -Version 7.3
# Build the phist CLI as one portable executable.
[CmdletBinding()]
param(
    [string]$PythonExecutable = '.venv/Scripts/python.exe',
    [string]$OutputDirectory,
    [string]$OutputFilename = 'phist.exe',
    [switch]$UseCurrentDefaultPaths,
    [switch]$ResetRuntimeDefaults
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$repoRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot '../..'))
$pythonPath = [IO.Path]::GetFullPath($PythonExecutable, $projectRoot)
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Build interpreter not found: $pythonPath"
}

Push-Location $projectRoot
try {
    # Inline Python uses the selected interpreter's TOML parser.
    $metadataCode = @'
import json, tomllib
from pathlib import Path
config = tomllib.loads(Path("pyproject.toml").read_text("utf-8"))
project = config["project"]
packaging = config["tool"]["plain-history"]["packaging"]
if not packaging.get("company-name") or not packaging.get("copyright"):
    raise ValueError("Confirm company and copyright packaging metadata first")
print(json.dumps({
    "title": packaging["title"], "version": project["version"],
    "description": project["description"],
    "company": packaging["company-name"], "copyright": packaging["copyright"],
    "emails": [entry["email"] for entry in project.get("authors", []) if entry.get("email")]
}))
'@
    $rawMetadata = & $pythonPath -c $metadataCode
    if ($LASTEXITCODE -ne 0) { throw 'Could not read confirmed packaging metadata.' }
    $metadata = $rawMetadata | ConvertFrom-Json
    $variant = 'onefile'
    Write-Host "Building $($metadata.title) CLI ($variant)"
    # Writing history lives in each writing folder, so no app data folder or
    # runtime defaults file exists to bundle or reset.
    if ($UseCurrentDefaultPaths) { throw 'Plain History has no runtime default-path settings to bundle.' }
    if ($ResetRuntimeDefaults) { throw 'Plain History keeps no application data folder to reset.' }
    if (-not $OutputDirectory) { $OutputDirectory = "build/$variant" }
    $outputPath = [IO.Path]::GetFullPath($OutputDirectory, $projectRoot)
    if ([IO.Path]::GetFileName($OutputFilename) -ne $OutputFilename -or
        [IO.Path]::GetExtension($OutputFilename) -ne '.exe' -or
        $OutputFilename.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0) {
        throw 'OutputFilename must be a plain .exe filename, without a directory.'
    }
    $outputName = [IO.Path]::GetFileNameWithoutExtension($OutputFilename)
    $licensePath = Join-Path $repoRoot 'LICENSE'
    $plugins = & $pythonPath -m nuitka --plugin-list 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Could not query Nuitka plugins in the selected interpreter.' }
    $commercialAvailable = ($plugins -join "`n") -match '(?m)^\s*data-hiding(?:\s|$)'
    # The CLI reads and writes the terminal, so every variant keeps a console.
    $nuitkaArguments = @(
        '-m', 'nuitka', '--windows-console-mode=force', '--msvc=latest',
        '--assume-yes-for-downloads', "--output-filename=$OutputFilename",
        "--output-folder-name=$outputName", "--output-dir=$outputPath",
        "--include-data-files=$licensePath=LICENSE",
        "--product-name=$($metadata.title)", "--file-version=$($metadata.version)",
        "--product-version=$($metadata.version)", "--file-description=$($metadata.description)",
        "--company-name=$($metadata.company)", "--copyright=$($metadata.copyright)"
    )
    if ($commercialAvailable) {
        # Nothing bundled needs embedding: LICENSE is public and no defaults
        # file exists.
        $nuitkaArguments += @('--enable-plugin=data-hiding', '--enable-plugin=anti-debugger')
    }
    else { Write-Warning 'Constants are not encrypted: Nuitka Commercial was not detected.' }
    $certificate = $env:WINDOWS_CERTIFICATE_SHA1
    if (-not $certificate) {
        $certificate = [Environment]::GetEnvironmentVariable('WINDOWS_CERTIFICATE_SHA1', 'User')
    }
    if ($certificate -and $commercialAvailable) {
        $certificate = $certificate -replace '\s', ''
        if ($certificate -notmatch '^[0-9a-fA-F]{40}$') { throw 'WINDOWS_CERTIFICATE_SHA1 must contain 40 hexadecimal characters.' }
        $nuitkaArguments += @('--enable-plugin=signtool', "--windows-certificate-sha1=$certificate")
    }
    else { Write-Warning 'Building unsigned: signing needs Nuitka Commercial and WINDOWS_CERTIFICATE_SHA1.' }
    & $pythonPath -c 'import zstandard'
    if ($LASTEXITCODE -ne 0) {
        throw "Compressed onefile builds need zstandard. Run: & '$pythonPath' -m pip install 'nuitka[onefile]'"
    }
    [IO.Directory]::CreateDirectory($outputPath) | Out-Null
    # No portable.marker: the CLI has no app data folder to place beside the exe.
    $nuitkaArguments += @('--onefile', 'plain_history/__main__.py')
    Write-Host "Output directory: $outputPath"
    & $pythonPath @nuitkaArguments
    if ($LASTEXITCODE -ne 0) { throw "Nuitka $variant build failed with exit code $LASTEXITCODE." }
    # The compressed exe cannot be scanned; scan the staging folder it was packed from.
    $distPath = Join-Path $outputPath "$outputName.dist"
    $exePath = Join-Path $outputPath $OutputFilename
    if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) { throw "Missing built executable: $exePath" }
    # Chunked byte scanning stays inside this script; no external helper modules.
    $privacyCode = @'
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).absolute()
needles = [value for value in json.loads(sys.argv[2]) if value]
patterns = {value: (value.encode("utf-8"), value.encode("utf-16-le")) for value in needles}
overlap = max((len(part) for pair in patterns.values() for part in pair), default=1) - 1
if not root.is_dir():
    raise ValueError(f"Missing Nuitka payload: {root}")
if any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
    raise ValueError(f"Linked Nuitka payload: {root}")
reports, pending = [], [root]
while pending:
    for path in pending.pop().iterdir():
        if path.is_symlink() or path.is_junction():
            reports.append(f"Privacy scan did not follow linked payload entry: {path}")
        elif path.is_dir():
            pending.append(path)
        elif path.suffix.lower() in {".exe", ".json", ".toml", ".ini", ".cfg", ".txt", ".env"} or path.name == ".env":
            found, tail = set(), b""
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    chunk = tail + chunk
                    for needle, pair in patterns.items():
                        if any(part in chunk for part in pair):
                            found.add(needle)
                    tail = chunk[-overlap:] if overlap else b""
            reports.extend(f"Privacy scan found {needle!r} in {path}" for needle in sorted(found))
print(json.dumps(reports))
'@
    $needles = @($env:USERNAME, $repoRoot, $projectRoot,
        $repoRoot.Replace('\', '/'), $projectRoot.Replace('\', '/')) + @($metadata.emails)
    $needleJson = ConvertTo-Json -InputObject $needles -Compress
    $reports = & $pythonPath -c $privacyCode $distPath $needleJson
    if ($LASTEXITCODE -ne 0) { throw 'The post-build privacy scan could not finish.' }
    foreach ($report in ($reports | ConvertFrom-Json)) { Write-Warning $report }
}
finally { Pop-Location }

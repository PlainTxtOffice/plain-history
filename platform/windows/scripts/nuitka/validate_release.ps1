#requires -Version 7.3
# Report runtime data, tests, and links in a release .dist folder; never change it.
[CmdletBinding()]
param(
    [string]$DistPath = 'build/standalone/phist.dist',
    [string]$PythonExecutable = '.venv/Scripts/python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$pythonPath = [IO.Path]::GetFullPath($PythonExecutable, $projectRoot)
$resolvedDist = [IO.Path]::GetFullPath($DistPath, $projectRoot)
$exitCode = 1
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw "Validation interpreter not found: $pythonPath"
    }
    $validationCode = @'
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).absolute()
problems, files = [], []
if not root.is_dir():
    problems.append(f"Distribution folder does not exist: {root}")
elif any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)):
    problems.append(f"Distribution path contains a link: {root}")
else:
    # Plain History writes no app data; these appear only when a test run or
    # a copied writing folder left local state in the payload.
    for name in ("logs", "data", "exports", ".plain_history"):
        if (root / name).exists():
            problems.append(f"Runtime data must not ship: {root / name}")
    pending = [root]
    while pending:
        for path in pending.pop().iterdir():
            if path.is_symlink() or path.is_junction():
                problems.append(f"Linked payload entry: {path}")
            elif path.is_dir():
                pending.append(path)
            else:
                files.append(path)
                if path.name == "portable.marker":
                    problems.append(f"Standalone payload contains portable marker: {path}")
                if path.name == ".env" or path.name.startswith(".env."):
                    problems.append(f"Environment file must not ship: {path}")
                # Dependencies may ship their own tests folders; check only the app's.
                parts = path.relative_to(root).parts
                if parts[:1] == ("tests",) or parts[:2] == ("plain_history", "tests"):
                    problems.append(f"Test file must not ship: {path}")
    if not any(p.parent == root and p.suffix.lower() == ".exe" for p in files):
        problems.append(f"No application executable at payload root: {root}")
# This app has no defaults file to check for absolute paths.
print(json.dumps(problems))
'@
    $rawProblems = & $pythonPath -c $validationCode $resolvedDist
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the release payload.' }
    $problems = @($rawProblems | ConvertFrom-Json)
    if ($problems.Count) {
        foreach ($problem in $problems) { Write-Host $problem }
    }
    else {
        Write-Host "Release folder is clean: $resolvedDist"
        $exitCode = 0
    }
}
catch { Write-Host $_.Exception.Message }
finally { Pop-Location }
exit $exitCode

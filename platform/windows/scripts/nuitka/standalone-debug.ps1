#requires -Version 7.3
# Build the phist CLI for local troubleshooting, without the anti-debugger or
# signing, into its own output folder.
[CmdletBinding()]
param(
    [string]$PythonExecutable = '.venv/Scripts/python.exe',
    [string]$OutputDirectory,
    [string]$OutputFilename = 'phist.exe',
    [switch]$UseCurrentDefaultPaths,
    [switch]$ResetRuntimeDefaults
)
$ErrorActionPreference = 'Stop'
# The standalone entrypoint owns all build logic and the debug output default.
& (Join-Path $PSScriptRoot 'standalone.ps1') @PSBoundParameters -Console

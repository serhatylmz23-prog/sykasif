$ErrorActionPreference = "Stop"

Set-Location (
    Split-Path -Parent $PSScriptRoot
)

$env:PYTHONPATH = (Get-Location).Path

python -m terminal_v2.desktop.app

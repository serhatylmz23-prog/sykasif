param(
    [string]$SunucuAdresi = "http://127.0.0.1:8013"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# PSScriptRoot = <repo>\terminal_v2
# Depo kökü yalnız bir üst klasördür.
$repo = Split-Path `
    -Parent `
    $PSScriptRoot

Set-Location $repo

$python = Join-Path `
    $repo `
    ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "PYTHON_SANAL_ORTAM_BULUNAMADI : $python"
}

$env:SYK_TERMINAL_BASE_URL = $SunucuAdresi
$env:PYTHONPATH = $repo

Write-Host ""
Write-Host "============================================"
Write-Host "SYKASIF WINDOWS MASAUSTU BASLATIYOR"
Write-Host "DEPO    : $repo"
Write-Host "PYTHON  : $python"
Write-Host "SUNUCU  : $SunucuAdresi"
Write-Host "============================================"

& $python -m terminal_v2.desktop

if ($LASTEXITCODE -ne 0) {
    throw "WINDOWS_MASAUSTU_UYGULAMASI_BASLATILAMADI"
}

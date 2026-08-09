$ErrorActionPreference = "Stop"

Set-StrictMode -Version Latest

$root = "terminal_v2"
$port = 8013

$env:PYTHONPATH = (Get-Location).Path

Write-Host ""
Write-Host "===================================="
Write-Host "SYK TERMINAL V2"
Write-Host "RUNTIME START"
Write-Host "===================================="
Write-Host ""

$connection = Get-NetTCPConnection `
    -LocalPort $port `
    -State Listen `
    -ErrorAction SilentlyContinue

if ($null -ne $connection) {
    Write-Host "PORT_${port}_ALREADY_IN_USE"
    return
}

$ipv4 = Get-NetIPAddress `
    -AddressFamily IPv4 `
    -ErrorAction SilentlyContinue |
    Where-Object {
        $_.IPAddress -notlike "127.*" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.InterfaceOperationalStatus -eq "Up"
    } |
    Select-Object -First 1 -ExpandProperty IPAddress

if ([string]::IsNullOrWhiteSpace($ipv4)) {
    $ipv4 = "BULUNAMADI"
}

Write-Host "PC URL     : http://127.0.0.1:$port"
Write-Host "TABLET URL : http://${ipv4}:$port"
Write-Host "POWER GUARD: ACTIVE"
Write-Host ""

python "$root\run_terminal.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "TERMINAL_V2_RUNTIME_FAIL"
    return
}

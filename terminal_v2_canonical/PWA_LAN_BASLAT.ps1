param(
    [int]$Port = 8013
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "PYTHON_SANAL_ORTAM_BULUNAMADI : $python"
}

Set-Location $repo

Get-CimInstance Win32_Process |
Where-Object {
    $_.Name -match "^python(\.exe)?$" -and
    $_.CommandLine -like "*terminal_v2.app.main:app*"
} |
ForEach-Object {
    Stop-Process `
        -Id $_.ProcessId `
        -Force `
        -ErrorAction SilentlyContinue
}

$lanIp = Get-NetIPAddress `
    -AddressFamily IPv4 `
    -ErrorAction SilentlyContinue |
Where-Object {
    $_.IPAddress -notlike "127.*" -and
    $_.IPAddress -notlike "169.254.*" -and
    $_.InterfaceAlias -notmatch "Loopback|Bluetooth|vEthernet"
} |
Sort-Object InterfaceMetric |
Select-Object `
    -ExpandProperty IPAddress `
    -First 1

if (-not $lanIp) {
    throw "LAN_IP_ADRESI_BULUNAMADI"
}

$stdout = Join-Path `
    $env:TEMP `
    "sykasif_pwa_lan_stdout.log"

$stderr = Join-Path `
    $env:TEMP `
    "sykasif_pwa_lan_stderr.log"

Remove-Item `
    $stdout, $stderr `
    -Force `
    -ErrorAction SilentlyContinue

$runtime = Start-Process `
    -FilePath $python `
    -WorkingDirectory $repo `
    -ArgumentList @(
        "-m",
        "uvicorn",
        "terminal_v2.app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "$Port",
        "--log-level",
        "warning"
    ) `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

$hazir = $false

for ($deneme = 1; $deneme -le 15; $deneme++) {
    Start-Sleep -Seconds 1

    try {
        $response = Invoke-WebRequest `
            -Uri "http://127.0.0.1:$Port/pwa/?v=2" `
            -UseBasicParsing `
            -TimeoutSec 3

        if ($response.StatusCode -eq 200) {
            $hazir = $true
            break
        }
    }
    catch {
        continue
    }
}

if (-not $hazir) {
    if (Test-Path $stderr) {
        Get-Content $stderr
    }

    throw "PWA_LAN_RUNTIME_BASLATILAMADI"
}

$adres = "http://${lanIp}:$Port/pwa/?v=2"
$mobil = "http://${lanIp}:$Port/mobil"

Write-Host ""
Write-Host "============================================"
Write-Host "SYKASIF PWA LAN UZERINDE HAZIR"
Write-Host "PROCESS_ID : $($runtime.Id)"
Write-Host "PWA_ADRESI : $adres"
Write-Host "KISA_ADRES : $mobil"
Write-Host "============================================"
Write-Host ""
Write-Host "Samsung tablet, Android telefon ve iPhone:"
Write-Host "1. Masaustu ile ayni Wi-Fi agina baglan"
Write-Host "2. Tarayicida PWA_ADRESI adresini ac"
Write-Host "3. Modul kartina tiklayarak ortak durumu dogrula"
Write-Host ""

Start-Process "http://127.0.0.1:$Port/pwa/?v=2"

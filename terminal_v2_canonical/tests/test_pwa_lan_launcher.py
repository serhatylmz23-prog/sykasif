from pathlib import Path


def test_pwa_lan_launcher_exists():
    path = Path(
        "terminal_v2/PWA_LAN_BASLAT.ps1"
    )

    assert path.is_file()


def test_pwa_lan_launcher_uses_all_interfaces():
    text = Path(
        "terminal_v2/PWA_LAN_BASLAT.ps1"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert '"0.0.0.0"' in text
    assert '"terminal_v2.app.main:app"' in text
    assert "Get-NetIPAddress" in text


def test_pwa_lan_launcher_builds_mobile_address():
    text = Path(
        "terminal_v2/PWA_LAN_BASLAT.ps1"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert "/pwa/?v=2" in text
    assert "/mobil" in text
    assert "PWA_ADRESI" in text
    assert "$lanIp" in text
    assert "$Port" in text

def test_pwa_lan_launcher_uses_project_python():
    text = Path(
        "terminal_v2/PWA_LAN_BASLAT.ps1"
    ).read_text(
        encoding="utf-8-sig",
    )

    assert ".venv\\Scripts\\python.exe" in text
    assert "$PSScriptRoot" in text

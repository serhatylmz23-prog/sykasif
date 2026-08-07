from pathlib import Path


SCRIPT = Path(
    "terminal_v2/"
    "SPRINT_043_CANLI_MODUL_DOGRULA.ps1"
)


def source() -> str:
    assert SCRIPT.is_file()

    return SCRIPT.read_text(
        encoding="utf-8-sig",
    )


def test_launcher_starts_shared_runtime():
    text = source()

    assert "terminal_v2.app.main:app" in text
    assert '"0.0.0.0"' in text
    assert "Start-Process" in text


def test_launcher_validates_live_module_endpoints():
    text = source()

    assert "/api/v2/runtime-state" in text
    assert "/api/v2/modul-katalogu" in text
    assert "/api/v2/modul-islemleri/gecmis" in text
    assert "/api/v2/modul-islemleri/ozet" in text


def test_launcher_validates_pwa_assets():
    text = source()

    assert "/pwa/module_catalog.js" in text
    assert "/pwa/module_actions.js" in text
    assert "/pwa/module_history.js" in text
    assert "/pwa/service-worker.js" in text


def test_launcher_executes_real_module_action():
    text = source()

    assert "/api/v2/modul-islemleri/sec" in text
    assert "Invoke-RestMethod" in text
    assert "sprint-043-gorsel-dogrulama" in text
    assert "CANLI_MODUL_ISLEMI_BASARISIZ" in text


def test_launcher_outputs_local_and_lan_addresses():
    text = source()

    assert "Get-NetIPAddress" in text
    assert "YEREL_PWA" in text
    assert "LAN_PWA" in text
    assert "/pwa/?v=43" in text

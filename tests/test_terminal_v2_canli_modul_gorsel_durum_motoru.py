from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ENGINE = (
    ROOT
    / "terminal_v2"
    / "static"
    / "js"
    / "canli_modul_gorsel_durum_motoru.js"
)


def source():
    assert ENGINE.exists()
    return ENGINE.read_text(encoding="utf-8")


def test_motor_dosyasi_var():
    assert ENGINE.exists()


def test_gercek_event_sozlesmesi():
    assert (
        "sykasif:aktif-modul-guncellendi"
        in source()
    )


def test_gercek_payload_sozlesmesi():
    assert (
        "event?.detail?.aktif_modul"
        in source()
    )


def test_gercek_dom_selectoru():
    assert "[data-modul-kodu]" in source()


def test_dataset_modul_kodu():
    assert "dataset?.modulKodu" in source()


def test_secim_dataseti():
    assert (
        "dataset.sykModulSecim"
        in source()
    )


def test_runtime_durum_dataseti():
    assert (
        "dataset.sykModulDurum"
        in source()
    )


def test_hareket_dataseti():
    assert (
        "dataset.sykModulHareket"
        in source()
    )


def test_runtime_dom_kaynagi():
    assert (
        "[data-runtime-durum]"
        in source()
    )


def test_aktif_pasif_secim_durumlari():
    text = source()
    assert 'AKTIF: "aktif"' in text
    assert 'PASIF: "pasif"' in text


def test_runtime_yasam_durumlari():
    text = source()
    assert 'CALISIYOR: "calisiyor"' in text
    assert 'BEKLIYOR: "bekliyor"' in text
    assert 'DURDU: "durdu"' in text
    assert 'CEVRIMDISI: "cevrimdisi"' in text


def test_runtime_normalizer():
    assert (
        "runtimeDurumunuNormalizeEt"
        in source()
    )


def test_aria_current():
    assert '"aria-current"' in source()


def test_motor_bind_fonksiyonu():
    assert (
        "bindCanliModulGorselDurumMotoru"
        in source()
    )


def test_motor_kendiliginden_boot_etmiyor():
    assert (
        "bindCanliModulGorselDurumMotoru();"
        not in source()
    )

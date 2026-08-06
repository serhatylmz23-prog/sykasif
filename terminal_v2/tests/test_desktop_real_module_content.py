from terminal_v2.desktop.module_views import (
    modul_gorunumu_getir,
)


def test_harita_has_real_operations():
    gorunum = modul_gorunumu_getir("harita")

    assert gorunum.baslik == "Canlı Harita"
    assert len(gorunum.islemler) == 4
    assert "Harita katmanlarını yönet" in (
        gorunum.islemler
    )


def test_analiz_has_real_operations():
    gorunum = modul_gorunumu_getir("analiz")

    assert "Yeni analiz başlat" in (
        gorunum.islemler
    )
    assert "bilimsel" in gorunum.aciklama


def test_report_has_seal_operations():
    gorunum = modul_gorunumu_getir("rapor")

    assert "Manifest ve SHA üret" in (
        gorunum.islemler
    )
    assert "Mühürlü" in gorunum.aciklama


def test_operation_text_is_turkish():
    gorunum = modul_gorunumu_getir("kanit")

    assert gorunum.islem_metni.startswith("• ")
    assert "Kanıt zincirini doğrula" in (
        gorunum.islem_metni
    )

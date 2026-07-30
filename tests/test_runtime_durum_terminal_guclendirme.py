from syk_simulasyon.runtime_durumu import (
    RuntimeDurumu,
    RuntimeDurumTuru,
)
from syk_simulasyon.runtime_terminal import RuntimeTerminal


def test_adimlardan_ilerleme_yuzdesi_hesaplanir():
    durum = RuntimeDurumu()

    durum.adimlari_guncelle(
        tamamlanan_adim=3,
        toplam_adim=4,
        aktif_modul="Ara?t?rma",
    )

    gorunum = durum.gorunum()

    assert gorunum["ilerleme_yuzdesi"] == 75.0
    assert gorunum["tamamlanan_adim"] == 3
    assert gorunum["toplam_adim"] == 4
    assert gorunum["kalan_adim"] == 1


def test_hata_kaydi_turkce_aciklama_ile_gorunur():
    durum = RuntimeDurumu()

    durum.hata_kaydet(
        "Kaynak ba?lant?s? kurulamad?",
        aktif_modul="Ara?t?rma",
    )

    gorunum = durum.gorunum()

    assert gorunum["durum"] == RuntimeDurumTuru.HATA.value
    assert gorunum["son_hata"] == "Kaynak ba?lant?s? kurulamad?"


def test_risk_kaydi_eklenebilir_ve_temizlenebilir():
    durum = RuntimeDurumu()

    durum.risk_guncelle("Kaynak do?rulamas? bekleniyor")
    assert durum.gorunum()["risk"] == "Kaynak do?rulamas? bekleniyor"

    durum.risk_guncelle(None)
    assert durum.gorunum()["risk"] is None


def test_terminal_arayuzu_turkcedir():
    html = RuntimeTerminal().html()

    assert 'lang="tr"' in html
    assert "SYKA??F" in html
    assert "Ba?lang??" in html
    assert "Hedef" in html
    assert "Rota" in html

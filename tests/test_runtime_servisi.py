from syk_simulasyon.olay_omurgasi import OlayTuru
from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_servis_guvenli_baslangic_durumu_ile_acilir():
    servis = RuntimeServisi()

    gorunum = servis.gorunum()

    assert gorunum["durum"] == "başlatılıyor"
    assert gorunum["ilerleme_yuzdesi"] == 0.0
    assert gorunum["aktif_modul"] is None


def test_servis_tek_runtime_durumunu_korur():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=35.0,
    )

    gorunum = servis.gorunum()

    assert gorunum["durum"] == "çalışıyor"
    assert gorunum["aktif_modul"] == "DSP"
    assert gorunum["ilerleme_yuzdesi"] == 35.0


def test_servis_runtime_durumundan_olay_uretir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=60.0,
    )

    olay = servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0011",
    )

    assert olay.tur == OlayTuru.GOZLEM
    assert olay.ortak_veri["durum"] == "çalışıyor"
    assert olay.ortak_veri["aktif_modul"] == "DSP"
    assert olay.ortak_veri["ilerleme_yuzdesi"] == 60.0
import pytest

from syk_simulasyon.olay_omurgasi import OlayTuru
from syk_simulasyon.ortak_dil import Katman
from syk_simulasyon.runtime_durumu import RuntimeDurumu, RuntimeDurumTuru
from syk_simulasyon.runtime_olay_adaptoru import runtime_durumunu_olaya_cevir


def test_calisan_runtime_gozlem_olayina_donusur():
    durum = RuntimeDurumu()
    durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=45.0,
    )

    olay = runtime_durumunu_olaya_cevir(
        durum,
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0010",
    )

    assert olay.tur == OlayTuru.GOZLEM
    assert olay.kaynak == Katman.SIMULASYON
    assert olay.hedef == Katman.BILGE_KAAN
    assert olay.ozet_kodu == "RUNTIME-DURUM-GOZLEMI"
    assert olay.ortak_veri["durum"] == "çalışıyor"
    assert olay.ortak_veri["aktif_modul"] == "DSP"
    assert olay.ortak_veri["ilerleme_yuzdesi"] == 45.0


def test_tamamlanan_runtime_gorev_sonucu_olayina_donusur():
    durum = RuntimeDurumu()
    durum.durum_guncelle(
        durum=RuntimeDurumTuru.TAMAMLANDI,
        aktif_modul="DSP",
        ilerleme_yuzdesi=100.0,
    )

    olay = runtime_durumunu_olaya_cevir(
        durum,
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0010",
    )

    assert olay.tur == OlayTuru.GOREV_SONUCU
    assert olay.ozet_kodu == "RUNTIME-GOREV-SONUCU"


def test_guvenli_durdurulan_runtime_acil_durdurma_olayina_donusur():
    durum = RuntimeDurumu()
    durum.durum_guncelle(
        durum=RuntimeDurumTuru.GUVENLI_DURDURULDU,
        aktif_modul="çekirdek",
        ilerleme_yuzdesi=25.0,
    )

    olay = runtime_durumunu_olaya_cevir(
        durum,
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0010",
    )

    assert olay.tur == OlayTuru.ACIL_DURDUR
    assert olay.ozet_kodu == "RUNTIME-GUVENLI-DURDURMA"


def test_bos_arastirma_kimligi_reddedilir():
    durum = RuntimeDurumu()

    with pytest.raises(ValueError, match="Araştırma kimliği boş olamaz"):
        runtime_durumunu_olaya_cevir(
            durum,
            arastirma_kimligi="   ",
        )
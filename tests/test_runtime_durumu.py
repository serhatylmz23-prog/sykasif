import pytest

from syk_simulasyon.olay_omurgasi import Olay, OlayTuru
from syk_simulasyon.ortak_dil import Katman
from syk_simulasyon.runtime_durumu import RuntimeDurumu, RuntimeDurumTuru


def olay(tur: OlayTuru = OlayTuru.KANIT) -> Olay:
    return Olay.olustur(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0009-R1",
        tur=tur,
        kaynak=Katman.ANALIZ,
        hedef=Katman.BILGE_KAAN,
        ozet_kodu="DSP-0009-R1",
        ortak_veri={"kaynak": "runtime_testi"},
        ozel_veri={"dogrulama": True},
    )


def test_baslangic_durumu_guvenlidir():
    durum = RuntimeDurumu()
    gorunum = durum.gorunum()

    assert gorunum["durum"] == "başlatılıyor"
    assert gorunum["ilerleme_yuzdesi"] == 0.0
    assert gorunum["aktif_katman"] is None


def test_kanit_olayi_tamamlandi_demez_onay_bekler():
    durum = RuntimeDurumu()

    durum.olaydan_guncelle(olay(OlayTuru.KANIT))

    gorunum = durum.gorunum()
    assert gorunum["durum"] == "onay_bekliyor"
    assert gorunum["aktif_katman"] == "K90"
    assert gorunum["son_olay_turu"] == "O04"


def test_gorev_sonucu_bekleme_durumuna_gecer():
    durum = RuntimeDurumu()

    durum.olaydan_guncelle(olay(OlayTuru.GOREV_SONUCU))

    assert durum.durum == RuntimeDurumTuru.BEKLEMEDE


def test_acil_durdurma_guvenli_durdurma_durumu_uretir():
    durum = RuntimeDurumu()

    durum.olaydan_guncelle(olay(OlayTuru.ACIL_DURDUR))

    assert durum.durum == RuntimeDurumTuru.GUVENLI_DURDURULDU


@pytest.mark.parametrize("yuzde", [-0.01, 100.01])
def test_gecersiz_ilerleme_yuzdesi_reddedilir(yuzde):
    durum = RuntimeDurumu()

    with pytest.raises(ValueError):
        durum.durum_guncelle(
            durum=RuntimeDurumTuru.CALISIYOR,
            ilerleme_yuzdesi=yuzde,
        )


def test_yuzde_yuz_olmadan_tamamlandi_durumu_reddedilir():
    durum = RuntimeDurumu()

    with pytest.raises(ValueError):
        durum.durum_guncelle(
            durum=RuntimeDurumTuru.TAMAMLANDI,
            ilerleme_yuzdesi=99.0,
        )


def test_yuzde_yuz_ile_tamamlandi_durumu_kabul_edilir():
    durum = RuntimeDurumu()

    durum.durum_guncelle(
        durum=RuntimeDurumTuru.TAMAMLANDI,
        aktif_modul="DSP",
        ilerleme_yuzdesi=100.0,
    )

    gorunum = durum.gorunum()
    assert gorunum["durum"] == "tamamlandı"
    assert gorunum["aktif_modul"] == "DSP"
    assert gorunum["ilerleme_yuzdesi"] == 100.0
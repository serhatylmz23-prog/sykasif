from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_durumu import RuntimeDurumTuru

def test_anlik_gorunum_olusturulur():
    servis = RuntimeServisi()

    saglayici = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    gorunum = saglayici.gorunum()

    assert gorunum.durum == "başlatılıyor"
    assert gorunum.olay_sayisi == 0


def test_anlik_gorunum_sozluge_cevrilebilir():
    servis = RuntimeServisi()

    saglayici = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    sozluk = saglayici.gorunum().sozluk()

    assert "durum" in sozluk
    assert "ilerleme_yuzdesi" in sozluk
    assert "olay_sayisi" in sozluk


def test_runtime_degisimleri_gorunume_yansir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=25.0,
    )

    saglayici = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    gorunum = saglayici.gorunum()

    assert gorunum.aktif_modul == "DSP"
    assert gorunum.ilerleme_yuzdesi == 25.0
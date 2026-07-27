from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_baslangic_gorunumu_dogru_uretilir():
    servis = RuntimeServisi()
    izleme = RuntimeIzlemeSaglayicisi(servis)

    gorunum = izleme.gorunum()

    assert gorunum.durum == "başlatılıyor"
    assert gorunum.aktif_katman is None
    assert gorunum.aktif_modul is None
    assert gorunum.ilerleme_yuzdesi == 0.0
    assert gorunum.olay_sayisi == 0


def test_runtime_degisimleri_izleme_gorunumune_yansir():
    servis = RuntimeServisi()
    izleme = RuntimeIzlemeSaglayicisi(servis)

    servis.durum.durum_guncelle(
        durum=RuntimeDurumTuru.CALISIYOR,
        aktif_modul="DSP",
        ilerleme_yuzdesi=48.0,
    )

    gorunum = izleme.gorunum()

    assert gorunum.durum == "çalışıyor"
    assert gorunum.aktif_modul == "DSP"
    assert gorunum.ilerleme_yuzdesi == 48.0
    assert gorunum.guncelleme_zamani is not None


def test_olay_sayisi_gecmisten_hesaplanir():
    servis = RuntimeServisi()
    izleme = RuntimeIzlemeSaglayicisi(servis)

    servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0013-1",
    )
    servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0013-2",
    )

    gorunum = izleme.gorunum()

    assert gorunum.olay_sayisi == 2


def test_gorunum_sozluge_donusebilir():
    servis = RuntimeServisi()
    izleme = RuntimeIzlemeSaglayicisi(servis)

    sozluk = izleme.gorunum().sozluk()

    assert sozluk["durum"] == "başlatılıyor"
    assert sozluk["olay_sayisi"] == 0
    assert "ilerleme_yuzdesi" in sozluk
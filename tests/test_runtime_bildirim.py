from syk_simulasyon.olay_omurgasi import Olay, OlayTuru
from syk_simulasyon.ortak_dil import Katman
from syk_simulasyon.runtime_bildirim import RuntimeBildirimMerkezi


def olay() -> Olay:
    return Olay.olustur(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0014",
        tur=OlayTuru.GOZLEM,
        kaynak=Katman.SIMULASYON,
        hedef=Katman.BILGE_KAAN,
        ozet_kodu="RUNTIME-BILDIRIM",
        ortak_veri={"durum": "çalışıyor"},
        ozel_veri={},
    )


def test_abone_eklenebilir():
    merkez = RuntimeBildirimMerkezi()

    def abone(_olay: Olay) -> None:
        pass

    merkez.abone_ekle(abone)

    assert merkez.abone_sayisi == 1


def test_ayni_abone_iki_kez_eklenmez():
    merkez = RuntimeBildirimMerkezi()

    def abone(_olay: Olay) -> None:
        pass

    merkez.abone_ekle(abone)
    merkez.abone_ekle(abone)

    assert merkez.abone_sayisi == 1


def test_abone_silinebilir():
    merkez = RuntimeBildirimMerkezi()

    def abone(_olay: Olay) -> None:
        pass

    merkez.abone_ekle(abone)
    merkez.abone_sil(abone)

    assert merkez.abone_sayisi == 0


def test_olay_abonelere_gonderilir():
    merkez = RuntimeBildirimMerkezi()
    alinan: list[Olay] = []

    merkez.abone_ekle(alinan.append)

    beklenen = olay()
    merkez.yayinla(beklenen)

    assert alinan == [beklenen]


def test_bir_abone_hatasi_digerlerini_durdurmaz():
    merkez = RuntimeBildirimMerkezi()
    alinan: list[Olay] = []

    def hatali_abone(_olay: Olay) -> None:
        raise RuntimeError("abone hatası")

    merkez.abone_ekle(hatali_abone)
    merkez.abone_ekle(alinan.append)

    beklenen = olay()
    merkez.yayinla(beklenen)

    assert alinan == [beklenen]
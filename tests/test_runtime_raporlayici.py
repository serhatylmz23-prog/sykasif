from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_raporlayici import RuntimeRaporlayici
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_rapor_olusturulur():
    servis = RuntimeServisi()

    raporlayici = RuntimeRaporlayici(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    rapor = raporlayici.rapor_uret()

    assert rapor.baslik == "SyKaşif Runtime Raporu"
    assert rapor.durum == "başlatılıyor"
    assert rapor.olay_sayisi == 0


def test_rapor_sozluge_cevrilebilir():
    servis = RuntimeServisi()

    raporlayici = RuntimeRaporlayici(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    sozluk = raporlayici.rapor_uret().sozluk()

    assert "baslik" in sozluk
    assert "durum" in sozluk
    assert "olay_sayisi" in sozluk


def test_ozel_baslik_kullanilabilir():
    servis = RuntimeServisi()

    raporlayici = RuntimeRaporlayici(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    rapor = raporlayici.rapor_uret("Deneme Raporu")

    assert rapor.baslik == "Deneme Raporu"
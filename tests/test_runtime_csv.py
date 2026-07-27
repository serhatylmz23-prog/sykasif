import csv
import io

from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_csv_olusturulur():
    servis = RuntimeServisi()

    csv_saglayici = RuntimeCsvSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    veri = csv_saglayici.csv_uret()

    assert "durum" in veri
    assert "olay_sayisi" in veri


def test_csv_gecerlidir():
    servis = RuntimeServisi()

    csv_saglayici = RuntimeCsvSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    okuyucu = csv.DictReader(io.StringIO(csv_saglayici.csv_uret()))
    satirlar = list(okuyucu)

    assert len(satirlar) == 1


def test_csv_guncel_veriyi_icerir():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=servis.durum.durum,
        aktif_modul="DSP",
        ilerleme_yuzdesi=55.0,
    )

    csv_saglayici = RuntimeCsvSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    okuyucu = csv.DictReader(io.StringIO(csv_saglayici.csv_uret()))
    satir = next(okuyucu)

    assert satir["aktif_modul"] == "DSP"
    assert float(satir["ilerleme_yuzdesi"]) == 55.0
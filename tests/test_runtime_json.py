import json

from syk_simulasyon.runtime_anlik_gorunum import RuntimeAnlikGorunumSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_servisi import RuntimeServisi


def test_json_olusturulur():
    servis = RuntimeServisi()

    json_saglayici = RuntimeJsonSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    veri = json.loads(json_saglayici.json_uret())

    assert veri["durum"] == "başlatılıyor"
    assert veri["olay_sayisi"] == 0


def test_json_gecerlidir():
    servis = RuntimeServisi()

    json_saglayici = RuntimeJsonSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    veri = json.loads(json_saglayici.json_uret())

    assert isinstance(veri, dict)
    assert "ilerleme_yuzdesi" in veri


def test_json_guncel_veriyi_doner():
    servis = RuntimeServisi()

    servis.durum.durum_guncelle(
        durum=servis.durum.durum,
        aktif_modul="DSP",
        ilerleme_yuzdesi=42.0,
    )

    json_saglayici = RuntimeJsonSaglayicisi(
        RuntimeAnlikGorunumSaglayicisi(
            RuntimeIzlemeSaglayicisi(servis)
        )
    )

    veri = json.loads(json_saglayici.json_uret())

    assert veri["aktif_modul"] == "DSP"
    assert veri["ilerleme_yuzdesi"] == 42.0
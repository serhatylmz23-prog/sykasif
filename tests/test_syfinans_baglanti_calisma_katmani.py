import json
import os

import pytest

from syk_finans_otagi.baglanti_calisma_katmani import (
    BaglantiAyarlari,
    FinansAgIstemcisi,
    KaynakSaglikDurumu,
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)


def ayarlar(
    **degisiklikler,
):
    degerler = {
        "saglayici_id": "deneme-kaynak",
        "temel_adres": (
            "https://ornek.invalid"
        ),
        "zaman_asimi_saniyesi": 1,
        "yeniden_deneme_sayisi": 2,
        "yeniden_deneme_bekleme_saniyesi": 0,
        "asgari_istek_araligi_saniyesi": 0,
    }

    degerler.update(
        degisiklikler
    )

    return BaglantiAyarlari(
        **degerler
    )


def test_canli_json_yaniti_alinir_ve_muhurlenir():
    def tasiyici(
        adres,
        basliklar,
        zaman_asimi,
    ):
        assert (
            adres
            == "https://ornek.invalid/piyasa"
        )

        assert (
            basliklar["Accept"]
            == "application/json"
        )

        assert zaman_asimi == 1

        return (
            200,
            json.dumps(
                {
                    "sembol": "ASELS",
                    "fiyat": 300,
                }
            ).encode("utf-8"),
        )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(),
        tasiyici=tasiyici,
        uyku=lambda _: None,
    )

    sonuc = istemci.getir(
        yol="/piyasa",
    )

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.CANLI
    )

    assert not sonuc.cevrimdisi

    assert (
        sonuc.veri["sembol"]
        == "ASELS"
    )

    assert len(
        sonuc.yanit_sha256
    ) == 64

    assert (
        istemci.saglik_durumu().durum
        == KaynakSaglikDurumu.SAGLIKLI
    )


def test_hata_sonrasi_kontrollu_yeniden_dener():
    sayac = {
        "adet": 0,
    }

    def tasiyici(
        adres,
        basliklar,
        zaman_asimi,
    ):
        sayac["adet"] += 1

        if sayac["adet"] < 3:
            raise TimeoutError(
                "Geçici zaman aşımı"
            )

        return (
            200,
            b'{"durum": "tamam"}',
        )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(),
        tasiyici=tasiyici,
        uyku=lambda _: None,
    )

    sonuc = istemci.getir(
        yol="/yeniden-dene",
    )

    assert sayac["adet"] == 3

    assert sonuc.deneme_sayisi == 3

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.CANLI
    )


def test_canli_baglanti_yoksa_son_guvenilir_yanit_kullanilir():
    depo = SonGuvenilirYanitDeposu()

    depo.kaydet(
        anahtar="ASELS",
        veri={
            "sembol": "ASELS",
            "fiyat": 299,
        },
    )

    def hatali_tasiyici(
        adres,
        basliklar,
        zaman_asimi,
    ):
        raise ConnectionError(
            "Bağlantı yok"
        )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(
            yeniden_deneme_sayisi=0,
        ),
        depo=depo,
        tasiyici=hatali_tasiyici,
        uyku=lambda _: None,
    )

    sonuc = istemci.getir(
        yol="/piyasa",
        depo_anahtari="ASELS",
    )

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.SON_GUVENILIR
    )

    assert sonuc.cevrimdisi

    assert (
        sonuc.veri["fiyat"]
        == 299
    )


def test_depo_yoksa_yerel_ornek_kullanilir():
    def hatali_tasiyici(
        adres,
        basliklar,
        zaman_asimi,
    ):
        raise ConnectionError(
            "Ağ yok"
        )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(
            yeniden_deneme_sayisi=0,
        ),
        yerel_ornekler={
            "ASELS": {
                "sembol": "ASELS",
                "fiyat": 298,
            }
        },
        tasiyici=hatali_tasiyici,
        uyku=lambda _: None,
    )

    sonuc = istemci.getir(
        yol="/piyasa",
        yerel_ornek_anahtari=(
            "ASELS"
        ),
    )

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.YEREL_ORNEK
    )

    assert sonuc.cevrimdisi


def test_gizli_anahtar_ortam_degikeninden_alinir(
    monkeypatch,
):
    monkeypatch.setenv(
        "SYFINANS_DENEME_ANAHTARI",
        "gizli-deger",
    )

    yakalanan = {}

    def tasiyici(
        adres,
        basliklar,
        zaman_asimi,
    ):
        yakalanan.update(
            basliklar
        )

        return (
            200,
            b'{"durum": "tamam"}',
        )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(
            gizli_anahtar_ortam_degikeni=(
                "SYFINANS_DENEME_ANAHTARI"
            ),
        ),
        tasiyici=tasiyici,
        uyku=lambda _: None,
    )

    istemci.getir(
        yol="/gizli",
    )

    assert (
        yakalanan["Authorization"]
        == "Bearer gizli-deger"
    )


def test_gizli_anahtar_yoksa_acik_hata_uretilir(
    monkeypatch,
):
    monkeypatch.delenv(
        "SYFINANS_EKSIK_ANAHTAR",
        raising=False,
    )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(
            gizli_anahtar_ortam_degikeni=(
                "SYFINANS_EKSIK_ANAHTAR"
            ),
        ),
        tasiyici=lambda *args: (
            200,
            b"{}",
        ),
        uyku=lambda _: None,
    )

    with pytest.raises(
        RuntimeError,
        match="gizli anahtar",
    ):
        istemci.getir(
            yol="/gizli",
        )


def test_uc_ardisik_hata_kaynagi_erisilemez_yapar():
    def hatali_tasiyici(
        adres,
        basliklar,
        zaman_asimi,
    ):
        raise TimeoutError(
            "Zaman aşımı"
        )

    istemci = FinansAgIstemcisi(
        ayarlar=ayarlar(
            yeniden_deneme_sayisi=2,
        ),
        yerel_ornekler={
            "yerel": {
                "durum": "yerel"
            }
        },
        tasiyici=hatali_tasiyici,
        uyku=lambda _: None,
    )

    istemci.getir(
        yol="/hata",
        yerel_ornek_anahtari=(
            "yerel"
        ),
    )

    assert (
        istemci.saglik_durumu().durum
        == KaynakSaglikDurumu
        .ERISILEMIYOR
    )

    assert (
        istemci
        .saglik_durumu()
        .ardisik_hata_sayisi
        == 3
    )


def test_son_guvenilir_yanit_diske_yazilir(
    tmp_path,
):
    yol = (
        tmp_path
        / "son_guvenilir.json"
    )

    depo = SonGuvenilirYanitDeposu(
        dosya_yolu=yol,
    )

    depo.kaydet(
        anahtar="USDTRY",
        veri={
            "fiyat": 40.1,
        },
    )

    yeniden = SonGuvenilirYanitDeposu(
        dosya_yolu=yol,
    )

    assert (
        yeniden.getir(
            anahtar="USDTRY"
        )["fiyat"]
        == 40.1
    )
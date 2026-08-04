from decimal import Decimal

import pytest

from syk_finans_otagi.baglanti_calisma_katmani import (
    SonGuvenilirYanitDeposu,
    YanitKaynagi,
)
from syk_finans_otagi.modeller import (
    VeriAkisDurumu,
)
from syk_finans_otagi.tcmb_guvenli_calisma import (
    TcmbGuvenliBagdastiricisi,
)


XML_ORNEGI = """<?xml version="1.0" encoding="UTF-8"?>
<Tarih_Date Tarih="03.08.2026" Date="08/03/2026">
    <Currency Kod="USD" CurrencyCode="USD">
        <Unit>1</Unit>
        <ForexBuying>47.4497</ForexBuying>
        <ForexSelling>47.5352</ForexSelling>
    </Currency>
    <Currency Kod="EUR" CurrencyCode="EUR">
        <Unit>1</Unit>
        <ForexBuying>54.6882</ForexBuying>
        <ForexSelling>54.7867</ForexSelling>
    </Currency>
</Tarih_Date>
""".encode("utf-8")


def test_canli_tcmb_yaniti_depolanir():
    depo = SonGuvenilirYanitDeposu()

    kaynak = TcmbGuvenliBagdastiricisi(
        depo=depo,
        tasiyici=(
            lambda adres, zaman_asimi:
            XML_ORNEGI
        ),
    )

    sonuc = kaynak.kurlari_getir()

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.CANLI
    )

    assert not sonuc.cevrimdisi

    assert depo.var_mi(
        anahtar=(
            kaynak.DEPO_ANAHTARI
        )
    )


def test_baglanti_kesilince_son_guvenilir_kayit_kullanilir():
    depo = SonGuvenilirYanitDeposu()

    canli = TcmbGuvenliBagdastiricisi(
        depo=depo,
        tasiyici=(
            lambda adres, zaman_asimi:
            XML_ORNEGI
        ),
    )

    canli.kurlari_getir()

    def kesik_tasiyici(
        adres,
        zaman_asimi,
    ):
        raise TimeoutError(
            "İnternet bağlantısı yok"
        )

    kesik = TcmbGuvenliBagdastiricisi(
        depo=depo,
        tasiyici=kesik_tasiyici,
    )

    sonuc = kesik.kurlari_getir()

    assert sonuc.cevrimdisi

    assert (
        sonuc.yanit_kaynagi
        == YanitKaynagi.SON_GUVENILIR
    )

    assert (
        "Son güvenilir"
        in sonuc.kullanici_aciklamasi
    )


def test_cevrimdisi_piyasa_verisi_acikca_isaretlenir():
    depo = SonGuvenilirYanitDeposu()

    depo.kaydet(
        anahtar=(
            TcmbGuvenliBagdastiricisi
            .DEPO_ANAHTARI
        ),
        veri={
            "xml": XML_ORNEGI.decode(
                "utf-8"
            ),
            "kayit_zamani": (
                "2026-08-03T15:30:00+03:00"
            ),
            "veri_tarihi": (
                "08/03/2026"
            ),
        },
    )

    kaynak = TcmbGuvenliBagdastiricisi(
        depo=depo,
        tasiyici=lambda *args: (
            (_ for _ in ())
            .throw(
                ConnectionError(
                    "Bağlantı yok"
                )
            )
        ),
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="USDTRY"
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.CEVRIMDISI
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("47.4925")
    )


def test_canli_veri_gecikmeli_resmi_veri_olarak_isaretlenir():
    kaynak = TcmbGuvenliBagdastiricisi(
        tasiyici=(
            lambda adres, zaman_asimi:
            XML_ORNEGI
        ),
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="EURTRY"
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.GECIKMELI
    )

    assert (
        sonuc.guven_profili.resmi
    )


def test_depo_yoksa_baglanti_hatasi_uretilir():
    kaynak = TcmbGuvenliBagdastiricisi(
        tasiyici=lambda *args: (
            (_ for _ in ())
            .throw(
                TimeoutError(
                    "Zaman aşımı"
                )
            )
        ),
    )

    with pytest.raises(
        ConnectionError,
        match="son güvenilir",
    ):
        kaynak.kurlari_getir()


def test_son_durum_kullanici_aciklamasi_uretir():
    kaynak = TcmbGuvenliBagdastiricisi(
        tasiyici=(
            lambda adres, zaman_asimi:
            XML_ORNEGI
        ),
    )

    kaynak.kurlari_getir()

    durum = kaynak.son_durum()

    assert durum["durum"] == "canli"

    assert (
        "gösterge kuru"
        in durum[
            "kullanici_aciklamasi"
        ]
    )
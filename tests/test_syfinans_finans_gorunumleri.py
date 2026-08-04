from datetime import UTC, datetime
from decimal import Decimal

from syk_finans_otagi.capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from syk_finans_otagi.finans_calisma_profili import (
    SyFinansCalismaProfili,
)
from syk_finans_otagi.finans_gorunumleri import (
    FinansGorunumMotoru,
)
from syk_finans_otagi.finans_kaynak_merkezi import (
    FinansKaynakMerkezi,
)
from syk_finans_otagi.gercek_kaynak_sozlesmeleri import (
    FinansKaynakSinifi,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)
from syk_finans_otagi.veri_saglayicilari import (
    PiyasaVerisi,
    VeriDogruLamaMotoru,
)


ZAMAN = datetime.now(
    UTC
).isoformat()


class DenemeKaynak:
    saglayici_id = "bist-deneme"
    kaynak_sinifi = (
        FinansKaynakSinifi.BIST
    )

    def piyasa_verisi_getir(
        self,
        *,
        sembol,
    ):
        veri = PiyasaVerisi(
            sembol=sembol,
            varlik_turu=(
                VarlikTuru.HISSE
            ),
            fiyat=Decimal("350"),
            para_birimi="TRY",
            zaman_damgasi=ZAMAN,
            kaynak="Deneme",
            saglayici_id=(
                self.saglayici_id
            ),
            veri_durumu=(
                VeriAkisDurumu.ANLIK
            ),
            dogrulandi=True,
        )

        veri = (
            VeriDogruLamaMotoru
            .muhurle(veri)
        )

        profil = KaynakGuvenProfili(
            saglayici_id=(
                self.saglayici_id
            ),
            kaynak_turu=(
                KaynakTuru
                .LISANSLI_PIYASA
            ),
            temel_guven_puani=90,
            guncellik_puani=90,
            gecmis_tutarlilik_puani=90,
            kesinti_dayanim_puani=85,
            lisansli=True,
            resmi=False,
        )

        return KaynakliPiyasaVerisi(
            veri=veri,
            guven_profili=profil,
        )


def motor():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemeKaynak()
        ]
    )

    profil = SyFinansCalismaProfili(
        merkez=merkez
    )

    return FinansGorunumMotoru(
        calisma_profili=profil
    )


def test_piyasa_karti_uretilir():
    kart = motor().piyasa_karti_uret(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    assert (
        kart.fiyat
        == Decimal("350.0000")
    )

    assert (
        kart.veri_akis_durumu
        == VeriAkisDurumu.ANLIK
    )

    assert len(
        kart.kanit_sha256
    ) == 64


def test_kasa_karti_kar_zarar_hesaplar():
    kart = motor().kasa_karti_uret(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
        miktar=100,
        ortalama_maliyet=300,
    )

    assert (
        kart.toplam_maliyet
        == Decimal("30000.0000")
    )

    assert (
        kart.guncel_deger
        == Decimal("35000.0000")
    )

    assert (
        kart.kar_zarar
        == Decimal("5000.0000")
    )

    assert (
        kart.kar_zarar_orani
        == 16.667
    )


def test_kaynak_saglik_karti_uretilir():
    gorunum = motor()

    gorunum.piyasa_karti_uret(
        sembol="ASELS",
        varlik_turu=(
            VarlikTuru.HISSE
        ),
    )

    kartlar = (
        gorunum
        .kaynak_saglik_kartlari()
    )

    assert len(
        kartlar
    ) == 1

    assert (
        kartlar[0].durum
        == "hazir"
    )

    assert (
        kartlar[0].basari_orani
        == 100.0
    )


def test_gorunum_paketi_uretilir():
    paket = motor().paket_uret(
        piyasa_varliklari=[
            (
                "ASELS",
                VarlikTuru.HISSE,
            )
        ],
        kasa_varliklari=[
            {
                "sembol": "ASELS",
                "varlik_turu": (
                    VarlikTuru.HISSE
                ),
                "miktar": 100,
                "ortalama_maliyet": 300,
            }
        ],
    )

    assert len(
        paket.piyasa_kartlari
    ) == 1

    assert len(
        paket.kasa_kartlari
    ) == 1

    assert len(
        paket.kaynak_saglik_kartlari
    ) == 1

    assert len(
        paket.paket_sha256
    ) == 64

    assert (
        paket.as_dict()["schema"]
        == "syfinans-gorunum-paketi/v1"
    )


def test_gorunum_kartlari_jsona_donusebilir():
    paket = motor().paket_uret(
        piyasa_varliklari=[
            (
                "ASELS",
                VarlikTuru.HISSE,
            )
        ],
    )

    veri = paket.as_dict()

    assert (
        veri["piyasa_kartlari"][0][
            "sembol"
        ]
        == "ASELS"
    )

    assert (
        veri["piyasa_kartlari"][0][
            "fiyat"
        ]
        == 350.0
    )
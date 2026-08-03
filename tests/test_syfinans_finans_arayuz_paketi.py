from datetime import UTC, datetime
from decimal import Decimal

from syk_finans_otagi.capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from syk_finans_otagi.finans_arayuz_paketi import (
    BilgiSatiriDurumu,
    EkranSinifi,
    FinansArayuzMotoru,
    FinansSekmesi,
)
from syk_finans_otagi.finans_calisma_profili import (
    SyFinansCalismaProfili,
)
from syk_finans_otagi.finans_gorunumleri import (
    FinansGorunumMotoru,
)
from syk_finans_otagi.finans_grafik_gecmisi import (
    FinansGrafikMotoru,
    FiyatGecmisDeposu,
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

    gorunum = FinansGorunumMotoru(
        calisma_profili=profil
    )

    depo = FiyatGecmisDeposu()

    for sira, fiyat in enumerate(
        (
            "300",
            "325",
            "350",
        )
    ):
        depo.kaydet(
            sembol="ASELS",
            fiyat=fiyat,
            zaman=(
                datetime(
                    2026,
                    8,
                    sira + 1,
                    tzinfo=UTC,
                ).isoformat()
            ),
            kaynak="bist-deneme",
        )

    grafik = FinansGrafikMotoru(
        depo=depo
    )

    return FinansArayuzMotoru(
        gorunum_motoru=gorunum,
        grafik_motoru=grafik,
    )


def test_piyasa_sekmesi_tek_pakette_uretilir():
    paket = motor().piyasa_sekmesi(
        varliklar=[
            (
                "ASELS",
                VarlikTuru.HISSE,
            )
        ],
        ekran_genisligi=1440,
    )

    assert (
        paket.sekme
        == FinansSekmesi.PIYASA
    )

    assert (
        paket.ekran_sinifi
        == EkranSinifi.MASAUSTU
    )

    assert len(
        paket.kartlar
    ) >= 1

    assert len(
        paket.grafikler
    ) == 1

    assert len(
        paket.paket_sha256
    ) == 64


def test_piyasa_bilgi_satiri_canli_veriyi_gosterir():
    paket = motor().piyasa_sekmesi(
        varliklar=[
            (
                "ASELS",
                VarlikTuru.HISSE,
            )
        ],
        ekran_genisligi=390,
    )

    assert (
        paket.ekran_sinifi
        == EkranSinifi.TELEFON
    )

    assert (
        paket.bilgi_satiri.durum
        == BilgiSatiriDurumu.CANLI
    )

    assert (
        paket.bilgi_satiri
        .gecikme_saniyesi
        == 0
    )


def test_kasam_sekmesi_kar_zarar_ve_grafik_uretir():
    paket = motor().kasam_sekmesi(
        varliklar=[
            {
                "sembol": "ASELS",
                "varlik_turu": (
                    VarlikTuru.HISSE
                ),
                "miktar": 100,
                "ortalama_maliyet": 300,
            }
        ],
        ekran_genisligi=800,
    )

    assert (
        paket.sekme
        == FinansSekmesi.KASAM
    )

    assert (
        paket.ekran_sinifi
        == EkranSinifi.TABLET
    )

    assert (
        paket.kartlar[0][
            "kar_zarar"
        ]
        == 5000.0
    )

    assert len(
        paket.grafikler
    ) == 1


def test_analiz_sekmesi_kanitli_kart_uretir():
    paket = motor().analiz_sekmesi(
        analizler=[
            {
                "sembol": "ASELS",
                "varlik_turu": (
                    VarlikTuru.HISSE
                ),
                "guncel_fiyat": 350,
                "ortalama_maliyet": 300,
                "kar_zarar": 5000,
                "kar_zarar_orani": 16.667,
                "risk_puani": 35,
                "guven_puani": 82,
                "kanit_gucu": 88,
                "aciklama": (
                    "Kanıt ağırlıklı "
                    "değerlendirme."
                ),
            }
        ],
        ekran_genisligi=1440,
    )

    assert (
        paket.sekme
        == FinansSekmesi.ANALIZ
    )

    assert (
        paket.kartlar[0][
            "guven_puani"
        ]
        == 82.0
    )

    assert len(
        paket.kartlar[0][
            "kanit_sha256"
        ]
    ) == 64


def test_planlar_sekmesi_gerceklesme_orani_hesaplar():
    paket = motor().planlar_sekmesi(
        planlar=[
            {
                "plan_id": "PLAN-001",
                "sembol": "ASELS",
                "plan_turu": (
                    "kademeli_alim"
                ),
                "toplam_butce": 100000,
                "kademe_sayisi": 4,
                "gerceklesen_kademe_sayisi": 3,
                "ortalama_maliyet": 297.50,
                "durum": "izleniyor",
            }
        ],
        ekran_genisligi=390,
    )

    assert (
        paket.sekme
        == FinansSekmesi.PLANLAR
    )

    assert (
        paket.kartlar[0][
            "gerceklesme_orani"
        ]
        == 75.0
    )

    assert len(
        paket.kartlar[0][
            "kanit_sha256"
        ]
    ) == 64


def test_tum_sekme_paketleri_jsona_donusebilir():
    piyasa = motor().piyasa_sekmesi(
        varliklar=[
            (
                "ASELS",
                VarlikTuru.HISSE,
            )
        ],
        ekran_genisligi=1440,
    ).as_dict()

    assert (
        piyasa["schema"]
        == "syfinans-sekme-paketi/v1"
    )

    assert (
        piyasa["sekme"]
        == "piyasa"
    )

    assert (
        piyasa["ekran_sinifi"]
        == "masaustu"
    )
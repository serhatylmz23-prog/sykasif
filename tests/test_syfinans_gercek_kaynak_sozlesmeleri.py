from datetime import UTC, datetime
from decimal import Decimal

import pytest

from syk_finans_otagi.capraz_dogrulama import (
    CaprazDogrulamaMotoru,
    DogrulamaDurumu,
    KaynakGuvenProfili,
    KaynakTuru,
)
from syk_finans_otagi.gercek_kaynak_sozlesmeleri import (
    BildirimOnemi,
    BistPiyasaKaydi,
    DenemeGercekKaynakBagdastiricisi,
    DovizKaydi,
    FinansKaynakHavuzu,
    FinansKaynakSinifi,
    FonKaydi,
    KapBildirimi,
    KapBildirimDogrulamaMotoru,
    KiymetliMadenKaydi,
)
from syk_finans_otagi.modeller import (
    VarlikTuru,
    VeriAkisDurumu,
)


ZAMAN = datetime.now(
    UTC
).isoformat()


def profil(
    kimlik: str,
    *,
    puan: float = 90,
) -> KaynakGuvenProfili:
    return KaynakGuvenProfili(
        saglayici_id=kimlik,
        kaynak_turu=(
            KaynakTuru.LISANSLI_PIYASA
        ),
        temel_guven_puani=puan,
        guncellik_puani=puan,
        gecmis_tutarlilik_puani=puan,
        kesinti_dayanim_puani=80,
        lisansli=True,
        resmi=False,
    )


def bist_kaynagi(
    kimlik: str,
    fiyat: str,
):
    return (
        DenemeGercekKaynakBagdastiricisi(
            saglayici_id=kimlik,
            kaynak_sinifi=(
                FinansKaynakSinifi.BIST
            ),
            guven_profili=profil(
                kimlik
            ),
            kayitlar={
                "ASELS": BistPiyasaKaydi(
                    sembol="ASELS",
                    son_fiyat=Decimal(
                        fiyat
                    ),
                    alis_fiyati=Decimal(
                        "299.90"
                    ),
                    satis_fiyati=Decimal(
                        "300.10"
                    ),
                    hacim=Decimal(
                        "250000000"
                    ),
                    degisim_orani=1.25,
                    zaman_damgasi=ZAMAN,
                )
            },
        )
    )


def test_bist_kaydi_ortak_piyasa_verisine_donusur():
    sonuc = bist_kaynagi(
        "bist-a",
        "300.00",
    ).piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.veri.varlik_turu
        == VarlikTuru.HISSE
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("300.0000")
    )

    assert (
        sonuc.veri.hacim
        == Decimal("250000000.0000")
    )

    assert len(
        sonuc.veri.veri_sha256
    ) == 64


def test_iki_bist_kaynagi_capraz_dogrulanir():
    havuz = FinansKaynakHavuzu(
        bagdastiricilar=[
            bist_kaynagi(
                "bist-a",
                "300.00",
            ),
            bist_kaynagi(
                "bist-b",
                "300.15",
            ),
        ]
    )

    veriler = havuz.verileri_getir(
        sembol="ASELS"
    )

    sonuc = (
        CaprazDogrulamaMotoru
        .dogrula(
            veriler=veriler,
        )
    )

    assert (
        sonuc.dogrulama_durumu
        == DogrulamaDurumu.DOGRULANDI
    )

    assert (
        sonuc.kabul_edilen_kaynak_sayisi
        == 2
    )


def test_fon_kaydi_ortak_veriye_donusur():
    kaynak = (
        DenemeGercekKaynakBagdastiricisi(
            saglayici_id="fon-a",
            kaynak_sinifi=(
                FinansKaynakSinifi.FON
            ),
            guven_profili=profil(
                "fon-a"
            ),
            kayitlar={
                "FON-A": FonKaydi(
                    fon_kodu="FON-A",
                    fon_adi="Deneme Fonu",
                    birim_fiyat=Decimal(
                        "2.4567"
                    ),
                    toplam_deger=Decimal(
                        "100000000"
                    ),
                    yatirimci_sayisi=2500,
                    portfoy_dagilimi={
                        "Hisse": 60,
                        "Tahvil": 30,
                        "Nakit": 10,
                    },
                    zaman_damgasi=ZAMAN,
                )
            },
        )
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="FON-A"
    )

    assert (
        sonuc.veri.varlik_turu
        == VarlikTuru.FON
    )

    assert (
        sonuc.veri.fiyat
        == Decimal("2.4567")
    )


def test_doviz_alis_satis_orta_fiyat_uretir():
    kayit = DovizKaydi(
        kod="USDTRY",
        alis_fiyati=Decimal(
            "40.00"
        ),
        satis_fiyati=Decimal(
            "40.20"
        ),
        zaman_damgasi=ZAMAN,
        kaynak_turu="resmi",
    )

    assert (
        kayit.orta_fiyat
        == Decimal("40.1000")
    )


def test_altin_ve_gumus_desteklenir():
    for kod, tur in (
        (
            "ALTIN",
            VarlikTuru.ALTIN,
        ),
        (
            "GUMUS",
            VarlikTuru.GUMUS,
        ),
    ):
        kaynak = (
            DenemeGercekKaynakBagdastiricisi(
                saglayici_id=f"{kod}-a",
                kaynak_sinifi=(
                    FinansKaynakSinifi
                    .KIYMETLI_MADEN
                ),
                guven_profili=profil(
                    f"{kod}-a"
                ),
                kayitlar={
                    kod: KiymetliMadenKaydi(
                        kod=kod,
                        maden_adi=kod,
                        birim="gram",
                        alis_fiyati=Decimal(
                            "100"
                        ),
                        satis_fiyati=Decimal(
                            "102"
                        ),
                        zaman_damgasi=ZAMAN,
                    )
                },
            )
        )

        sonuc = kaynak.piyasa_verisi_getir(
            sembol=kod
        )

        assert (
            sonuc.veri.varlik_turu
            == tur
        )


def test_kap_bildirimi_muhurlenir():
    bildirim = KapBildirimi(
        bildirim_id="KAP-001",
        sembol="ASELS",
        baslik="Yeni iş ilişkisi",
        yayin_zamani=ZAMAN,
        bildirim_turu=(
            "Özel durum açıklaması"
        ),
        ozet=(
            "Deneme amaçlı KAP bildirimi."
        ),
        kaynak_adresi=(
            "https://ornek.invalid/KAP-001"
        ),
        onem=BildirimOnemi.ONEMLI,
    )

    muhurlu = (
        KapBildirimDogrulamaMotoru
        .muhurle(bildirim)
    )

    assert (
        muhurlu.dogrulanmis
    )

    assert len(
        muhurlu.bildirim_sha256
    ) == 64

    assert (
        KapBildirimDogrulamaMotoru
        .dogrula(muhurlu)
    )


def test_fon_dagilimi_yuzde_yuzu_asiri_sapamaz():
    with pytest.raises(
        ValueError,
        match="yüzde 100",
    ):
        FonKaydi(
            fon_kodu="FON-X",
            fon_adi="Hatalı Fon",
            birim_fiyat=Decimal("1"),
            toplam_deger=None,
            yatirimci_sayisi=None,
            portfoy_dagilimi={
                "Hisse": 80,
                "Tahvil": 80,
            },
            zaman_damgasi=ZAMAN,
        )


def test_doviz_satis_fiyati_alistan_dusuk_olamaz():
    with pytest.raises(
        ValueError,
        match="düşük olamaz",
    ):
        DovizKaydi(
            kod="EURTRY",
            alis_fiyati=Decimal(
                "45.00"
            ),
            satis_fiyati=Decimal(
                "44.00"
            ),
            zaman_damgasi=ZAMAN,
            kaynak_turu="resmi",
        )


def test_gecikmeli_kaynak_durumu_korunur():
    kaynak = (
        DenemeGercekKaynakBagdastiricisi(
            saglayici_id="bist-gecikmeli",
            kaynak_sinifi=(
                FinansKaynakSinifi.BIST
            ),
            guven_profili=profil(
                "bist-gecikmeli"
            ),
            kayitlar={
                "ASELS": BistPiyasaKaydi(
                    sembol="ASELS",
                    son_fiyat=Decimal(
                        "300"
                    ),
                    alis_fiyati=None,
                    satis_fiyati=None,
                    hacim=None,
                    degisim_orani=None,
                    zaman_damgasi=ZAMAN,
                )
            },
            veri_durumu=(
                VeriAkisDurumu.GECIKMELI
            ),
            gecikme_saniyesi=900,
        )
    )

    sonuc = kaynak.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.veri.veri_durumu
        == VeriAkisDurumu.GECIKMELI
    )

    assert (
        sonuc.veri.gecikme_saniyesi
        == 900
    )
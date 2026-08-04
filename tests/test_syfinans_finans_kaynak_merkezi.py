from datetime import UTC, datetime
from decimal import Decimal

import pytest

from syk_finans_otagi.capraz_dogrulama import (
    KaynakGuvenProfili,
    KaynakliPiyasaVerisi,
    KaynakTuru,
)
from syk_finans_otagi.finans_kaynak_merkezi import (
    FinansKaynakMerkezi,
    KaynakMerkeziDurumu,
)
from syk_finans_otagi.gercek_kaynak_sozlesmeleri import (
    BildirimOnemi,
    FinansKaynakSinifi,
    KapBildirimi,
    KapBildirimDogrulamaMotoru,
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


class DenemePiyasaKaynagi:
    def __init__(
        self,
        *,
        kimlik: str,
        fiyat: str,
        kaynak_sinifi: (
            FinansKaynakSinifi
        ) = FinansKaynakSinifi.BIST,
        durum: VeriAkisDurumu = (
            VeriAkisDurumu.ANLIK
        ),
        hata: bool = False,
    ) -> None:
        self._kimlik = kimlik
        self.fiyat = Decimal(
            fiyat
        )
        self._kaynak_sinifi = (
            kaynak_sinifi
        )
        self.durum = durum
        self.hata = hata

    @property
    def saglayici_id(self):
        return self._kimlik

    @property
    def kaynak_sinifi(self):
        return self._kaynak_sinifi

    def piyasa_verisi_getir(
        self,
        *,
        sembol: str,
    ):
        if self.hata:
            raise ConnectionError(
                "Deneme bağlantı hatası"
            )

        veri = PiyasaVerisi(
            sembol=sembol,
            varlik_turu=(
                VarlikTuru.HISSE
            ),
            fiyat=self.fiyat,
            para_birimi="TRY",
            zaman_damgasi=ZAMAN,
            kaynak=self._kimlik,
            saglayici_id=(
                self._kimlik
            ),
            veri_durumu=(
                self.durum
            ),
            dogrulandi=True,
        )

        muhurlu = (
            VeriDogruLamaMotoru
            .muhurle(veri)
        )

        profil = KaynakGuvenProfili(
            saglayici_id=(
                self._kimlik
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
            veri=muhurlu,
            guven_profili=profil,
        )


class DenemeKapKaynagi:
    saglayici_id = "kap-deneme"

    def bildirimleri_getir(
        self,
        *,
        sembol=None,
        limit=50,
    ):
        bildirim = KapBildirimi(
            bildirim_id="KAP-001",
            sembol=(
                sembol or "ASELS"
            ),
            baslik="Yeni İş İlişkisi",
            yayin_zamani=ZAMAN,
            bildirim_turu=(
                "Özel Durum Açıklaması"
            ),
            ozet=(
                "Yeni sözleşme imzalandı."
            ),
            kaynak_adresi=(
                "https://ornek.invalid/kap"
            ),
            onem=BildirimOnemi.ONEMLI,
        )

        return (
            KapBildirimDogrulamaMotoru
            .muhurle(
                bildirim
            ),
        )


def test_piyasa_kaynagi_merkeze_eklenir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-a",
                fiyat="300",
            )
        ]
    )

    snapshot = merkez.snapshot()

    assert (
        snapshot["kaynak_sayisi"]
        == 1
    )

    assert len(
        snapshot["snapshot_sha256"]
    ) == 64


def test_tek_kaynaktan_piyasa_verisi_alinir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-a",
                fiyat="300",
            )
        ]
    )

    sonuc = merkez.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.secilen_fiyat
        == Decimal("300")
    )

    assert (
        sonuc.kullanilan_kaynaklar
        == ("bist-a",)
    )

    assert len(
        sonuc.merkez_sha256
    ) == 64


def test_iki_kaynak_capraz_dogrulanir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-a",
                fiyat="300.00",
            ),
            DenemePiyasaKaynagi(
                kimlik="bist-b",
                fiyat="300.10",
            ),
        ]
    )

    sonuc = merkez.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.capraz_dogrulama
        is not None
    )

    assert (
        sonuc.capraz_dogrulama
        .kabul_edilen_kaynak_sayisi
        == 2
    )


def test_hata_veren_kaynak_atlanir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-a",
                fiyat="300",
            ),
            DenemePiyasaKaynagi(
                kimlik="bist-hatali",
                fiyat="0",
                hata=True,
            ),
        ]
    )

    sonuc = merkez.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.basarisiz_kaynaklar
        == ("bist-hatali",)
    )

    durum = merkez.kaynak_durumu_getir(
        "bist-hatali"
    )

    assert (
        durum.durum
        == KaynakMerkeziDurumu
        .ERISILEMIYOR
    )


def test_gecikmeli_veri_merkez_sonucuna_yansir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-gecikmeli",
                fiyat="300",
                durum=(
                    VeriAkisDurumu
                    .GECIKMELI
                ),
            )
        ]
    )

    sonuc = merkez.piyasa_verisi_getir(
        sembol="ASELS"
    )

    assert (
        sonuc.veri_akis_durumu
        == VeriAkisDurumu.GECIKMELI
    )


def test_kap_bildirimleri_merkezden_alinir():
    merkez = FinansKaynakMerkezi(
        kap_kaynaklari=[
            DenemeKapKaynagi()
        ]
    )

    sonuc = merkez.kap_bildirimleri_getir(
        sembol="ASELS"
    )

    assert len(
        sonuc.bildirimler
    ) == 1

    assert (
        sonuc.bildirimler[0]
        .dogrulanmis
    )

    assert len(
        sonuc.merkez_sha256
    ) == 64


def test_ayni_kaynak_kimligi_tekrar_eklenemez():
    kaynak = DenemePiyasaKaynagi(
        kimlik="bist-a",
        fiyat="300",
    )

    with pytest.raises(
        ValueError,
        match="daha önce",
    ):
        FinansKaynakMerkezi(
            piyasa_kaynaklari=[
                kaynak,
                kaynak,
            ]
        )


def test_hicbir_kaynak_veri_uretemezse_hata_verilir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-hatali",
                fiyat="0",
                hata=True,
            )
        ]
    )

    with pytest.raises(
        ConnectionError,
        match="Hiçbir finans kaynağı",
    ):
        merkez.piyasa_verisi_getir(
            sembol="ASELS"
        )


def test_basarili_istek_kaynak_durumuna_yansir():
    merkez = FinansKaynakMerkezi(
        piyasa_kaynaklari=[
            DenemePiyasaKaynagi(
                kimlik="bist-a",
                fiyat="300",
            )
        ]
    )

    merkez.piyasa_verisi_getir(
        sembol="ASELS"
    )

    durum = merkez.kaynak_durumu_getir(
        "bist-a"
    )

    assert (
        durum.durum
        == KaynakMerkeziDurumu.HAZIR
    )

    assert (
        durum.basari_orani
        == 100.0
    )
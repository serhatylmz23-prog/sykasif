from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_field_link import (
    KesifDurumu,
    SahaCihazAdayi,
    SahaCihazBaglantiBilgisi,
    SahaCihazEslestirmeYoneticisi,
    SahaCihazKesifYoneticisi,
    SahaCihazTuru,
    SahaCihazYonetimHatasi,
    SahaCihazYoneticisi,
)


class ElleSaat:
    def __init__(self) -> None:
        self.simdi = datetime(
            2026,
            8,
            5,
            2,
            30,
            tzinfo=UTC,
        )

    def oku(self) -> datetime:
        return self.simdi

    def ilerlet(
        self,
        *,
        saniye: int = 0,
    ) -> None:
        self.simdi += timedelta(
            seconds=saniye
        )


def sistem_olustur():
    saat = ElleSaat()

    yonetici = SahaCihazYoneticisi(
        eslestirme=(
            SahaCihazEslestirmeYoneticisi(
                saat=saat.oku,
                kod_gecerlilik_dakikasi=10,
                azami_deneme_sayisi=3,
                ana_gizli_deger=(
                    "SAHA-ESLESTIRME-GIZLI"
                ),
            )
        ),
        kesif=SahaCihazKesifYoneticisi(
            saat=saat.oku,
            cevrimdisi_suresi_saniye=30,
            kayit_silme_suresi_dakika=60,
        ),
    )

    tablet = SahaCihazAdayi(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_adi="Samsung Ana Saha Terminali",
        cihaz_turu=SahaCihazTuru.TABLET,
        cihaz_parmak_izi=(
            "SAMSUNG-TABLET-PARMAK-IZI"
        ),
        yerel_ag_adresi="192.168.1.20",
        yetenekler=frozenset(
            {
                "terminal",
                "kamera",
                "konum",
            }
        ),
    )

    baglanti = SahaCihazBaglantiBilgisi(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "SAMSUNG-TABLET-PARMAK-IZI"
        ),
        ag_adresi="192.168.1.20",
        hizmet_noktasi=8014,
    )

    return saat, yonetici, tablet, baglanti


def eslestir():
    saat, yonetici, tablet, baglanti = (
        sistem_olustur()
    )

    istek, kod = yonetici.eslestirme_baslat(
        tablet
    )

    yonetici.eslestirmeyi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    istek, cihaz = (
        yonetici.eslestirmeyi_tamamla(
            istek.istek_kimligi,
            kod=kod,
            baglanti=baglanti,
        )
    )

    return (
        saat,
        yonetici,
        istek,
        cihaz,
    )


def test_eslestirme_ve_kesif_birlesir() -> None:
    _, _, istek, cihaz = eslestir()

    assert istek.tamamlandi_mi
    assert cihaz.bagli_mi


def test_oturum_anahtari_kesif_kaydina_baglanir() -> None:
    _, _, istek, cihaz = eslestir()

    assert istek.oturum_anahtari
    assert cihaz.oturum_anahtari_ozeti


def test_eslesen_cihaz_ag_adresini_tasir() -> None:
    _, _, _, cihaz = eslestir()

    assert cihaz.ag_adresi == (
        "192.168.1.20"
    )
    assert cihaz.hizmet_noktasi == 8014


def test_farkli_cihaz_kimligi_reddedilir() -> None:
    _, yonetici, tablet, _ = (
        sistem_olustur()
    )

    istek, kod = yonetici.eslestirme_baslat(
        tablet
    )

    yonetici.eslestirmeyi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    yanlis_baglanti = (
        SahaCihazBaglantiBilgisi(
            cihaz_kimligi="BASKA-CIHAZ",
            cihaz_parmak_izi=(
                tablet.cihaz_parmak_izi
            ),
            ag_adresi="192.168.1.99",
            hizmet_noktasi=8014,
        )
    )

    with pytest.raises(
        SahaCihazYonetimHatasi,
        match="uyuşmuyor",
    ):
        yonetici.eslestirmeyi_tamamla(
            istek.istek_kimligi,
            kod=kod,
            baglanti=yanlis_baglanti,
        )


def test_zaman_asimi_cihazi_cevrimdisi_yapar() -> None:
    saat, yonetici, _, cihaz = eslestir()

    saat.ilerlet(
        saniye=31
    )

    degisenler = (
        yonetici
        .zaman_asimlarini_kontrol_et()
    )

    assert cihaz in degisenler
    assert (
        cihaz.durum
        is KesifDurumu.CEVRIMDISI
    )


def test_oturum_anahtariyla_yeniden_baglanir() -> None:
    saat, yonetici, istek, cihaz = eslestir()

    saat.ilerlet(
        saniye=31
    )

    yonetici.zaman_asimlarini_kontrol_et()

    sonuc = yonetici.yeniden_baglan(
        baglanti=SahaCihazBaglantiBilgisi(
            cihaz_kimligi=(
                cihaz.cihaz_kimligi
            ),
            cihaz_parmak_izi=(
                cihaz.cihaz_parmak_izi
            ),
            ag_adresi="192.168.1.25",
            hizmet_noktasi=8014,
        ),
        oturum_anahtari=(
            istek.oturum_anahtari or ""
        ),
    )

    assert sonuc.bagli_mi
    assert sonuc.ag_adresi == (
        "192.168.1.25"
    )


def test_durum_ozeti_birlesik_yapidadir() -> None:
    _, yonetici, _, _ = eslestir()

    ozet = yonetici.durum_ozeti()

    assert ozet[
        "sistem_durumu"
    ] == "hazır"
    assert "eşleştirme" in ozet
    assert "keşif" in ozet
    assert (
        ozet["keşif"][
            "bağlı_cihaz_sayısı"
        ]
        == 1
    )

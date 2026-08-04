from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_field_link import (
    KesifDurumu,
    SahaCihazKesifYoneticisi,
    SahaKesifHatasi,
)


class ElleSaat:
    def __init__(self) -> None:
        self.simdi = datetime(
            2026,
            8,
            5,
            2,
            0,
            tzinfo=UTC,
        )

    def oku(self) -> datetime:
        return self.simdi

    def ilerlet(
        self,
        *,
        saniye: int = 0,
        dakika: int = 0,
    ) -> None:
        self.simdi += timedelta(
            seconds=saniye,
            minutes=dakika,
        )


def sistem_olustur():
    saat = ElleSaat()

    yonetici = SahaCihazKesifYoneticisi(
        saat=saat.oku,
        cevrimdisi_suresi_saniye=30,
        kayit_silme_suresi_dakika=60,
    )

    return saat, yonetici


def tablet_bildir(
    yonetici: SahaCihazKesifYoneticisi,
):
    return yonetici.cihaz_bildir(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_adi="Samsung Ana Saha Terminali",
        cihaz_turu="tablet",
        cihaz_parmak_izi=(
            "SAMSUNG-TABLET-PARMAK-IZI"
        ),
        ag_adresi="192.168.1.20",
        hizmet_noktasi=8014,
        yetenekler={
            "terminal",
            "kamera",
            "konum",
        },
    )


def test_tablet_kesfedilir() -> None:
    _, yonetici = sistem_olustur()

    cihaz = tablet_bildir(
        yonetici
    )

    assert (
        cihaz.durum
        is KesifDurumu.GORULDU
    )


def test_kesfedilen_cihaz_listelenir() -> None:
    _, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    assert len(
        yonetici.cihazlari_listele()
    ) == 1


def test_oturum_anahtariyla_dogrulanir() -> None:
    _, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    cihaz = yonetici.cihazi_dogrula(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "SAMSUNG-TABLET-PARMAK-IZI"
        ),
        oturum_anahtari=(
            "SAHA-OTURUM-ANAHTARI"
        ),
    )

    assert cihaz.bagli_mi
    assert cihaz.oturum_anahtari_ozeti


def test_yanlis_parmak_izi_dogrulanamaz() -> None:
    _, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    with pytest.raises(
        SahaKesifHatasi,
        match="parmak izi",
    ):
        yonetici.cihazi_dogrula(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi="YANLIS",
            oturum_anahtari="ANAHTAR",
        )


def test_kayitli_parmak_izi_degistirilemez() -> None:
    _, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    with pytest.raises(
        SahaKesifHatasi,
        match="değiştirilemez",
    ):
        yonetici.cihaz_bildir(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_adi="Taklit cihaz",
            cihaz_turu="tablet",
            cihaz_parmak_izi=(
                "FARKLI-PARMAK-IZI"
            ),
            ag_adresi="192.168.1.99",
            hizmet_noktasi=8014,
        )


def test_zaman_asimi_cevrimdisi_yapar() -> None:
    saat, yonetici = sistem_olustur()

    cihaz = tablet_bildir(
        yonetici
    )

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


def test_dogru_anahtarla_yeniden_baglanir() -> None:
    saat, yonetici = sistem_olustur()

    cihaz = tablet_bildir(
        yonetici
    )

    yonetici.cihazi_dogrula(
        cihaz_kimligi=(
            cihaz.cihaz_kimligi
        ),
        cihaz_parmak_izi=(
            cihaz.cihaz_parmak_izi
        ),
        oturum_anahtari=(
            "SAHA-OTURUM-ANAHTARI"
        ),
    )

    saat.ilerlet(
        saniye=31
    )

    yonetici.zaman_asimlarini_kontrol_et()

    sonuc = yonetici.yeniden_baglan(
        cihaz_kimligi=(
            cihaz.cihaz_kimligi
        ),
        cihaz_parmak_izi=(
            cihaz.cihaz_parmak_izi
        ),
        oturum_anahtari=(
            "SAHA-OTURUM-ANAHTARI"
        ),
        ag_adresi="192.168.1.25",
        hizmet_noktasi=8014,
    )

    assert sonuc.bagli_mi
    assert sonuc.ag_adresi == (
        "192.168.1.25"
    )
    assert (
        sonuc.yeniden_baglanma_sayisi
        == 1
    )


def test_yanlis_anahtarla_yeniden_baglanamaz() -> None:
    saat, yonetici = sistem_olustur()

    cihaz = tablet_bildir(
        yonetici
    )

    yonetici.cihazi_dogrula(
        cihaz_kimligi=(
            cihaz.cihaz_kimligi
        ),
        cihaz_parmak_izi=(
            cihaz.cihaz_parmak_izi
        ),
        oturum_anahtari="DOGRU",
    )

    saat.ilerlet(
        saniye=31
    )

    yonetici.zaman_asimlarini_kontrol_et()

    with pytest.raises(
        SahaKesifHatasi,
        match="anahtarı",
    ):
        yonetici.yeniden_baglan(
            cihaz_kimligi=(
                cihaz.cihaz_kimligi
            ),
            cihaz_parmak_izi=(
                cihaz.cihaz_parmak_izi
            ),
            oturum_anahtari="YANLIS",
            ag_adresi="192.168.1.25",
            hizmet_noktasi=8014,
        )


def test_anahtarsiz_cihaz_yeniden_baglanamaz() -> None:
    _, yonetici = sistem_olustur()

    cihaz = tablet_bildir(
        yonetici
    )

    with pytest.raises(
        SahaKesifHatasi,
        match="kayıtlı oturum anahtarı",
    ):
        yonetici.yeniden_baglan(
            cihaz_kimligi=(
                cihaz.cihaz_kimligi
            ),
            cihaz_parmak_izi=(
                cihaz.cihaz_parmak_izi
            ),
            oturum_anahtari="ANAHTAR",
            ag_adresi="192.168.1.25",
            hizmet_noktasi=8014,
        )


def test_eski_cevrimdisi_kayit_temizlenir() -> None:
    saat, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    saat.ilerlet(
        saniye=31
    )

    yonetici.zaman_asimlarini_kontrol_et()

    saat.ilerlet(
        dakika=61
    )

    silinenler = (
        yonetici
        .eski_kayitlari_temizle()
    )

    assert silinenler == (
        "SAMSUNG-TABLET",
    )


def test_denetim_kayitlari_tutulur() -> None:
    _, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    olaylar = {
        kayit.olay
        for kayit
        in yonetici.denetim_kayitlari()
    }

    assert "cihaz_keşfedildi" in olaylar


def test_durum_ozeti_turkcedir() -> None:
    _, yonetici = sistem_olustur()

    tablet_bildir(
        yonetici
    )

    ozet = yonetici.durum_ozeti()

    assert ozet[
        "keşfedilen_cihaz_sayısı"
    ] == 1
    assert "bağlı_cihaz_sayısı" in ozet
    assert "çevrimdışı_cihaz_sayısı" in ozet
    assert "cihazlar" in ozet

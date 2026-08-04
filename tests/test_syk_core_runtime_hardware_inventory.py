from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_hardware_validation import (
    BaglantiTuru,
    DogrulamaSonucu,
    DonanimDogrulamaHatasi,
    DonanimDurumu,
    DonanimEnvanteri,
    DonanimKimligi,
    DonanimTuru,
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
        saniye: int = 1,
    ) -> None:
        self.simdi += timedelta(
            seconds=saniye
        )


def sistem_olustur():
    saat = ElleSaat()

    envanter = DonanimEnvanteri(
        saat=saat.oku
    )

    tablet = DonanimKimligi(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_adi="Samsung Ana Saha Terminali",
        donanim_turu=DonanimTuru.TABLET,
        uretici="Samsung",
        model="Galaxy Tab",
        seri_numarasi="TEST-SERI-001",
        parmak_izi="TABLET-PARMAK-IZI",
    )

    return saat, envanter, tablet


def test_gercek_cihaz_envantere_kaydedilir() -> None:
    _, envanter, tablet = sistem_olustur()

    kayit = envanter.cihaz_kaydet(
        tablet,
        yetenekler={
            "terminal",
            "kamera",
            "konum",
        },
    )

    assert (
        kayit.durum
        is DonanimDurumu.KAYITLI
    )

    assert kayit.gercek_donanim_mi is True


def test_ayni_cihaz_iki_kez_kaydedilemez() -> None:
    _, envanter, tablet = sistem_olustur()

    envanter.cihaz_kaydet(
        tablet
    )

    with pytest.raises(
        DonanimDogrulamaHatasi,
        match="daha önce",
    ):
        envanter.cihaz_kaydet(
            tablet
        )


def test_usb_baglantisi_kaydedilir() -> None:
    _, envanter, tablet = sistem_olustur()

    cihaz = envanter.cihaz_kaydet(
        tablet
    )

    baglanti = envanter.baglanti_kaydi_ekle(
        tablet.cihaz_kimligi,
        baglanti_turu=BaglantiTuru.USB,
        baglanti_adresi="USB:VID_0001",
        baglandi_mi=True,
        gecikme_milisaniye=4.2,
    )

    assert baglanti.baglandi_mi is True
    assert (
        cihaz.durum
        is DonanimDurumu.BAGLI
    )


def test_basarisiz_baglanti_hata_durumu_olusturur() -> None:
    _, envanter, tablet = sistem_olustur()

    cihaz = envanter.cihaz_kaydet(
        tablet
    )

    envanter.baglanti_kaydi_ekle(
        tablet.cihaz_kimligi,
        baglanti_turu=BaglantiTuru.WIFI,
        baglanti_adresi="192.168.1.20",
        baglandi_mi=False,
        hata="Cihaz yanıt vermedi.",
    )

    assert (
        cihaz.durum
        is DonanimDurumu.HATALI
    )


def test_donanim_testi_baslatilir() -> None:
    _, envanter, tablet = sistem_olustur()

    cihaz = envanter.cihaz_kaydet(
        tablet
    )

    test = envanter.test_baslat(
        tablet.cihaz_kimligi,
        test_adi="Canlı bağlantı testi",
    )

    assert (
        test.sonuc
        is DogrulamaSonucu.BEKLIYOR
    )

    assert (
        cihaz.durum
        is DonanimDurumu.BEKLIYOR
    )


def test_basarili_test_cihazi_dogrular() -> None:
    saat, envanter, tablet = sistem_olustur()

    cihaz = envanter.cihaz_kaydet(
        tablet
    )

    envanter.test_baslat(
        tablet.cihaz_kimligi,
        test_adi="Kamera veri akışı",
    )

    saat.ilerlet()

    sonuc = envanter.test_tamamla(
        tablet.cihaz_kimligi,
        sonuc=DogrulamaSonucu.BASARILI,
        olcumler={
            "kare_hızı": 30,
            "gecikme_ms": 18.4,
        },
    )

    assert (
        sonuc.sonuc
        is DogrulamaSonucu.BASARILI
    )

    assert cihaz.dogrulandi_mi


def test_basarisiz_test_hata_durumu_olusturur() -> None:
    _, envanter, tablet = sistem_olustur()

    cihaz = envanter.cihaz_kaydet(
        tablet
    )

    envanter.test_baslat(
        tablet.cihaz_kimligi,
        test_adi="Sensör bağlantısı",
    )

    envanter.test_tamamla(
        tablet.cihaz_kimligi,
        sonuc=DogrulamaSonucu.BASARISIZ,
        aciklama="Sensör bulunamadı.",
    )

    assert (
        cihaz.durum
        is DonanimDurumu.HATALI
    )


def test_acik_test_yokken_tamamlama_reddedilir() -> None:
    _, envanter, tablet = sistem_olustur()

    envanter.cihaz_kaydet(
        tablet
    )

    with pytest.raises(
        DonanimDogrulamaHatasi,
        match="açık donanım testi",
    ):
        envanter.test_tamamla(
            tablet.cihaz_kimligi,
            sonuc=DogrulamaSonucu.BASARILI,
        )


def test_donanim_notu_eklenir() -> None:
    _, envanter, tablet = sistem_olustur()

    cihaz = envanter.cihaz_kaydet(
        tablet
    )

    envanter.not_ekle(
        tablet.cihaz_kimligi,
        "Saha testi henüz yapılmadı.",
    )

    assert cihaz.notlar == [
        "Saha testi henüz yapılmadı."
    ]


def test_dogrulanan_cihazlar_listelenir() -> None:
    _, envanter, tablet = sistem_olustur()

    envanter.cihaz_kaydet(
        tablet
    )

    envanter.test_baslat(
        tablet.cihaz_kimligi,
        test_adi="Temel doğrulama",
    )

    envanter.test_tamamla(
        tablet.cihaz_kimligi,
        sonuc=DogrulamaSonucu.BASARILI,
    )

    assert len(
        envanter
        .dogrulanan_cihazlari_listele()
    ) == 1


def test_denetim_kaydi_tutulur() -> None:
    _, envanter, tablet = sistem_olustur()

    envanter.cihaz_kaydet(
        tablet
    )

    olaylar = {
        kayit.olay
        for kayit
        in envanter.denetim_kayitlari()
    }

    assert (
        "cihaz_envantere_kaydedildi"
        in olaylar
    )


def test_durum_ozeti_turkcedir() -> None:
    _, envanter, tablet = sistem_olustur()

    envanter.cihaz_kaydet(
        tablet
    )

    ozet = envanter.durum_ozeti()

    assert ozet[
        "toplam_cihaz_sayısı"
    ] == 1

    assert ozet[
        "gerçek_donanım_sayısı"
    ] == 1

    assert (
        ozet[
            "gerçek_donanım_doğrulaması"
        ]
        == "başladı"
    )

    assert "cihazlar" in ozet

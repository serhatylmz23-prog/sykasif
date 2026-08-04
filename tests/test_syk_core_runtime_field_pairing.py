from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_field_link import (
    EslestirmeDurumu,
    SahaCihazAdayi,
    SahaCihazEslestirmeYoneticisi,
    SahaCihazTuru,
    SahaEslestirmeHatasi,
)


class ElleSaat:
    def __init__(self) -> None:
        self.simdi = datetime(
            2026,
            8,
            5,
            1,
            30,
            tzinfo=UTC,
        )

    def oku(self) -> datetime:
        return self.simdi

    def ilerlet(self, dakika: int) -> None:
        self.simdi += timedelta(
            minutes=dakika
        )


def sistem_olustur():
    saat = ElleSaat()

    yonetici = SahaCihazEslestirmeYoneticisi(
        saat=saat.oku,
        kod_gecerlilik_dakikasi=10,
        azami_deneme_sayisi=3,
        ana_gizli_deger="SYK-TEST-GIZLI",
    )

    tablet = SahaCihazAdayi(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_adi="Samsung Ana Saha Terminali",
        cihaz_turu=SahaCihazTuru.TABLET,
        cihaz_parmak_izi="SAMSUNG-TABLET-PARMAK-IZI",
        yerel_ag_adresi="192.168.1.20",
        uygulama_surumu="0.1.0",
        sistem_surumu="Android",
        yetenekler=frozenset(
            {
                "terminal",
                "kamera",
                "konum",
                "bildirim",
            }
        ),
    )

    return saat, yonetici, tablet


def test_eslestirme_istegi_olusturulur() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, kod = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    assert (
        istek.durum
        is EslestirmeDurumu.ONAY_BEKLIYOR
    )
    assert len(kod) == 6
    assert kod.isdigit()


def test_kod_acik_saklanmaz() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, kod = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    assert istek.kod_ozeti != kod
    assert len(istek.kod_ozeti) == 64


def test_ayni_cihaz_icin_ikinci_istek_reddedilir() -> None:
    _, yonetici, tablet = sistem_olustur()

    yonetici.eslestirme_istegi_olustur(
        tablet
    )

    with pytest.raises(
        SahaEslestirmeHatasi,
        match="açık bir eşleştirme",
    ):
        yonetici.eslestirme_istegi_olustur(
            tablet
        )


def test_yetkisiz_onay_reddedilir() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, _ = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    with pytest.raises(
        SahaEslestirmeHatasi,
        match="Bilge Kaan",
    ):
        yonetici.istegi_onayla(
            istek.istek_kimligi,
            onaylayan="işletmen",
        )


def test_bilge_kaan_onaylar() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, _ = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    sonuc = yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    assert (
        sonuc.durum
        is EslestirmeDurumu.ONAYLANDI
    )


def test_onaysiz_eslestirme_tamamlanamaz() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, kod = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    with pytest.raises(
        SahaEslestirmeHatasi,
        match="önce yetkili",
    ):
        yonetici.eslestirmeyi_tamamla(
            istek.istek_kimligi,
            kod=kod,
            cihaz_parmak_izi=(
                tablet.cihaz_parmak_izi
            ),
        )


def test_dogru_kodla_eslestirme_tamamlanir() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, kod = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    sonuc = yonetici.eslestirmeyi_tamamla(
        istek.istek_kimligi,
        kod=kod,
        cihaz_parmak_izi=(
            tablet.cihaz_parmak_izi
        ),
    )

    assert sonuc.tamamlandi_mi
    assert sonuc.oturum_anahtari
    assert (
        len(
            yonetici
            .eslesen_cihazlari_listele()
        )
        == 1
    )


def test_yanlis_kod_reddedilir() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, _ = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    with pytest.raises(
        SahaEslestirmeHatasi,
        match="kodu doğrulanamadı",
    ):
        yonetici.eslestirmeyi_tamamla(
            istek.istek_kimligi,
            kod="000000",
            cihaz_parmak_izi=(
                tablet.cihaz_parmak_izi
            ),
        )


def test_yanlis_parmak_izi_reddedilir() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, kod = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    with pytest.raises(
        SahaEslestirmeHatasi,
        match="parmak izi",
    ):
        yonetici.eslestirmeyi_tamamla(
            istek.istek_kimligi,
            kod=kod,
            cihaz_parmak_izi="YANLIS",
        )


def test_uc_yanlis_deneme_istegi_reddeder() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, _ = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    for _ in range(3):
        with pytest.raises(
            SahaEslestirmeHatasi
        ):
            yonetici.eslestirmeyi_tamamla(
                istek.istek_kimligi,
                kod="111111",
                cihaz_parmak_izi=(
                    tablet.cihaz_parmak_izi
                ),
            )

    assert (
        istek.durum
        is EslestirmeDurumu.REDDEDILDI
    )


def test_suresi_gecen_istek_tamamlanamaz() -> None:
    saat, yonetici, tablet = sistem_olustur()

    istek, kod = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    saat.ilerlet(11)

    with pytest.raises(
        SahaEslestirmeHatasi
    ):
        yonetici.eslestirmeyi_tamamla(
            istek.istek_kimligi,
            kod=kod,
            cihaz_parmak_izi=(
                tablet.cihaz_parmak_izi
            ),
        )

    assert (
        istek.durum
        is EslestirmeDurumu.SURESI_DOLDU
    )


def test_kurucu_kaan_istegi_reddeder() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, _ = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    sonuc = yonetici.istegi_reddet(
        istek.istek_kimligi,
        gerekce="Cihaz doğrulanmadı.",
        reddeden="Kurucu Kaan",
    )

    assert (
        sonuc.durum
        is EslestirmeDurumu.REDDEDILDI
    )


def test_denetim_kaydi_tutulur() -> None:
    _, yonetici, tablet = sistem_olustur()

    istek, _ = (
        yonetici.eslestirme_istegi_olustur(
            tablet
        )
    )

    yonetici.istegi_onayla(
        istek.istek_kimligi,
        onaylayan="Bilge Kaan",
    )

    olaylar = {
        kayit.olay
        for kayit
        in yonetici.denetim_kayitlari()
    }

    assert (
        "eşleştirme_isteği_oluşturuldu"
        in olaylar
    )
    assert "eşleştirme_onaylandı" in olaylar


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    _, yonetici, tablet = sistem_olustur()

    yonetici.eslestirme_istegi_olustur(
        tablet
    )

    ozet = yonetici.durum_ozeti()

    assert ozet[
        "toplam_istek_sayısı"
    ] == 1
    assert ozet[
        "onay_bekleyen_istek_sayısı"
    ] == 1
    assert "eşleşmiş_cihazlar" in ozet

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_terminal import (
    CalismaTerminali,
    CihazTuru,
    MesajDurumu,
    MesajTuru,
    OturumDurumu,
    OturumHatasi,
    TerminalOturumYoneticisi,
    YetkiliCihazTanimi,
    YetkiSeviyesi,
)


class ElleSaat:
    def __init__(
        self,
        simdi: datetime,
    ) -> None:
        self.simdi = simdi

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
    saat = ElleSaat(
        datetime(
            2026,
            8,
            4,
            21,
            0,
            tzinfo=UTC,
        )
    )

    terminal = CalismaTerminali(
        saat=saat.oku
    )

    terminal.cihaz_kaydet(
        YetkiliCihazTanimi(
            cihaz_kimligi="SAMSUNG-TABLET",
            ad="Samsung Ana Saha Terminali",
            cihaz_turu=CihazTuru.TABLET,
            yetki_seviyesi=(
                YetkiSeviyesi.BILGE_KAAN
            ),
            cihaz_parmak_izi=(
                "TABLET-PARMAK-IZI"
            ),
        )
    )

    terminal.cihaz_kaydet(
        YetkiliCihazTanimi(
            cihaz_kimligi="IPHONE-8-PLUS",
            ad="iPhone Yetkili Yardımcı Terminal",
            cihaz_turu=CihazTuru.TELEFON,
            yetki_seviyesi=(
                YetkiSeviyesi.OPERATOR
            ),
            cihaz_parmak_izi=(
                "IPHONE-PARMAK-IZI"
            ),
        )
    )

    terminal.cihaz_kaydet(
        YetkiliCihazTanimi(
            cihaz_kimligi="ANA-MASAUSTU",
            ad="SyKaşif Ana Makine",
            cihaz_turu=CihazTuru.MASAUSTU,
            yetki_seviyesi=(
                YetkiSeviyesi.KURUCU_KAAN
            ),
            cihaz_parmak_izi=(
                "MASAUSTU-PARMAK-IZI"
            ),
        )
    )

    yonetici = TerminalOturumYoneticisi(
        terminal,
        saat=saat.oku,
        canlilik_zaman_asimi_saniye=30,
        oturum_suresi_dakika=60,
        mesaj_gecerlilik_saniye=60,
    )

    return saat, terminal, yonetici


def tablet_oturumu_ac(
    yonetici: TerminalOturumYoneticisi,
):
    return yonetici.oturum_ac(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
        oturum_kimligi="OTURUM-TABLET",
        oturum_anahtari=(
            "TABLET-GIZLI-ANAHTAR"
        ),
    )


def test_yetkili_cihaz_oturum_acar() -> None:
    _, terminal, yonetici = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        yonetici
    )

    assert oturum.durum is (
        OturumDurumu.BAGLI
    )
    assert oturum.oturum_kimligi == (
        "OTURUM-TABLET"
    )
    assert terminal.cihaz_getir(
        "SAMSUNG-TABLET"
    ).bagli_mi


def test_yanlis_parmak_izi_oturumu_reddeder() -> None:
    _, _, yonetici = sistem_olustur()

    with pytest.raises(
        OturumHatasi,
        match="doğrulanamadı",
    ):
        yonetici.oturum_ac(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi="YANLIS",
        )


def test_ayni_cihazin_iki_etkin_oturumu_olamaz() -> None:
    _, _, yonetici = sistem_olustur()

    tablet_oturumu_ac(yonetici)

    with pytest.raises(
        OturumHatasi,
        match="zaten etkin",
    ):
        yonetici.oturum_ac(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi=(
                "TABLET-PARMAK-IZI"
            ),
        )


def test_canlilik_bildirimi_oturumu_gunceller() -> None:
    saat, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    ilk_zaman = (
        oturum.son_canlilik_zamani
    )

    saat.ilerlet(saniye=10)

    yonetici.canlilik_bildir(
        oturum.oturum_kimligi
    )

    assert (
        oturum.son_canlilik_zamani
        > ilk_zaman
    )


def test_canlilik_zaman_asimi_cevrimdisi_yapar() -> None:
    saat, terminal, yonetici = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        yonetici
    )

    saat.ilerlet(saniye=31)

    degisenler = (
        yonetici.zaman_asimlarini_kontrol_et()
    )

    assert oturum in degisenler
    assert oturum.durum is (
        OturumDurumu.CEVRIMDISI
    )
    assert not terminal.cihaz_getir(
        "SAMSUNG-TABLET"
    ).bagli_mi


def test_cevrimdisi_oturum_yeniden_baglanir() -> None:
    saat, terminal, yonetici = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        yonetici
    )

    saat.ilerlet(saniye=31)
    yonetici.zaman_asimlarini_kontrol_et()

    saat.ilerlet(saniye=5)
    yonetici.canlilik_bildir(
        oturum.oturum_kimligi
    )

    assert oturum.durum is (
        OturumDurumu.BAGLI
    )
    assert (
        oturum.yeniden_baglanma_sayisi
        == 1
    )
    assert terminal.cihaz_getir(
        "SAMSUNG-TABLET"
    ).bagli_mi


def test_oturum_suresi_dolunca_sonlanir() -> None:
    saat, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    saat.ilerlet(dakika=61)

    yonetici.zaman_asimlarini_kontrol_et()

    assert oturum.durum is (
        OturumDurumu.SONA_ERDI
    )


def test_mesaj_imzalanir_ve_gonderilir() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.DURUM,
        icerik={
            "istek": "çalışma_durumu",
        },
    )

    assert mesaj.imza
    assert mesaj.durum is (
        MesajDurumu.IMZALANDI
    )
    assert mesaj.sira_numarasi == 1

    yonetici.mesaji_gonder(
        mesaj.mesaj_kimligi
    )

    assert mesaj.durum is (
        MesajDurumu.GONDERILDI
    )
    assert (
        oturum.gonderilen_mesaj_sayisi
        == 1
    )


def test_mesaj_imzasi_dogrulanir() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.VERI,
        icerik={
            "ölçüm": 42,
        },
    )

    sonuc = yonetici.mesaji_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.ISLENDI
    )
    assert oturum.alinan_mesaj_sayisi == 1


def test_degistirilmis_mesaj_reddedilir() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.VERI,
        icerik={
            "ölçüm": 42,
        },
    )

    mesaj.icerik["ölçüm"] = 99

    sonuc = yonetici.mesaji_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.REDDEDILDI
    )
    assert "imzası" in str(
        sonuc.hata
    )


def test_ayni_mesaj_iki_kez_islenmez() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.DURUM,
    )

    yonetici.mesaji_al(mesaj)
    ikinci = yonetici.mesaji_al(mesaj)

    assert ikinci.durum is (
        MesajDurumu.REDDEDILDI
    )
    assert "yeniden" in str(
        ikinci.hata
    )


def test_suresi_gecmis_mesaj_reddedilir() -> None:
    saat, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.DURUM,
    )

    saat.ilerlet(saniye=61)

    sonuc = yonetici.mesaji_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.REDDEDILDI
    )
    assert "geçerlilik" in str(
        sonuc.hata
    )


def test_mesaj_isleyici_sonucu_kaydeder() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    yonetici.mesaj_isleyici_kaydet(
        MesajTuru.DURUM,
        lambda mesaj: {
            "çalışma_sistemi": "hazır",
        },
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.DURUM,
    )

    sonuc = yonetici.mesaji_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.ISLENDI
    )
    assert (
        sonuc.icerik[
            "işleme_sonucu"
        ]["çalışma_sistemi"]
        == "hazır"
    )


def test_mesaj_isleyici_hatasi_kaydedilir() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    def hata_uret(mesaj):
        raise RuntimeError(
            "Mesaj işlenemedi."
        )

    yonetici.mesaj_isleyici_kaydet(
        MesajTuru.KOMUT,
        hata_uret,
    )

    mesaj = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.KOMUT,
    )

    sonuc = yonetici.mesaji_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.HATA
    )
    assert sonuc.hata == (
        "Mesaj işlenemedi."
    )


def test_oturum_sonlandirilinca_mesaj_olusturulamaz() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    yonetici.oturumu_sonlandir(
        oturum.oturum_kimligi,
        gerekce="Kullanıcı çıkışı",
    )

    with pytest.raises(
        OturumHatasi,
        match="Sona ermiş",
    ):
        yonetici.mesaj_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            mesaj_turu=MesajTuru.DURUM,
        )


def test_mesaj_sira_numarasi_artarak_ilerler() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    birinci = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.DURUM,
    )

    ikinci = yonetici.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.BILDIRIM,
    )

    assert birinci.sira_numarasi == 1
    assert ikinci.sira_numarasi == 2


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    _, _, yonetici = sistem_olustur()

    tablet_oturumu_ac(
        yonetici
    )

    ozet = yonetici.durum_ozeti()

    assert ozet[
        "toplam_oturum_sayısı"
    ] == 1
    assert ozet[
        "bağlı_oturum_sayısı"
    ] == 1
    assert ozet[
        "toplam_mesaj_sayısı"
    ] == 0


def test_oturum_olaylari_yayinlanir() -> None:
    _, _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    yonetici.canlilik_bildir(
        oturum.oturum_kimligi
    )

    konular = [
        olay.topic
        for olay
        in yonetici.olay_hatti.history
    ]

    assert "terminal.oturum.acildi" in konular
    assert (
        "terminal.oturum.canlilik"
        in konular
    )

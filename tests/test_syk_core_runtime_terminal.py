from __future__ import annotations

from datetime import UTC, datetime

import pytest

from syk_core.runtime_terminal import (
    BildirimTuru,
    CalismaTerminali,
    CihazDurumu,
    CihazTuru,
    KomutDurumu,
    KomutTuru,
    TerminalHatasi,
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


def terminal_olustur() -> CalismaTerminali:
    saat = ElleSaat(
        datetime(
            2026,
            8,
            4,
            20,
            0,
            tzinfo=UTC,
        )
    )

    return CalismaTerminali(
        saat=saat.oku
    )


def samsung_tablet() -> YetkiliCihazTanimi:
    return YetkiliCihazTanimi(
        cihaz_kimligi="SAMSUNG-TABLET",
        ad="Samsung Ana Saha Terminali",
        cihaz_turu=CihazTuru.TABLET,
        yetki_seviyesi=(
            YetkiSeviyesi.BILGE_KAAN
        ),
        cihaz_parmak_izi="TABLET-PARMAK-IZI",
    )


def iphone() -> YetkiliCihazTanimi:
    return YetkiliCihazTanimi(
        cihaz_kimligi="IPHONE-8-PLUS",
        ad="iPhone Yetkili Yardımcı Terminal",
        cihaz_turu=CihazTuru.TELEFON,
        yetki_seviyesi=(
            YetkiSeviyesi.OPERATOR
        ),
        cihaz_parmak_izi="IPHONE-PARMAK-IZI",
    )


def masaustu() -> YetkiliCihazTanimi:
    return YetkiliCihazTanimi(
        cihaz_kimligi="ANA-MASAUSTU",
        ad="SyKaşif Ana Makine",
        cihaz_turu=CihazTuru.MASAUSTU,
        yetki_seviyesi=(
            YetkiSeviyesi.KURUCU_KAAN
        ),
        cihaz_parmak_izi="MASAUSTU-PARMAK-IZI",
    )


def test_cihaz_kayit_ve_baglanti() -> None:
    terminal = terminal_olustur()

    cihaz = terminal.cihaz_kaydet(
        samsung_tablet()
    )

    assert cihaz.durum is CihazDurumu.KAYITLI

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    assert cihaz.durum is CihazDurumu.BAGLI
    assert cihaz.baglanti_sayisi == 1


def test_ayni_cihaz_iki_kez_kaydedilemez() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )

    with pytest.raises(
        TerminalHatasi,
        match="zaten kayıtlı",
    ):
        terminal.cihaz_kaydet(
            samsung_tablet()
        )


def test_yanlis_parmak_izi_reddedilir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )

    with pytest.raises(
        TerminalHatasi,
        match="doğrulanamadı",
    ):
        terminal.cihaz_bagla(
            "SAMSUNG-TABLET",
            cihaz_parmak_izi="YANLIS",
        )


def test_engelli_cihaz_baglanamaz() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        iphone()
    )

    terminal.cihaz_engelle(
        "IPHONE-8-PLUS",
        gerekce="Yetkisiz deneme",
    )

    with pytest.raises(
        TerminalHatasi,
        match="Engelli cihaz",
    ):
        terminal.cihaz_bagla(
            "IPHONE-8-PLUS",
            cihaz_parmak_izi=(
                "IPHONE-PARMAK-IZI"
            ),
        )


def test_normal_komut_kuyruga_alinir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )
    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    komut = terminal.komut_olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        komut_turu=KomutTuru.DURUM_ISTE,
    )

    assert komut.durum is KomutDurumu.KUYRUKTA
    assert terminal.kuyruktaki_komut_sayisi == 1


def test_kritik_komut_insan_onayi_ister() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    with pytest.raises(
        TerminalHatasi,
        match="insan onayı",
    ):
        terminal.komut_olustur(
            kaynak_cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            komut_turu=(
                KomutTuru.MASAUSTUNU_KAPAT
            ),
        )


def test_operator_masaustunu_kapatamaz() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        iphone()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "IPHONE-8-PLUS",
        cihaz_parmak_izi=(
            "IPHONE-PARMAK-IZI"
        ),
    )

    with pytest.raises(
        TerminalHatasi,
        match="Bilge Kaan",
    ):
        terminal.komut_olustur(
            kaynak_cihaz_kimligi=(
                "IPHONE-8-PLUS"
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            komut_turu=(
                KomutTuru.MASAUSTUNU_KAPAT
            ),
            onaylayan="Bilge Kaan",
        )


def test_komut_basariyla_calistirilir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )
    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    terminal.isleyici_kaydet(
        KomutTuru.UYGULAMA_AC,
        lambda komut: {
            "uygulama": "SyKaşif",
            "durum": "açıldı",
        },
    )

    komut = terminal.komut_olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        komut_turu=KomutTuru.UYGULAMA_AC,
    )

    sonuc = (
        terminal.siradaki_komutu_calistir()
    )

    assert sonuc is komut
    assert sonuc.durum is (
        KomutDurumu.TAMAMLANDI
    )
    assert sonuc.sonuc["durum"] == "açıldı"


def test_cevrimdisi_hedef_komutu_reddeder() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    terminal.isleyici_kaydet(
        KomutTuru.DURUM_ISTE,
        lambda komut: {"durum": "hazır"},
    )

    komut = terminal.komut_olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        komut_turu=KomutTuru.DURUM_ISTE,
    )

    terminal.siradaki_komutu_calistir()

    assert komut.durum is (
        KomutDurumu.REDDEDILDI
    )
    assert "bağlı değil" in str(
        komut.hata
    )


def test_isleyici_hatasi_kaydedilir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )
    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    def hata_uret(komut):
        raise RuntimeError(
            "Uygulama açılamadı."
        )

    terminal.isleyici_kaydet(
        KomutTuru.UYGULAMA_AC,
        hata_uret,
    )

    komut = terminal.komut_olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        komut_turu=KomutTuru.UYGULAMA_AC,
    )

    terminal.siradaki_komutu_calistir()

    assert komut.durum is KomutDurumu.HATA
    assert komut.hata == (
        "Uygulama açılamadı."
    )


def test_bildirim_olusturulur() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        iphone()
    )

    bildirim = terminal.bildirim_olustur(
        bildirim_turu=(
            BildirimTuru.YENI_KANIT
        ),
        baslik="Yeni kanıt",
        aciklama=(
            "Yeni yüzey kanıtı incelemeye hazır."
        ),
        hedef_cihaz_kimligi=(
            "IPHONE-8-PLUS"
        ),
    )

    assert bildirim.baslik == "Yeni kanıt"
    assert len(terminal.bildirimler) == 1


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    ozet = terminal.durum_ozeti()

    assert ozet["toplam_cihaz_sayısı"] == 1
    assert ozet["bağlı_cihaz_sayısı"] == 1
    assert ozet["kuyruktaki_komut_sayısı"] == 0
    assert ozet["cihazlar"][0]["ad"] == (
        "Samsung Ana Saha Terminali"
    )


def test_terminal_olaylari_yayinlanir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    terminal.bildirim_olustur(
        bildirim_turu=BildirimTuru.BILGI,
        baslik="Sistem",
        aciklama="Terminal hazır.",
    )

    konular = [
        olay.topic
        for olay in terminal.olay_hatti.history
    ]

    assert "terminal.cihaz.kaydedildi" in konular
    assert "terminal.cihaz.baglandi" in konular
    assert (
        "terminal.bildirim.olusturuldu"
        in konular
    )


def test_kuyruk_sinirli_calistirilir() -> None:
    terminal = terminal_olustur()

    terminal.cihaz_kaydet(
        samsung_tablet()
    )
    terminal.cihaz_kaydet(
        masaustu()
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )
    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    terminal.isleyici_kaydet(
        KomutTuru.DURUM_ISTE,
        lambda komut: {"durum": "hazır"},
    )

    for _ in range(3):
        terminal.komut_olustur(
            kaynak_cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            komut_turu=(
                KomutTuru.DURUM_ISTE
            ),
        )

    sonuclar = terminal.kuyrugu_calistir(
        sinir=2
    )

    assert len(sonuclar) == 2
    assert terminal.kuyruktaki_komut_sayisi == 1

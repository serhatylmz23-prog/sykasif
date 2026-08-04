from __future__ import annotations

from datetime import UTC, datetime

import pytest

from syk_core.runtime_terminal import (
    AracDurumu,
    CalismaTerminali,
    CihazAraciHatasi,
    CihazTuru,
    IslemDurumu,
    IslemTuru,
    KomutDurumu,
    KomutTuru,
    UygulamaTanimi,
    YetkiliCihazAraci,
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


class SahteUygulamaSistemi:
    def __init__(self) -> None:
        self.son_islem_kimligi = 1000
        self.calisanlar: set[str] = set()

    def baslat(
        self,
        tanim: UygulamaTanimi,
    ) -> int:
        self.son_islem_kimligi += 1
        self.calisanlar.add(
            tanim.uygulama_kimligi
        )
        return self.son_islem_kimligi

    def kapat(
        self,
        tanim: UygulamaTanimi,
        durum,
    ) -> bool:
        self.calisanlar.discard(
            tanim.uygulama_kimligi
        )
        return True


class SahteSistemIsleyicisi:
    def __init__(self) -> None:
        self.islemler: list[
            tuple[IslemTuru, dict]
        ] = []

    def calistir(
        self,
        islem_turu: IslemTuru,
        icerik: dict,
    ) -> dict:
        self.islemler.append(
            (
                islem_turu,
                dict(icerik),
            )
        )

        return {
            "durum": "kabul_edildi",
            "işlem_türü": islem_turu.value,
        }


def sistem_olustur():
    saat = ElleSaat(
        datetime(
            2026,
            8,
            4,
            22,
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

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    terminal.cihaz_bagla(
        "IPHONE-8-PLUS",
        cihaz_parmak_izi=(
            "IPHONE-PARMAK-IZI"
        ),
    )

    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    uygulamalar = SahteUygulamaSistemi()
    sistem_isleyicisi = SahteSistemIsleyicisi()

    arac = YetkiliCihazAraci(
        terminal,
        cihaz_kimligi="ANA-MASAUSTU",
        saat=saat.oku,
        uygulama_baslatici=(
            uygulamalar.baslat
        ),
        uygulama_kapatici=(
            uygulamalar.kapat
        ),
        sistem_isleyicisi=(
            sistem_isleyicisi.calistir
        ),
    )

    arac.uygulama_kaydet(
        UygulamaTanimi(
            uygulama_kimligi="SYKASIF",
            gorunen_ad="SyKaşif",
            calistirma_yolu=(
                r"D:\sykasif_repo\sykasif"
            ),
        )
    )

    return (
        saat,
        terminal,
        arac,
        uygulamalar,
        sistem_isleyicisi,
    )


def test_arac_hazir_durumda_baslar() -> None:
    _, _, arac, _, _ = sistem_olustur()

    assert arac.durum is AracDurumu.HAZIR
    assert arac.cihaz_kimligi == (
        "ANA-MASAUSTU"
    )


def test_operator_cihazinda_arac_baslatilamaz() -> None:
    saat, terminal, _, _, _ = (
        sistem_olustur()
    )

    with pytest.raises(
        CihazAraciHatasi,
        match="Bilge Kaan",
    ):
        YetkiliCihazAraci(
            terminal,
            cihaz_kimligi="IPHONE-8-PLUS",
            saat=saat.oku,
        )


def test_uygulama_kayit_altina_alinir() -> None:
    _, _, arac, _, _ = sistem_olustur()

    tanim = arac.uygulama_getir(
        "SYKASIF"
    )

    assert tanim.gorunen_ad == "SyKaşif"
    assert len(
        arac.uygulamalari_listele()
    ) == 1


def test_ayni_uygulama_iki_kez_kaydedilemez() -> None:
    _, _, arac, _, _ = sistem_olustur()

    with pytest.raises(
        CihazAraciHatasi,
        match="zaten kayıtlı",
    ):
        arac.uygulama_kaydet(
            UygulamaTanimi(
                uygulama_kimligi="SYKASIF",
                gorunen_ad="SyKaşif",
                calistirma_yolu="D:\\sykasif",
            )
        )


def test_uygulama_baslatilir() -> None:
    _, _, arac, uygulamalar, _ = (
        sistem_olustur()
    )

    islem = arac.uygulamayi_ac(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
        gerekce="Saha oturumu",
    )

    assert islem.durum is (
        IslemDurumu.TAMAMLANDI
    )

    durum = arac.uygulama_durumu_getir(
        "SYKASIF"
    )

    assert durum.calisiyor_mu
    assert durum.islem_kimligi == 1001
    assert "SYKASIF" in uygulamalar.calisanlar


def test_calisan_uygulama_tekrar_baslatilmaz() -> None:
    _, _, arac, _, _ = sistem_olustur()

    arac.uygulamayi_ac(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
    )

    ikinci = arac.uygulamayi_ac(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
    )

    assert ikinci.durum is (
        IslemDurumu.REDDEDILDI
    )
    assert "zaten çalışıyor" in str(
        ikinci.hata
    )


def test_uygulama_guvenli_kapatilir() -> None:
    _, _, arac, uygulamalar, _ = (
        sistem_olustur()
    )

    arac.uygulamayi_ac(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
    )

    islem = arac.uygulamayi_kapat(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
        gerekce="Saha oturumu tamamlandı",
    )

    assert islem.durum is (
        IslemDurumu.TAMAMLANDI
    )

    durum = arac.uygulama_durumu_getir(
        "SYKASIF"
    )

    assert not durum.calisiyor_mu
    assert "SYKASIF" not in (
        uygulamalar.calisanlar
    )


def test_kritik_islem_insan_onayi_ister() -> None:
    _, _, arac, _, _ = sistem_olustur()

    islem = arac.sistem_islemi_calistir(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        islem_turu=(
            IslemTuru.MASAUSTUNU_KAPAT
        ),
        insan_onayi=None,
        gerekce="Saha çıkışı",
    )

    assert islem.durum is (
        IslemDurumu.REDDEDILDI
    )
    assert "insan onayı" in str(
        islem.hata
    )


def test_operator_kritik_islem_yapamaz() -> None:
    _, _, arac, _, _ = sistem_olustur()

    islem = arac.sistem_islemi_calistir(
        kaynak_cihaz_kimligi=(
            "IPHONE-8-PLUS"
        ),
        islem_turu=(
            IslemTuru.MASAUSTUNU_KAPAT
        ),
        insan_onayi="Bilge Kaan",
        gerekce="Saha çıkışı",
    )

    assert islem.durum is (
        IslemDurumu.REDDEDILDI
    )
    assert "Bilge Kaan" in str(
        islem.hata
    )


def test_yetkili_kritik_islem_calistirir() -> None:
    _, _, arac, _, sistem = (
        sistem_olustur()
    )

    islem = arac.sistem_islemi_calistir(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        islem_turu=(
            IslemTuru.MASAUSTUNU_KAPAT
        ),
        insan_onayi="Bilge Kaan",
        gerekce="Saha çıkışı tamamlandı",
    )

    assert islem.durum is (
        IslemDurumu.TAMAMLANDI
    )
    assert sistem.islemler[-1][0] is (
        IslemTuru.MASAUSTUNU_KAPAT
    )


def test_terminal_uygulama_acma_komutu_araca_ulasir() -> None:
    _, terminal, arac, _, _ = (
        sistem_olustur()
    )

    komut = terminal.komut_olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        komut_turu=KomutTuru.UYGULAMA_AC,
        icerik={
            "uygulama_kimliği": "SYKASIF",
        },
        gerekce="Saha çalışması",
    )

    terminal.siradaki_komutu_calistir()

    assert komut.durum is (
        KomutDurumu.TAMAMLANDI
    )
    assert komut.sonuc[
        "durum"
    ] == "tamamlandı"

    assert arac.uygulama_durumu_getir(
        "SYKASIF"
    ).calisiyor_mu


def test_terminal_durum_komutu_arac_ozeti_dondurur() -> None:
    _, terminal, _, _, _ = (
        sistem_olustur()
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
        KomutDurumu.TAMAMLANDI
    )

    sonuc = komut.sonuc[
        "sonuç"
    ]

    assert sonuc[
        "cihaz_kimliği"
    ] == "ANA-MASAUSTU"
    assert sonuc[
        "araç_durumu"
    ] == "hazır"


def test_terminal_kapatma_komutu_insan_onayi_ile_calistirilir() -> None:
    _, terminal, _, _, sistem = (
        sistem_olustur()
    )

    komut = terminal.komut_olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        komut_turu=(
            KomutTuru.MASAUSTUNU_KAPAT
        ),
        gerekce="Saha çıkışı tamamlandı",
        onaylayan="Bilge Kaan",
    )

    terminal.siradaki_komutu_calistir()

    assert komut.durum is (
        KomutDurumu.TAMAMLANDI
    )

    assert sistem.islemler[-1][0] is (
        IslemTuru.MASAUSTUNU_KAPAT
    )


def test_arac_guvenli_durdurulur() -> None:
    _, _, arac, _, _ = sistem_olustur()

    arac.uygulamayi_ac(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
    )

    arac.guvenli_durdur()

    assert arac.durum is (
        AracDurumu.DURDURULDU
    )

    assert not arac.uygulama_durumu_getir(
        "SYKASIF"
    ).calisiyor_mu


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    _, _, arac, _, _ = sistem_olustur()

    ozet = arac.durum_ozeti()

    assert ozet[
        "cihaz_kimliği"
    ] == "ANA-MASAUSTU"
    assert ozet[
        "kayıtlı_uygulama_sayısı"
    ] == 1
    assert ozet[
        "çalışan_uygulama_sayısı"
    ] == 0


def test_arac_olaylari_yayinlanir() -> None:
    _, _, arac, _, _ = sistem_olustur()

    arac.uygulamayi_ac(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        uygulama_kimligi="SYKASIF",
    )

    konular = [
        olay.topic
        for olay in arac.olay_hatti.history
    ]

    assert "terminal.arac.hazir" in konular
    assert (
        "terminal.arac.uygulama_kaydedildi"
        in konular
    )
    assert (
        "terminal.arac.islem_tamamlandi"
        in konular
    )

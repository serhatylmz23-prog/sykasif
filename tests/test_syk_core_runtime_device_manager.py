from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_device_link import (
    CihazYonetimHatasi,
    CihazYetkisi,
    GuvenlikHatasi,
    IslemYetkisi,
    KomutDurumu,
    OturumDurumu,
    YetkiliCihazKaydi,
    YetkiliCihazYoneticisi,
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
    ) -> None:
        self.simdi += timedelta(
            seconds=saniye
        )


def sistem_olustur():
    saat = ElleSaat(
        datetime(
            2026,
            8,
            5,
            2,
            0,
            tzinfo=UTC,
        )
    )

    yonetici = YetkiliCihazYoneticisi(
        saat=saat.oku
    )

    yonetici.cihaz_kaydet(
        YetkiliCihazKaydi(
            cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            cihaz_parmak_izi=(
                "MASAUSTU-IZI"
            ),
            yetki=(
                CihazYetkisi.KURUCU_KAAN
            ),
            gizli_anahtar=(
                "MASAUSTU-ANAHTARI"
            ),
        )
    )

    yonetici.cihaz_kaydet(
        YetkiliCihazKaydi(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi=(
                "TABLET-IZI"
            ),
            yetki=(
                CihazYetkisi.BILGE_KAAN
            ),
            gizli_anahtar=(
                "TABLET-ANAHTARI"
            ),
        )
    )

    yonetici.cihaz_kaydet(
        YetkiliCihazKaydi(
            cihaz_kimligi=(
                "IPHONE-8-PLUS"
            ),
            cihaz_parmak_izi=(
                "IPHONE-IZI"
            ),
            yetki=(
                CihazYetkisi.ISLETMEN
            ),
            gizli_anahtar=(
                "IPHONE-ANAHTARI"
            ),
        )
    )

    return saat, yonetici


def tablet_oturumu_ac(
    yonetici: YetkiliCihazYoneticisi,
):
    return yonetici.oturum_ac(
        cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        cihaz_parmak_izi=(
            "TABLET-IZI"
        ),
        gizli_anahtar=(
            "TABLET-ANAHTARI"
        ),
    )


def telefon_oturumu_ac(
    yonetici: YetkiliCihazYoneticisi,
):
    return yonetici.oturum_ac(
        cihaz_kimligi=(
            "IPHONE-8-PLUS"
        ),
        cihaz_parmak_izi=(
            "IPHONE-IZI"
        ),
        gizli_anahtar=(
            "IPHONE-ANAHTARI"
        ),
    )


def test_uc_yetkili_cihaz_kaydedilir() -> None:
    _, yonetici = sistem_olustur()

    assert len(
        yonetici.cihazlari_listele()
    ) == 3


def test_ayni_cihaz_tekrar_kaydedilemez() -> None:
    _, yonetici = sistem_olustur()

    with pytest.raises(
        CihazYonetimHatasi,
        match="zaten kayıtlı",
    ):
        yonetici.cihaz_kaydet(
            YetkiliCihazKaydi(
                cihaz_kimligi=(
                    "SAMSUNG-TABLET"
                ),
                cihaz_parmak_izi="IZ",
                yetki=(
                    CihazYetkisi.BILGE_KAAN
                ),
                gizli_anahtar="ANAHTAR",
            )
        )


def test_tablet_oturum_acar() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    assert oturum.bagli_mi


def test_tablet_uygulama_acma_komutu_olusturur() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.UYGULAMA_AC
        ),
        icerik={
            "uygulama": "SyKaşif",
        },
    )

    assert (
        komut.durum
        is KomutDurumu.KUYRUKTA
    )

    assert komut.mesaj_kimligi


def test_komut_isleyiciyle_tamamlanir() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    yonetici.isleyici_kaydet(
        IslemYetkisi.UYGULAMA_AC,
        lambda komut: {
            "uygulama": (
                komut.icerik["uygulama"]
            ),
            "durum": "açıldı",
        },
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.UYGULAMA_AC
        ),
        icerik={
            "uygulama": "SyKaşif",
        },
    )

    sonuc = (
        yonetici
        .siradaki_komutu_calistir()
    )

    assert sonuc is komut

    assert (
        komut.durum
        is KomutDurumu.TAMAMLANDI
    )

    assert komut.sonuc[
        "durum"
    ] == "açıldı"


def test_isleyicisiz_komut_hata_olur() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.UYGULAMA_AC
        ),
    )

    yonetici.siradaki_komutu_calistir()

    assert (
        komut.durum
        is KomutDurumu.HATA
    )

    assert "işleyicisi" in str(
        komut.hata
    )


def test_isleyici_hatasi_kaydedilir() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    def hatali_isleyici(
        komut,
    ):
        raise RuntimeError(
            "Deneme işlem hatası"
        )

    yonetici.isleyici_kaydet(
        IslemYetkisi.UYGULAMA_AC,
        hatali_isleyici,
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.UYGULAMA_AC
        ),
    )

    yonetici.siradaki_komutu_calistir()

    assert (
        komut.durum
        is KomutDurumu.HATA
    )

    assert "Deneme işlem hatası" in str(
        komut.hata
    )


def test_telefon_uygulama_acamaz() -> None:
    _, yonetici = sistem_olustur()

    oturum = telefon_oturumu_ac(
        yonetici
    )

    with pytest.raises(
        GuvenlikHatasi,
        match="yetkisi yok",
    ):
        yonetici.komut_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            islem_yetkisi=(
                IslemYetkisi.UYGULAMA_AC
            ),
        )


def test_telefon_durum_okuyabilir() -> None:
    _, yonetici = sistem_olustur()

    oturum = telefon_oturumu_ac(
        yonetici
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.DURUM_OKU
        ),
    )

    assert (
        komut.durum
        is KomutDurumu.KUYRUKTA
    )


def test_kritik_islem_gerekce_ister() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    with pytest.raises(
        CihazYonetimHatasi,
        match="gerekçe",
    ):
        yonetici.komut_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            islem_yetkisi=(
                IslemYetkisi.SISTEMI_DURDUR
            ),
            insan_onayi="Bilge Kaan",
        )


def test_kritik_islem_insan_onayi_ister() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    with pytest.raises(
        CihazYonetimHatasi,
        match="insan onayı",
    ):
        yonetici.komut_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            islem_yetkisi=(
                IslemYetkisi.SISTEMI_DURDUR
            ),
            gerekce="Saha çıkışı",
        )


def test_bilge_kaan_kritik_islem_olusturur() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.SISTEMI_DURDUR
        ),
        gerekce="Saha çalışması tamamlandı",
        insan_onayi="Bilge Kaan",
    )

    assert (
        komut.durum
        is KomutDurumu.KUYRUKTA
    )


def test_tum_bekleyen_komutlar_calistirilir() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    yonetici.isleyici_kaydet(
        IslemYetkisi.DURUM_OKU,
        lambda komut: {
            "durum": "hazır",
        },
    )

    for _ in range(3):
        yonetici.komut_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            islem_yetkisi=(
                IslemYetkisi.DURUM_OKU
            ),
        )

    sonuclar = (
        yonetici
        .tum_bekleyenleri_calistir()
    )

    assert len(sonuclar) == 3

    assert all(
        komut.durum
        is KomutDurumu.TAMAMLANDI
        for komut in sonuclar
    )


def test_cevrimdisi_oturum_komut_gonderemez() -> None:
    saat, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    saat.ilerlet(
        saniye=31
    )

    yonetici.zaman_asimlarini_kontrol_et()

    assert (
        oturum.durum
        is OturumDurumu.CEVRIMDISI
    )

    with pytest.raises(
        CihazYonetimHatasi,
        match="bağlı olmalıdır",
    ):
        yonetici.komut_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            islem_yetkisi=(
                IslemYetkisi.DURUM_OKU
            ),
        )


def test_yeniden_baglanan_oturum_komut_gonderir() -> None:
    saat, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    saat.ilerlet(
        saniye=31
    )

    yonetici.zaman_asimlarini_kontrol_et()

    yonetici.canlilik_bildir(
        oturum.oturum_kimligi
    )

    komut = yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.DURUM_OKU
        ),
    )

    assert (
        komut.durum
        is KomutDurumu.KUYRUKTA
    )


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    _, yonetici = sistem_olustur()

    oturum = tablet_oturumu_ac(
        yonetici
    )

    yonetici.komut_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        islem_yetkisi=(
            IslemYetkisi.DURUM_OKU
        ),
    )

    ozet = yonetici.durum_ozeti()

    assert ozet[
        "kayıtlı_cihaz_sayısı"
    ] == 3

    assert ozet[
        "toplam_komut_sayısı"
    ] == 1

    assert ozet[
        "kuyruktaki_komut_sayısı"
    ] == 1

    assert "bağlantı" in ozet
    assert "güvenlik" in ozet
    assert "komutlar" in ozet

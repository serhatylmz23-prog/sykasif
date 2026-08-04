from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from syk_core.runtime_device_link import (
    CihazBaglantiYoneticisi,
    CihazGuvenlikYoneticisi,
    CihazMesaji,
    CihazOturumuHatasi,
    CihazYetkisi,
    GuvenlikHatasi,
    IslemYetkisi,
    MesajDurumu,
    MesajTuru,
    OturumDurumu,
    ProtokolHatasi,
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
            5,
            1,
            0,
            tzinfo=UTC,
        )
    )

    guvenlik = (
        CihazGuvenlikYoneticisi(
            saat=saat.oku
        )
    )

    tablet, tablet_anahtari = (
        guvenlik.cihaz_kaydet(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi=(
                "TABLET-PARMAK-IZI"
            ),
            yetki=(
                CihazYetkisi.BILGE_KAAN
            ),
            gizli_anahtar=(
                "TABLET-GIZLI-ANAHTAR"
            ),
        )
    )

    telefon, telefon_anahtari = (
        guvenlik.cihaz_kaydet(
            cihaz_kimligi=(
                "IPHONE-8-PLUS"
            ),
            cihaz_parmak_izi=(
                "IPHONE-PARMAK-IZI"
            ),
            yetki=(
                CihazYetkisi.ISLETMEN
            ),
            gizli_anahtar=(
                "IPHONE-GIZLI-ANAHTAR"
            ),
        )
    )

    masaustu, masaustu_anahtari = (
        guvenlik.cihaz_kaydet(
            cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            cihaz_parmak_izi=(
                "MASAUSTU-PARMAK-IZI"
            ),
            yetki=(
                CihazYetkisi.KURUCU_KAAN
            ),
            gizli_anahtar=(
                "MASAUSTU-GIZLI-ANAHTAR"
            ),
        )
    )

    baglanti = (
        CihazBaglantiYoneticisi(
            guvenlik,
            saat=saat.oku,
            canlilik_zaman_asimi_saniye=30,
            oturum_suresi_dakika=60,
        )
    )

    return (
        saat,
        guvenlik,
        baglanti,
        {
            "tablet": (
                tablet,
                tablet_anahtari,
            ),
            "telefon": (
                telefon,
                telefon_anahtari,
            ),
            "masaüstü": (
                masaustu,
                masaustu_anahtari,
            ),
        },
    )


def tablet_oturumu_ac(
    baglanti: CihazBaglantiYoneticisi,
):
    return baglanti.oturum_ac(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
        gizli_anahtar=(
            "TABLET-GIZLI-ANAHTAR"
        ),
    )


def test_uc_yetkili_cihaz_kaydedilir() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    ozet = guvenlik.durum_ozeti()

    assert ozet[
        "kayıtlı_cihaz_sayısı"
    ] == 3

    assert ozet[
        "etkin_cihaz_sayısı"
    ] == 3


def test_yanlis_parmak_izi_reddedilir() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    with pytest.raises(
        GuvenlikHatasi,
        match="parmak izi",
    ):
        guvenlik.cihaz_dogrula(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi="YANLIS",
            gizli_anahtar=(
                "TABLET-GIZLI-ANAHTAR"
            ),
        )


def test_yanlis_gizli_anahtar_reddedilir() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    with pytest.raises(
        GuvenlikHatasi,
        match="gizli anahtarı",
    ):
        guvenlik.cihaz_dogrula(
            cihaz_kimligi=(
                "SAMSUNG-TABLET"
            ),
            cihaz_parmak_izi=(
                "TABLET-PARMAK-IZI"
            ),
            gizli_anahtar="YANLIS",
        )


def test_bilge_kaan_uygulama_acabilir() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    guvenlik.yetki_dogrula(
        cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        islem_yetkisi=(
            IslemYetkisi.UYGULAMA_AC
        ),
    )


def test_isletmen_masaustunu_kapatamaz() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    with pytest.raises(
        GuvenlikHatasi,
        match="yetkisi yok",
    ):
        guvenlik.yetki_dogrula(
            cihaz_kimligi=(
                "IPHONE-8-PLUS"
            ),
            islem_yetkisi=(
                IslemYetkisi.MASAUSTUNU_KAPAT
            ),
        )


def test_kurucu_kaan_tum_yetkilere_sahiptir() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    for izin in IslemYetkisi:
        guvenlik.yetki_dogrula(
            cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            islem_yetkisi=izin,
        )


def test_tablet_oturumu_acilir() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    assert oturum.bagli_mi

    assert oturum.durum is (
        OturumDurumu.BAGLI
    )


def test_ayni_cihaz_iki_oturum_acamaz() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    tablet_oturumu_ac(
        baglanti
    )

    with pytest.raises(
        CihazOturumuHatasi,
        match="zaten etkin",
    ):
        tablet_oturumu_ac(
            baglanti
        )


def test_mesaj_imzalanir() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    mesaj = baglanti.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=(
            MesajTuru.DURUM_ISTEGI
        ),
        icerik={
            "istek": "sistem_durumu",
        },
    )

    assert mesaj.imza

    assert mesaj.durum is (
        MesajDurumu.IMZALANDI
    )

    assert mesaj.sira_numarasi == 1


def test_ardisik_mesajlarda_sira_numarasi_artir() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    birinci = baglanti.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=(
            MesajTuru.DURUM_ISTEGI
        ),
    )

    ikinci = baglanti.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=(
            MesajTuru.CANLILIK
        ),
    )

    assert birinci.sira_numarasi == 1
    assert ikinci.sira_numarasi == 2


def test_imzali_mesaj_dogrulanir() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    mesaj = baglanti.mesaj_olustur(
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

    sonuc = baglanti.mesaj_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.ALINDI
    )

    assert oturum.alinan_mesaj_sayisi == 1


def test_degistirilmis_mesaj_reddedilir() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    mesaj = baglanti.mesaj_olustur(
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

    mesaj.icerik[
        "ölçüm"
    ] = 999

    sonuc = baglanti.mesaj_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.REDDEDILDI
    )

    assert "imzası" in str(
        sonuc.hata
    )


def test_ayni_mesaj_iki_kez_islenmez() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    mesaj = baglanti.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=(
            MesajTuru.CANLILIK
        ),
    )

    ilk = baglanti.mesaj_al(
        mesaj
    )

    assert ilk.durum is (
        MesajDurumu.ALINDI
    )

    ikinci = baglanti.mesaj_al(
        mesaj
    )

    assert ikinci.durum is (
        MesajDurumu.REDDEDILDI
    )

    assert "daha önce" in str(
        ikinci.hata
    )


def test_suresi_gecmis_mesaj_reddedilir() -> None:
    saat, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    mesaj = baglanti.mesaj_olustur(
        oturum_kimligi=(
            oturum.oturum_kimligi
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.VERI,
    )

    saat.ilerlet(
        saniye=61
    )

    sonuc = baglanti.mesaj_al(
        mesaj
    )

    assert sonuc.durum is (
        MesajDurumu.REDDEDILDI
    )

    assert "geçerlilik" in str(
        sonuc.hata
    )


def test_canlilik_zaman_asimi_cevrimdisi_yapar() -> None:
    saat, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    saat.ilerlet(
        saniye=31
    )

    degisenler = (
        baglanti
        .zaman_asimlarini_kontrol_et()
    )

    assert oturum in degisenler

    assert oturum.durum is (
        OturumDurumu.CEVRIMDISI
    )


def test_cevrimdisi_oturum_yeniden_baglanir() -> None:
    saat, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    saat.ilerlet(
        saniye=31
    )

    baglanti.zaman_asimlarini_kontrol_et()

    baglanti.canlilik_bildir(
        oturum.oturum_kimligi
    )

    assert oturum.bagli_mi

    assert (
        oturum.yeniden_baglanma_sayisi
        == 1
    )


def test_oturum_suresi_dolunca_sonlanir() -> None:
    saat, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    saat.ilerlet(
        dakika=61
    )

    baglanti.zaman_asimlarini_kontrol_et()

    assert oturum.sona_erdi_mi


def test_sona_eren_oturum_mesaj_gonderemez() -> None:
    _, _, baglanti, _ = (
        sistem_olustur()
    )

    oturum = tablet_oturumu_ac(
        baglanti
    )

    baglanti.oturumu_sonlandir(
        oturum.oturum_kimligi,
        gerekce="Kullanıcı çıkışı",
    )

    with pytest.raises(
        CihazOturumuHatasi,
        match="bağlı olmalıdır",
    ):
        baglanti.mesaj_olustur(
            oturum_kimligi=(
                oturum.oturum_kimligi
            ),
            hedef_cihaz_kimligi=(
                "ANA-MASAUSTU"
            ),
            mesaj_turu=(
                MesajTuru.DURUM_ISTEGI
            ),
        )


def test_mesaj_json_donusumu_kayipsizdir() -> None:
    zaman = datetime(
        2026,
        8,
        5,
        1,
        30,
        tzinfo=UTC,
    )

    mesaj = CihazMesaji.olustur(
        kaynak_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        hedef_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        mesaj_turu=MesajTuru.VERI,
        sira_numarasi=1,
        icerik={
            "ölçüm": 42,
            "birim": "santimetre",
        },
        oturum_kimligi="OTURUM-1",
        olusturulma_zamani=zaman,
    )

    mesaj.imzala(
        "GIZLI-ANAHTAR"
    )

    yeniden = CihazMesaji.json_coz(
        mesaj.json_olustur()
    )

    assert yeniden.mesaj_kimligi == (
        mesaj.mesaj_kimligi
    )

    assert yeniden.icerik == (
        mesaj.icerik
    )

    assert yeniden.imza == (
        mesaj.imza
    )


def test_gecersiz_json_reddedilir() -> None:
    with pytest.raises(
        ProtokolHatasi,
        match="geçerli JSON",
    ):
        CihazMesaji.json_coz(
            "{geçersiz"
        )


def test_guvenlik_denetim_kaydi_tutulur() -> None:
    _, guvenlik, _, _ = (
        sistem_olustur()
    )

    guvenlik.cihaz_dogrula(
        cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
        gizli_anahtar=(
            "TABLET-GIZLI-ANAHTAR"
        ),
    )

    kayitlar = (
        guvenlik.denetim_kayitlari()
    )

    assert any(
        kayit.olay
        == "cihaz_dogrulama"
        and kayit.basarili
        for kayit in kayitlar
    )


def test_durum_ozeti_turkce_anahtarlar_kullanir() -> None:
    _, guvenlik, baglanti, _ = (
        sistem_olustur()
    )

    tablet_oturumu_ac(
        baglanti
    )

    guvenlik_ozeti = (
        guvenlik.durum_ozeti()
    )

    baglanti_ozeti = (
        baglanti.durum_ozeti()
    )

    assert (
        guvenlik_ozeti[
            "kayıtlı_cihaz_sayısı"
        ]
        == 3
    )

    assert (
        baglanti_ozeti[
            "bağlı_oturum_sayısı"
        ]
        == 1
    )

    assert "oturumlar" in (
        baglanti_ozeti
    )

    assert "mesajlar" in (
        baglanti_ozeti
    )

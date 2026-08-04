from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from syk_core.runtime_terminal import (
    BildirimTuru,
    CalismaTerminali,
    CihazTuru,
    KomutTuru,
    PanelAyarlari,
    TerminalAgGecidi,
    TerminalOturumYoneticisi,
    TerminalPaneli,
    YetkiliCihazTanimi,
    YetkiSeviyesi,
    terminal_panelini_bagla,
)


class ElleSaat:
    def __init__(
        self,
        simdi: datetime,
    ) -> None:
        self.simdi = simdi

    def oku(self) -> datetime:
        return self.simdi


def sistem_olustur():
    saat = ElleSaat(
        datetime(
            2026,
            8,
            5,
            0,
            10,
            tzinfo=UTC,
        )
    )

    terminal = CalismaTerminali(
        saat=saat.oku
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

    terminal.cihaz_bagla(
        "ANA-MASAUSTU",
        cihaz_parmak_izi=(
            "MASAUSTU-PARMAK-IZI"
        ),
    )

    terminal.cihaz_bagla(
        "SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
    )

    oturum_yoneticisi = (
        TerminalOturumYoneticisi(
            terminal,
            saat=saat.oku,
        )
    )

    oturum = oturum_yoneticisi.oturum_ac(
        cihaz_kimligi="SAMSUNG-TABLET",
        cihaz_parmak_izi=(
            "TABLET-PARMAK-IZI"
        ),
        oturum_kimligi="OTURUM-TABLET",
        oturum_anahtari="GIZLI-ANAHTAR",
    )

    terminal.isleyici_kaydet(
        KomutTuru.DURUM_ISTE,
        lambda komut: {
            "durum": "hazır",
        },
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

    terminal.bildirim_olustur(
        bildirim_turu=(
            BildirimTuru.YENI_KANIT
        ),
        baslik="Yeni kanıt",
        aciklama=(
            "Yeni kanıt incelemeye hazır."
        ),
        hedef_cihaz_kimligi=(
            "SAMSUNG-TABLET"
        ),
    )

    ag_gecidi = TerminalAgGecidi(
        terminal,
        oturum_yoneticisi,
        saat=saat.oku,
    )

    panel = TerminalPaneli(
        terminal,
        oturum_yoneticisi,
        ag_gecidi=ag_gecidi,
        saat=saat.oku,
        ayarlar=PanelAyarlari(
            yenileme_suresi_saniye=7,
        ),
    )

    panel.uygulamaya_bagla(
        ag_gecidi.uygulama
    )

    istemci = TestClient(
        ag_gecidi.uygulama
    )

    return (
        saat,
        terminal,
        oturum_yoneticisi,
        ag_gecidi,
        panel,
        istemci,
        oturum,
        komut,
    )


def test_panel_anlik_gorunumu_olusturulur() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    gorunum = (
        panel.anlik_gorunum_olustur()
    )

    assert gorunum.toplam_cihaz_sayisi == 3
    assert gorunum.bagli_cihaz_sayisi == 2
    assert gorunum.etkin_oturum_sayisi == 1
    assert gorunum.tamamlanan_komut_sayisi == 1
    assert gorunum.bildirim_sayisi == 1


def test_panel_verisi_turkce_anahtarlar_kullanir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    veri = (
        panel.anlik_gorunum_olustur()
        .sozluk()
    )

    assert veri["toplam_cihaz_sayısı"] == 3
    assert veri["bağlı_cihaz_sayısı"] == 2
    assert veri["etkin_oturum_sayısı"] == 1
    assert veri["bildirim_sayısı"] == 1


def test_panel_html_turkce_baslik_tasir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    html = panel.html_olustur()

    assert "<title>SyKaşif Terminali</title>" in html
    assert "Yetkili cihazlar" in html
    assert "Çalışma oturumları" in html
    assert "Komut geçmişi" in html
    assert "Bildirimler" in html
    assert "Güvenlik durumu" in html


def test_panel_html_ingilizce_arayuz_basligi_tasimaz() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    html = panel.html_olustur()

    yasakli_ifadeler = {
        "Dashboard",
        "Devices",
        "Sessions",
        "Commands",
        "Notifications",
        "System Health",
    }

    assert not any(
        ifade in html
        for ifade in yasakli_ifadeler
    )


def test_panel_html_cihazlari_gosterir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    html = panel.html_olustur()

    assert "SyKaşif Ana Makine" in html
    assert "Samsung Ana Saha Terminali" in html
    assert "iPhone Yetkili Yardımcı Terminal" in html
    assert "Kurucu Kaan" in html
    assert "Bilge Kaan" in html


def test_panel_html_komutlari_gosterir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    html = panel.html_olustur()

    assert "durum_iste" in html
    assert "tamamlandı" in html
    assert "SAMSUNG-TABLET" in html
    assert "ANA-MASAUSTU" in html


def test_panel_html_bildirimleri_gosterir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    html = panel.html_olustur()

    assert "Yeni kanıt" in html
    assert (
        "Yeni kanıt incelemeye hazır."
        in html
    )


def test_panel_otomatik_yenileme_suresini_kullanir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    html = panel.html_olustur()

    assert "7000" in html
    assert "7 saniye" in html


def test_terminal_paneli_yolu_calisir() -> None:
    (
        _,
        _,
        _,
        _,
        _,
        istemci,
        _,
        _,
    ) = sistem_olustur()

    yanit = istemci.get(
        "/terminal"
    )

    assert yanit.status_code == 200
    assert (
        "text/html"
        in yanit.headers["content-type"]
    )
    assert "SyKaşif Terminali" in yanit.text


def test_terminal_paneli_veri_yolu_calisir() -> None:
    (
        _,
        _,
        _,
        _,
        _,
        istemci,
        _,
        _,
    ) = sistem_olustur()

    yanit = istemci.get(
        "/terminal/veri"
    )

    assert yanit.status_code == 200
    assert yanit.json()["başarılı"] is True
    assert yanit.json()[
        "panel"
    ]["toplam_cihaz_sayısı"] == 3
    assert yanit.json()[
        "ayarlar"
    ]["yenileme_süresi_saniye"] == 7


def test_panel_uygulama_durumuna_kaydedilir() -> None:
    (
        _,
        _,
        _,
        ag_gecidi,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    assert (
        ag_gecidi.uygulama.state
        .terminal_paneli
        is panel
    )


def test_terminal_panelini_bagla_yardimcisi_calisir() -> None:
    saat = ElleSaat(
        datetime(
            2026,
            8,
            5,
            0,
            20,
            tzinfo=UTC,
        )
    )

    terminal = CalismaTerminali(
        saat=saat.oku
    )

    terminal.cihaz_kaydet(
        YetkiliCihazTanimi(
            cihaz_kimligi="ANA-MASAUSTU",
            ad="Ana Makine",
            cihaz_turu=CihazTuru.MASAUSTU,
            yetki_seviyesi=(
                YetkiSeviyesi.KURUCU_KAAN
            ),
            cihaz_parmak_izi="IZ",
        )
    )

    oturum_yoneticisi = (
        TerminalOturumYoneticisi(
            terminal,
            saat=saat.oku,
        )
    )

    ag_gecidi = TerminalAgGecidi(
        terminal,
        oturum_yoneticisi,
        saat=saat.oku,
    )

    panel = terminal_panelini_bagla(
        ag_gecidi.uygulama,
        terminal,
        oturum_yoneticisi,
        ag_gecidi=ag_gecidi,
        ayarlar=PanelAyarlari(
            baslik="SyKaşif Kontrol Alanı",
        ),
        panel_yolu="/kontrol",
        veri_yolu="/kontrol/veri",
    )

    istemci = TestClient(
        ag_gecidi.uygulama
    )

    yanit = istemci.get(
        "/kontrol"
    )

    assert yanit.status_code == 200
    assert "SyKaşif Kontrol Alanı" in yanit.text
    assert panel.ayarlar.baslik == (
        "SyKaşif Kontrol Alanı"
    )


def test_panel_olaylari_yayinlanir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    panel.anlik_gorunum_olustur()

    konular = [
        olay.topic
        for olay
        in panel.olay_hatti.history
    ]

    assert "terminal.panel.hazir" in konular
    assert (
        "terminal.panel.uygulamaya_baglandi"
        in konular
    )
    assert (
        "terminal.panel.gorunum_olusturuldu"
        in konular
    )


def test_panel_guvenlik_bilgilerini_gosterir() -> None:
    (
        _,
        _,
        _,
        _,
        panel,
        _,
        _,
        _,
    ) = sistem_olustur()

    gorunum = (
        panel.anlik_gorunum_olustur()
    )

    assert gorunum.sistem[
        "insan_onayı"
    ] == "zorunlu"
    assert gorunum.sistem[
        "dışarı_veri_çıkışı"
    ] == "varsayılan_olarak_kapalı"


def test_panel_ayar_sinirlari_uygulanir() -> None:
    (
        _,
        terminal,
        oturum_yoneticisi,
        ag_gecidi,
        _,
        _,
        oturum,
        _,
    ) = sistem_olustur()

    for sira in range(5):
        terminal.bildirim_olustur(
            bildirim_turu=(
                BildirimTuru.BILGI
            ),
            baslik=f"Bildirim {sira}",
            aciklama="Deneme bildirimi",
        )

    panel = TerminalPaneli(
        terminal,
        oturum_yoneticisi,
        ag_gecidi=ag_gecidi,
        ayarlar=PanelAyarlari(
            en_fazla_bildirim_sayisi=2,
            en_fazla_komut_sayisi=1,
            en_fazla_oturum_sayisi=1,
        ),
    )

    gorunum = (
        panel.anlik_gorunum_olustur()
    )

    assert len(gorunum.bildirimler) == 2
    assert len(gorunum.komutlar) == 1
    assert len(gorunum.oturumlar) == 1

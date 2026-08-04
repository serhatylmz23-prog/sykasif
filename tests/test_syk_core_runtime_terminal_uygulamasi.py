from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from syk_core.runtime_terminal import (
    CalismaKipi,
    GuvenliSistemIsletmeni,
    IslemTuru,
    SyKasifTerminalUygulamasi,
    TerminalUygulamasiAyarlari,
    UygulamaTanimi,
    YerelUygulamaIsletmeni,
    YetkiliCihazAyari,
    terminal_uygulamasi_olustur,
)


class ElleSaat:
    def __init__(
        self,
        simdi: datetime,
    ) -> None:
        self.simdi = simdi

    def oku(self) -> datetime:
        return self.simdi


def ayarlar_olustur(
    gecici_dizin: Path,
) -> TerminalUygulamasiAyarlari:
    return TerminalUygulamasiAyarlari(
        calisma_kipi=(
            CalismaKipi.LABORATUVAR
        ),
        ana_makine="127.0.0.1",
        baglanti_noktasi=8114,
        panel_yolu="/terminal",
        panel_veri_yolu="/terminal/veri",
        ana_makine_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        sykasif_uygulama_kimligi=(
            "SYKASIF"
        ),
        sykasif_calistirma_yolu=str(
            gecici_dizin
        ),
        durum_dosyasi=str(
            gecici_dizin
            / "terminal_durumu.json"
        ),
        yetkili_cihazlar=(
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "ANA-MASAUSTU"
                ),
                ad="SyKaşif Ana Makine",
                cihaz_turu="masaüstü",
                yetki_seviyesi=(
                    "Kurucu Kaan"
                ),
                cihaz_parmak_izi=(
                    "MASAUSTU-IZI"
                ),
                baslangicta_bagli=True,
            ),
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "SAMSUNG-TABLET"
                ),
                ad=(
                    "Samsung Ana Saha Terminali"
                ),
                cihaz_turu="tablet",
                yetki_seviyesi=(
                    "Bilge Kaan"
                ),
                cihaz_parmak_izi=(
                    "TABLET-IZI"
                ),
                baslangicta_bagli=False,
            ),
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "IPHONE-8-PLUS"
                ),
                ad=(
                    "iPhone Yetkili Yardımcı Terminal"
                ),
                cihaz_turu="telefon",
                yetki_seviyesi="işletmen",
                cihaz_parmak_izi=(
                    "IPHONE-IZI"
                ),
                baslangicta_bagli=False,
            ),
        ),
    )


def uygulama_olustur(
    tmp_path: Path,
):
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

    terminal_uygulamasi = (
        SyKasifTerminalUygulamasi(
            ayarlar=ayarlar_olustur(
                tmp_path
            ),
            saat=saat.oku,
        )
    )

    return (
        saat,
        terminal_uygulamasi,
        TestClient(
            terminal_uygulamasi.uygulama
        ),
    )


def test_varsayilan_ayarlar_uc_yetkili_cihaz_tanimlar() -> None:
    ayarlar = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    kimlikler = {
        cihaz.cihaz_kimligi
        for cihaz in ayarlar.yetkili_cihazlar
    }

    assert kimlikler == {
        "ANA-MASAUSTU",
        "SAMSUNG-TABLET",
        "IPHONE-8-PLUS",
    }


def test_terminal_uygulamasi_bilesenleri_birlestirir(
    tmp_path: Path,
) -> None:
    _, sistem, _ = uygulama_olustur(
        tmp_path
    )

    assert sistem.terminal is not None
    assert sistem.oturum_yoneticisi is not None
    assert sistem.cihaz_araci is not None
    assert sistem.ag_gecidi is not None
    assert sistem.panel is not None
    assert sistem.uygulama is not None


def test_yetkili_cihazlar_baslangicta_kaydedilir(
    tmp_path: Path,
) -> None:
    _, sistem, _ = uygulama_olustur(
        tmp_path
    )

    cihazlar = (
        sistem.terminal
        .cihazlari_listele()
    )

    assert len(cihazlar) == 3

    assert sistem.terminal.cihaz_getir(
        "ANA-MASAUSTU"
    ).bagli_mi

    assert not sistem.terminal.cihaz_getir(
        "SAMSUNG-TABLET"
    ).bagli_mi

    assert not sistem.terminal.cihaz_getir(
        "IPHONE-8-PLUS"
    ).bagli_mi


def test_sykasif_uygulamasi_araca_kaydedilir(
    tmp_path: Path,
) -> None:
    _, sistem, _ = uygulama_olustur(
        tmp_path
    )

    tanim = (
        sistem.cihaz_araci
        .uygulama_getir("SYKASIF")
    )

    assert tanim.gorunen_ad == "SyKaşif"
    assert tanim.guvenli_kapatma_destegi


def test_terminal_paneli_canli_acilir(
    tmp_path: Path,
) -> None:
    _, _, istemci = uygulama_olustur(
        tmp_path
    )

    yanit = istemci.get(
        "/terminal"
    )

    assert yanit.status_code == 200
    assert "SyKaşif Terminali" in yanit.text
    assert "Yetkili cihazlar" in yanit.text


def test_terminal_paneli_verisi_canli_acilir(
    tmp_path: Path,
) -> None:
    _, _, istemci = uygulama_olustur(
        tmp_path
    )

    yanit = istemci.get(
        "/terminal/veri"
    )

    assert yanit.status_code == 200
    assert yanit.json()[
        "panel"
    ]["toplam_cihaz_sayısı"] == 3


def test_ag_gecidi_saglik_yolu_calisir(
    tmp_path: Path,
) -> None:
    _, _, istemci = uygulama_olustur(
        tmp_path
    )

    yanit = istemci.get(
        "/saglik"
    )

    assert yanit.status_code == 200
    assert yanit.json()["durum"] == "sağlıklı"


def test_tablet_ag_uzerinden_oturum_acar(
    tmp_path: Path,
) -> None:
    _, sistem, istemci = uygulama_olustur(
        tmp_path
    )

    yanit = istemci.post(
        "/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "TABLET-IZI"
            ),
        },
    )

    assert yanit.status_code == 201
    assert yanit.json()[
        "oturum"
    ]["durum"] == "bağlı"

    assert sistem.terminal.cihaz_getir(
        "SAMSUNG-TABLET"
    ).bagli_mi


def test_tablet_terminalden_sykasif_uygulamasini_acar(
    tmp_path: Path,
) -> None:
    _, sistem, istemci = uygulama_olustur(
        tmp_path
    )

    oturum_yaniti = istemci.post(
        "/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "TABLET-IZI"
            ),
        },
    )

    oturum_kimligi = (
        oturum_yaniti.json()
        ["oturum"]
        ["oturum_kimliği"]
    )

    komut_yaniti = istemci.post(
        "/komutlar",
        json={
            "oturum_kimliği": (
                oturum_kimligi
            ),
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "komut_türü": (
                "uygulamayı_aç"
            ),
            "içerik": {
                "uygulama_kimliği": (
                    "SYKASIF"
                ),
            },
            "gerekçe": (
                "Laboratuvar çalışması"
            ),
            "hemen_çalıştır": True,
        },
    )

    assert komut_yaniti.status_code == 201
    assert komut_yaniti.json()[
        "komut"
    ]["durum"] == "tamamlandı"

    assert (
        sistem.cihaz_araci
        .uygulama_durumu_getir(
            "SYKASIF"
        )
        .calisiyor_mu
    )


def test_gercek_uygulama_islemi_varsayilan_olarak_kapali() -> None:
    isletmen = (
        YerelUygulamaIsletmeni()
    )

    islem_kimligi = isletmen.baslat(
        UygulamaTanimi(
            uygulama_kimligi="DENEME",
            gorunen_ad="Deneme",
            calistirma_yolu=(
                "bulunmayan-yol"
            ),
        )
    )

    assert islem_kimligi > 50000


def test_gercek_sistem_islemi_varsayilan_olarak_kapali() -> None:
    isletmen = (
        GuvenliSistemIsletmeni()
    )

    sonuc = isletmen.calistir(
        IslemTuru.MASAUSTUNU_KAPAT,
        {
            "gerekçe": "Deneme",
        },
    )

    assert sonuc[
        "gerçek_işlem"
    ] is False
    assert "yalnız kayıt" in sonuc[
        "açıklama"
    ]


def test_durum_kaydi_json_olarak_yazilir(
    tmp_path: Path,
) -> None:
    _, sistem, _ = uygulama_olustur(
        tmp_path
    )

    yol = sistem.durum_kaydi_yaz()

    assert yol.exists()

    veri = json.loads(
        yol.read_text(
            encoding="utf-8"
        )
    )

    assert veri["sistem"] == "SyKaşif"
    assert veri["durum"] == "hazır"
    assert veri["çalışma_kipi"] == (
        "laboratuvar"
    )


def test_durum_ozeti_turkce_anahtarlar_kullanir(
    tmp_path: Path,
) -> None:
    _, sistem, _ = uygulama_olustur(
        tmp_path
    )

    ozet = sistem.durum_ozeti()

    assert "çalışma_kipi" in ozet
    assert "ağ_geçidi" in ozet
    assert "cihaz_aracı" in ozet
    assert "oturumlar" in ozet


def test_guvenli_durdurma_etkin_oturumlari_kapatir(
    tmp_path: Path,
) -> None:
    _, sistem, istemci = uygulama_olustur(
        tmp_path
    )

    yanit = istemci.post(
        "/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "TABLET-IZI"
            ),
        },
    )

    assert yanit.status_code == 201

    sistem.guvenli_durdur()

    oturumlar = (
        sistem.oturum_yoneticisi
        .oturumlari_listele()
    )

    assert len(oturumlar) == 1
    assert oturumlar[0].sona_erdi_mi


def test_fastapi_yardimci_uygulama_olusturur(
    tmp_path: Path,
) -> None:
    uygulama = terminal_uygulamasi_olustur(
        ayarlar=ayarlar_olustur(
            tmp_path
        )
    )

    istemci = TestClient(
        uygulama
    )

    yanit = istemci.get(
        "/terminal"
    )

    assert yanit.status_code == 200


def test_uygulama_durumuna_terminal_nesnesi_kaydedilir(
    tmp_path: Path,
) -> None:
    _, sistem, _ = uygulama_olustur(
        tmp_path
    )

    assert (
        sistem.uygulama.state
        .sykasif_terminal
        is sistem
    )

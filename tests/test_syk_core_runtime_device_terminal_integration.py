from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from syk_core.runtime_device_link import (
    TerminalCihazAnahtarlari,
    terminale_cihaz_iletisimini_bagla,
)
from syk_core.runtime_terminal import (
    SyKasifTerminalUygulamasi,
    TerminalUygulamasiAyarlari,
)


def sistem_olustur(
    tmp_path: Path,
):
    varsayilan = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    ayarlar = TerminalUygulamasiAyarlari(
        ana_makine="127.0.0.1",
        baglanti_noktasi=8314,
        panel_yolu="/terminal",
        panel_veri_yolu="/terminal/veri",
        ana_makine_cihaz_kimligi=(
            varsayilan
            .ana_makine_cihaz_kimligi
        ),
        sykasif_uygulama_kimligi=(
            varsayilan
            .sykasif_uygulama_kimligi
        ),
        sykasif_calistirma_yolu=str(
            tmp_path
        ),
        durum_dosyasi=str(
            tmp_path
            / "terminal_durumu.json"
        ),
        yetkili_cihazlar=(
            varsayilan.yetkili_cihazlar
        ),
    )

    terminal = SyKasifTerminalUygulamasi(
        ayarlar=ayarlar
    )

    kopru = terminale_cihaz_iletisimini_bagla(
        terminal,
        anahtarlar=TerminalCihazAnahtarlari(
            ana_masaustu=(
                "MASAUSTU-ANAHTARI"
            ),
            samsung_tablet=(
                "TABLET-ANAHTARI"
            ),
            iphone=(
                "IPHONE-ANAHTARI"
            ),
        ),
    )

    istemci = TestClient(
        terminal.uygulama
    )

    return terminal, kopru, istemci


def tablet_oturumu_ac(
    istemci: TestClient,
) -> str:
    yanit = istemci.post(
        "/cihaz-iletisimi/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "gizli_anahtar": (
                "TABLET-ANAHTARI"
            ),
        },
    )

    assert yanit.status_code == 201

    return yanit.json()[
        "oturum"
    ][
        "oturum_kimliği"
    ]


def test_terminal_ve_cihaz_api_ayni_uygulamada(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    assert istemci.get(
        "/terminal"
    ).status_code == 200

    assert istemci.get(
        "/cihaz-iletisimi/saglik"
    ).status_code == 200


def test_uc_yetkili_cihaz_kaydedilir(
    tmp_path: Path,
) -> None:
    _, kopru, _ = sistem_olustur(
        tmp_path
    )

    assert kopru.yonetici.durum_ozeti()[
        "kayıtlı_cihaz_sayısı"
    ] == 3


def test_tablet_terminale_oturum_acar(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    assert oturum_kimligi.startswith(
        "SYK-CIHAZ-OTURUM-"
    )


def test_tablet_runtime_durumunu_okur(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/komutlar",
        json={
            "oturum_kimliği": (
                oturum_kimligi
            ),
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "işlem_yetkisi": (
                "durum_oku"
            ),
            "hemen_çalıştır": True,
        },
    )

    assert yanit.status_code == 201

    komut = yanit.json()[
        "komut"
    ]

    assert komut[
        "durum"
    ] == "tamamlandı"

    assert komut[
        "sonuç"
    ][
        "runtime_terminal"
    ][
        "sistem"
    ] == "SyKaşif"


def test_tablet_sykasif_uygulamasini_acar(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    oturum_kimligi = tablet_oturumu_ac(
        istemci
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/komutlar",
        json={
            "oturum_kimliği": (
                oturum_kimligi
            ),
            "hedef_cihaz_kimliği": (
                "ANA-MASAUSTU"
            ),
            "işlem_yetkisi": (
                "uygulama_aç"
            ),
            "içerik": {
                "uygulama_kimliği": (
                    "SYKASIF"
                ),
            },
            "hemen_çalıştır": True,
        },
    )

    assert yanit.status_code == 201

    sonuc = yanit.json()[
        "komut"
    ][
        "sonuç"
    ]

    assert sonuc[
        "durum"
    ] == "açıldı"

    assert sonuc[
        "işlem_kimliği"
    ] > 50000

    assert sonuc[
        "gerçek_işlem"
    ] is False


def test_gercek_islem_varsayilan_kapali(
    tmp_path: Path,
) -> None:
    terminal, _, _ = sistem_olustur(
        tmp_path
    )

    assert (
        terminal
        .uygulama_isletmeni
        .gercek_isleme_izin_ver
        is False
    )


def test_kopru_uygulama_durumuna_kaydedilir(
    tmp_path: Path,
) -> None:
    terminal, kopru, _ = sistem_olustur(
        tmp_path
    )

    assert (
        terminal.uygulama.state
        .cihaz_iletisim_koprusu
        is kopru
    )


def test_kopru_durum_ozeti_turkce(
    tmp_path: Path,
) -> None:
    _, kopru, _ = sistem_olustur(
        tmp_path
    )

    ozet = kopru.durum_ozeti()

    assert ozet["durum"] == "hazır"
    assert "terminal" in ozet
    assert "cihaz_iletişimi" in ozet


def test_yanlis_tablet_anahtari_reddedilir(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    yanit = istemci.post(
        "/cihaz-iletisimi/oturumlar/ac",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "gizli_anahtar": (
                "YANLIS-ANAHTAR"
            ),
        },
    )

    assert yanit.status_code == 401

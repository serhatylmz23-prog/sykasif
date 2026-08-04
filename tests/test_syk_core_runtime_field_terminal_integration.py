from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from syk_core.runtime_field_link import (
    SahaTerminalEntegrasyonHatasi,
    terminale_saha_cihazlarini_bagla,
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
        baglanti_noktasi=8514,
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
            / "saha_terminal_durumu.json"
        ),
        yetkili_cihazlar=(
            varsayilan.yetkili_cihazlar
        ),
    )

    terminal = SyKasifTerminalUygulamasi(
        ayarlar=ayarlar
    )

    kopru = terminale_saha_cihazlarini_bagla(
        terminal,
        ana_gizli_deger=(
            "SPR-008-SAHA-TERMINAL-GIZLI"
        ),
    )

    istemci = TestClient(
        terminal.uygulama
    )

    return terminal, kopru, istemci


def eslestirme_baslat(
    istemci: TestClient,
) -> tuple[str, str]:
    yanit = istemci.post(
        "/saha-cihazlari/eslestirme",
        json={
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_adı": (
                "Samsung Ana Saha Terminali"
            ),
            "cihaz_türü": "tablet",
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "yerel_ağ_adresi": (
                "192.168.1.20"
            ),
            "yetenekler": [
                "terminal",
                "kamera",
                "konum",
            ],
        },
    )

    assert yanit.status_code == 201

    veri = yanit.json()

    return (
        veri["eşleştirme"][
            "istek_kimliği"
        ],
        veri["tek_kullanımlık_kod"],
    )


def test_terminal_ve_saha_api_ayni_uygulamadadir(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    assert istemci.get(
        "/terminal"
    ).status_code == 200

    assert istemci.get(
        "/saha-cihazlari/saglik"
    ).status_code == 200


def test_saha_koprusu_uygulama_durumuna_kaydedilir(
    tmp_path: Path,
) -> None:
    terminal, kopru, _ = sistem_olustur(
        tmp_path
    )

    assert (
        terminal.uygulama.state
        .saha_terminal_koprusu
        is kopru
    )


def test_tablet_eslestirmesi_terminal_uzerinden_baslar(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    istek_kimligi, kod = (
        eslestirme_baslat(
            istemci
        )
    )

    assert istek_kimligi.startswith(
        "SYK-SAHA-ESLESTIRME-"
    )

    assert len(kod) == 6


def test_bilge_kaan_terminal_uzerinden_onaylar(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    istek_kimligi, _ = (
        eslestirme_baslat(
            istemci
        )
    )

    yanit = istemci.post(
        f"/saha-cihazlari/eslestirme/"
        f"{istek_kimligi}/onayla",
        json={
            "onaylayan": "Bilge Kaan"
        },
    )

    assert yanit.status_code == 200

    assert yanit.json()[
        "eşleştirme"
    ][
        "durum"
    ] == "onaylandı"


def test_tablet_terminal_uzerinden_eslesir(
    tmp_path: Path,
) -> None:
    _, _, istemci = sistem_olustur(
        tmp_path
    )

    istek_kimligi, kod = (
        eslestirme_baslat(
            istemci
        )
    )

    istemci.post(
        f"/saha-cihazlari/eslestirme/"
        f"{istek_kimligi}/onayla",
        json={
            "onaylayan": "Bilge Kaan"
        },
    )

    yanit = istemci.post(
        f"/saha-cihazlari/eslestirme/"
        f"{istek_kimligi}/tamamla",
        json={
            "kod": kod,
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "ağ_adresi": (
                "192.168.1.20"
            ),
            "hizmet_noktası": 8014,
        },
    )

    assert yanit.status_code == 200

    assert yanit.json()[
        "cihaz"
    ][
        "durum"
    ] == "bağlı"

    assert yanit.json()[
        "oturum_anahtarı"
    ]


def test_birlesik_durum_ozeti_turkcedir(
    tmp_path: Path,
) -> None:
    _, kopru, _ = sistem_olustur(
        tmp_path
    )

    ozet = kopru.durum_ozeti()

    assert ozet["durum"] == "hazır"
    assert "runtime_terminal" in ozet
    assert "saha_cihazları" in ozet


def test_bos_gizli_deger_reddedilir(
    tmp_path: Path,
) -> None:
    ayarlar = (
        TerminalUygulamasiAyarlari
        .varsayilan()
    )

    terminal = SyKasifTerminalUygulamasi(
        ayarlar=ayarlar
    )

    try:
        terminale_saha_cihazlarini_bagla(
            terminal,
            ana_gizli_deger="",
        )
    except SahaTerminalEntegrasyonHatasi:
        return

    raise AssertionError(
        "Boş gizli değer reddedilmedi."
    )

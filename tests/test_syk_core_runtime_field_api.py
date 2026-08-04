from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_core.runtime_field_link import (
    SahaCihazAgGecidi,
    SahaCihazEslestirmeYoneticisi,
    SahaCihazKesifYoneticisi,
    SahaCihazYoneticisi,
    saha_cihaz_ag_gecidini_bagla,
)


class SabitSaat:
    def __init__(self) -> None:
        self.simdi = datetime(
            2026,
            8,
            5,
            3,
            0,
            tzinfo=UTC,
        )

    def oku(self) -> datetime:
        return self.simdi


def sistem_olustur():
    saat = SabitSaat()

    yonetici = SahaCihazYoneticisi(
        eslestirme=(
            SahaCihazEslestirmeYoneticisi(
                saat=saat.oku,
                ana_gizli_deger="SAHA-GIZLI",
            )
        ),
        kesif=SahaCihazKesifYoneticisi(
            saat=saat.oku
        ),
    )

    uygulama = FastAPI()

    gecit = saha_cihaz_ag_gecidini_bagla(
        uygulama,
        yonetici,
    )

    return (
        yonetici,
        gecit,
        TestClient(uygulama),
    )


def eslestirme_baslat(
    istemci: TestClient,
) -> tuple[str, str]:
    yanit = istemci.post(
        "/saha-cihazlari/eslestirme",
        json={
            "cihaz_kimliği": "SAMSUNG-TABLET",
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


def test_saglik_yolu_calisir() -> None:
    _, _, istemci = sistem_olustur()

    yanit = istemci.get(
        "/saha-cihazlari/saglik"
    )

    assert yanit.status_code == 200
    assert yanit.json()["durum"] == (
        "sağlıklı"
    )


def test_eslestirme_http_uzerinden_baslar() -> None:
    _, _, istemci = sistem_olustur()

    istek_kimligi, kod = (
        eslestirme_baslat(istemci)
    )

    assert istek_kimligi.startswith(
        "SYK-SAHA-ESLESTIRME-"
    )
    assert len(kod) == 6


def test_bilge_kaan_http_uzerinden_onaylar() -> None:
    _, _, istemci = sistem_olustur()

    istek_kimligi, _ = (
        eslestirme_baslat(istemci)
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


def test_yetkisiz_onay_reddedilir() -> None:
    _, _, istemci = sistem_olustur()

    istek_kimligi, _ = (
        eslestirme_baslat(istemci)
    )

    yanit = istemci.post(
        f"/saha-cihazlari/eslestirme/"
        f"{istek_kimligi}/onayla",
        json={
            "onaylayan": "işletmen"
        },
    )

    assert yanit.status_code == 403


def test_eslestirme_http_uzerinden_tamamlanir() -> None:
    _, _, istemci = sistem_olustur()

    istek_kimligi, kod = (
        eslestirme_baslat(istemci)
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
            "ağ_adresi": "192.168.1.20",
            "hizmet_noktası": 8014,
        },
    )

    assert yanit.status_code == 200
    assert yanit.json()["cihaz"][
        "durum"
    ] == "bağlı"
    assert yanit.json()[
        "oturum_anahtarı"
    ]


def test_yanlis_kod_reddedilir() -> None:
    _, _, istemci = sistem_olustur()

    istek_kimligi, _ = (
        eslestirme_baslat(istemci)
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
            "kod": "000000",
            "cihaz_kimliği": (
                "SAMSUNG-TABLET"
            ),
            "cihaz_parmak_izi": (
                "SAMSUNG-TABLET-PARMAK-IZI"
            ),
            "ağ_adresi": "192.168.1.20",
            "hizmet_noktası": 8014,
        },
    )

    assert yanit.status_code == 400


def test_durum_yolu_turkcedir() -> None:
    _, _, istemci = sistem_olustur()

    yanit = istemci.get(
        "/saha-cihazlari/durum"
    )

    assert yanit.status_code == 200
    assert "eşleştirme" in (
        yanit.json()["durum"]
    )
    assert "keşif" in (
        yanit.json()["durum"]
    )


def test_ag_gecidi_uygulama_durumundadir() -> None:
    _, gecit, _ = sistem_olustur()

    assert (
        gecit.uygulama.state
        .saha_cihaz_ag_gecidi
        is gecit
    )


def test_ag_gecidi_dogrudan_olusturulur() -> None:
    yonetici, _, _ = sistem_olustur()

    gecit = SahaCihazAgGecidi(
        yonetici
    )

    istemci = TestClient(
        gecit.uygulama
    )

    assert istemci.get(
        "/saha-cihazlari/saglik"
    ).status_code == 200

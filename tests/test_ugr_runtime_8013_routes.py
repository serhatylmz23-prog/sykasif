from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from syk_simulasyon.syk_ui_runtime.ugr_runtime_routes import (
    ugr_router,
)


ROOT = Path(__file__).resolve().parents[1]

UGR_ROUTE = (
    ROOT
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "ugr_runtime_routes.py"
)

ANA_SUNUCU = (
    ROOT
    / "src"
    / "syk_simulasyon"
    / "runtime_ui_sunucusu.py"
)

MANIFEST = (
    ROOT
    / "src"
    / "syk_ui"
    / "icons"
    / "ugr"
    / "manifests"
    / "ugr_prototype_icons_manifest.json"
)


@pytest.fixture()
def istemci() -> TestClient:
    uygulama = FastAPI()
    uygulama.include_router(
        ugr_router
    )

    return TestClient(
        uygulama
    )


def test_ugr_router_api_router_nesnesidir() -> None:
    assert ugr_router.prefix == "/api/ugr"
    assert len(ugr_router.routes) >= 13


def test_ugr_route_dosyasi_soz_dizimi_gecerli() -> None:
    icerik = UGR_ROUTE.read_text(
        encoding="utf-8-sig"
    )

    ast.parse(
        icerik,
        filename=str(UGR_ROUTE),
    )


def test_ana_sunucu_ugr_router_importunu_tasir() -> None:
    icerik = ANA_SUNUCU.read_text(
        encoding="utf-8-sig"
    )

    assert (
        "# SYK_UGR_RUNTIME_ROUTER_IMPORT"
        in icerik
    )

    assert (
        "ugr_router as syk_ugr_router"
        in icerik
    )


def test_ana_sunucu_include_router_baglantisini_tasir() -> None:
    icerik = ANA_SUNUCU.read_text(
        encoding="utf-8-sig"
    )

    assert (
        "# SYK_UGR_RUNTIME_ROUTER_BAGLANTISI"
        in icerik
    )

    assert (
        "include_router("
        in icerik
    )

    assert (
        "syk_ugr_router"
        in icerik
    )


def test_gercek_manifest_215_ikon_tasir() -> None:
    veri = json.loads(
        MANIFEST.read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        int(
            veri["icon_count"]
        )
        == 215
    )

    assert (
        len(
            veri["icons"]
        )
        == 215
    )


def test_saglik_route_200_dondurur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        "/api/ugr/health"
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert veri["durum"] == "saglikli"
    assert veri["runtime_portu"] == 8013
    assert veri["toplam_ikon"] == 215


def test_snapshot_215_ikon_dondurur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        "/api/ugr/snapshot"
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert (
        veri["olay_turu"]
        == "snapshot"
    )

    assert (
        veri["veri"]["toplam_ikon"]
        == 215
    )


def test_ikon_listesi_dondurulur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        "/api/ugr/icons",
        params={
            "limit": 10,
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert len(
        veri["ikonlar"]
    ) == 10

    assert veri["toplam_ikon"] == 215


def test_ikon_durumu_canli_degistirilir(
    istemci: TestClient,
) -> None:
    yanit = istemci.post(
        "/api/ugr/icons/sys-001/state",
        json={
            "durum": "calisiyor",
            "neden": "Route testi.",
            "zorla": True,
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert (
        veri["ikon"]["durum"]
        == "calisiyor"
    )

    assert (
        veri["stil"]["animasyon"]
        == "nabiz"
    )


def test_ikon_ar_gorunumu_uygulanir(
    istemci: TestClient,
) -> None:
    yanit = istemci.post(
        "/api/ugr/icons/sys-001/view",
        json={
            "gorunum_modu": "ar",
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert (
        veri["gorunum_modu"]
        == "ar"
    )


def test_ikon_pasif_yapilabilir(
    istemci: TestClient,
) -> None:
    yanit = istemci.post(
        "/api/ugr/icons/sys-001/active",
        json={
            "aktif": False,
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert veri["aktif"] is False


def test_toplu_ikon_durumu_degistirilir(
    istemci: TestClient,
) -> None:
    yanit = istemci.post(
        "/api/ugr/icons/bulk/state",
        json={
            "ikon_kimlikleri": [
                "sys-001",
                "sys-002",
                "sys-003",
            ],
            "durum": "uyari",
            "neden": "Toplu route testi.",
            "zorla": True,
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert (
        veri["olay_turu"]
        == "toplu_guncelleme"
    )

    assert (
        veri["veri"][
            "basarili_ikon_sayisi"
        ]
        == 3
    )


def test_olay_gecmisi_json_dondurur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        "/api/ugr/events/history",
        params={
            "adet": 20,
        },
    )

    assert yanit.status_code == 200

    veri = yanit.json()

    assert "olay_sayisi" in veri
    assert "olaylar" in veri


def test_onizleme_html_dondurur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        "/api/ugr/preview"
    )

    assert yanit.status_code == 200

    assert (
        "SyKaşif UGR"
        in yanit.text
        or "syk-ugr-icon"
        in yanit.text
    )


def test_css_statigi_sunulur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        (
            "/api/ugr/assets/"
            "web/static/css/"
            "ugr_dynamic_icons.css"
        )
    )

    assert yanit.status_code == 200

    assert (
        ".syk-ugr-icon"
        in yanit.text
    )


def test_javascript_statigi_sunulur(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        (
            "/api/ugr/assets/"
            "web/static/js/"
            "ugr_dynamic_icons.js"
        )
    )

    assert yanit.status_code == 200

    assert (
        "UgrDynamicIconRuntime"
        in yanit.text
    )


def test_dizin_disina_cikis_reddedilir(
    istemci: TestClient,
) -> None:
    yanit = istemci.get(
        (
            "/api/ugr/assets/"
            "..%2F..%2F..%2Fpyproject.toml"
        )
    )

    assert yanit.status_code in {
        403,
        404,
    }


def test_gecersiz_durum_422_dondurur(
    istemci: TestClient,
) -> None:
    yanit = istemci.post(
        "/api/ugr/icons/sys-001/state",
        json={
            "durum": "gecersiz",
            "neden": "Test.",
        },
    )

    assert yanit.status_code == 422


def test_gecersiz_gorunum_422_dondurur(
    istemci: TestClient,
) -> None:
    yanit = istemci.post(
        "/api/ugr/icons/sys-001/view",
        json={
            "gorunum_modu": "5b",
        },
    )

    assert yanit.status_code == 422


def test_ana_sunucu_modulu_import_edilebilir() -> None:
    modul = importlib.import_module(
        "syk_simulasyon.runtime_ui_sunucusu"
    )

    kaynak = ANA_SUNUCU.read_text(
        encoding="utf-8-sig"
    )

    assert (
        "syk_ugr_router"
        in kaynak
    )

    assert modul is not None

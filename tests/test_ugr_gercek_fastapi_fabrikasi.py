from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PATCH_REPORT = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_007_gercek_fastapi_fabrikasi_patch"
    / "GERCEK_FASTAPI_FABRIKASI_PATCH_RAPORU.json"
)

LIVE_REPORT = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_007_gercek_fastapi_fabrikasi_patch"
    / "GERCEK_FASTAPI_UGR_CANLI_SONUC.json"
)


def patch_verisi() -> dict:
    return json.loads(
        PATCH_REPORT.read_text(
            encoding="utf-8-sig"
        )
    )


def canli_veri() -> dict:
    return json.loads(
        LIVE_REPORT.read_text(
            encoding="utf-8-sig"
        )
    )


def test_gercek_fastapi_adayi_bulunmustur() -> None:
    veri = patch_verisi()

    assert (
        veri["toplam_fastapi_adayi"]
        >= 1
    )

    assert veri["secili_aday"]


def test_ugr_router_gercek_uygulamaya_baglanmistir() -> None:
    veri = patch_verisi()

    assert (
        veri["runtime_dogrulama"][
            "import_edildi"
        ]
        is True
    )


def test_canli_dogrulama_basarilidir() -> None:
    veri = canli_veri()

    assert (
        veri["genel_durum"]
        == "basarili"
    )

    assert (
        veri["basarisiz_denetim"]
        == 0
    )


def test_canli_runtime_8013_portunda_acilmistir() -> None:
    veri = canli_veri()

    assert veri["port"] == 8013


def test_canli_openapi_ugr_yollarini_tasir() -> None:
    veri = canli_veri()

    assert (
        veri["openapi_ugr_yol_sayisi"]
        >= 13
    )

    assert (
        "/api/ugr/health"
        in veri["openapi_ugr_yollari"]
    )

    assert (
        "/api/ugr/snapshot"
        in veri["openapi_ugr_yollari"]
    )


def test_canli_saglik_215_ikon_dondurur() -> None:
    veri = canli_veri()

    assert (
        veri["health_toplam_ikon"]
        == 215
    )


def test_sekiz_canli_denetim_gecmistir() -> None:
    veri = canli_veri()

    assert (
        veri["toplam_denetim"]
        == 8
    )

    assert (
        veri["basarili_denetim"]
        == 8
    )


def test_canli_css_ve_javascript_gecmistir() -> None:
    veri = canli_veri()

    yollar = {
        kayit["path"]:
            kayit["status_code"]
        for kayit in veri["checks"]
    }

    assert yollar[
        (
            "/api/ugr/assets/"
            "web/static/css/"
            "ugr_dynamic_icons.css"
        )
    ] == 200

    assert yollar[
        (
            "/api/ugr/assets/"
            "web/static/js/"
            "ugr_dynamic_icons.js"
        )
    ] == 200


def test_canli_bulk_rotasi_gecmistir() -> None:
    veri = canli_veri()

    kayit = next(
        kayit
        for kayit
        in veri["checks"]
        if (
            kayit["path"]
            == "/api/ugr/icons/bulk/state"
        )
    )

    assert (
        kayit["status_code"]
        == 200
    )

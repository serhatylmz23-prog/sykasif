from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SONUC = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_007_runtime_8013_canli_dogrulama"
    / "ugr_runtime_8013_canli_sonuc.json"
)


def sonuc_verisi() -> dict:
    return json.loads(
        SONUC.read_text(
            encoding="utf-8-sig"
        )
    )


def test_canli_sonuc_dosyasi_olusmustur() -> None:
    assert SONUC.exists()


def test_canli_dogrulama_tamamen_basarilidir() -> None:
    veri = sonuc_verisi()

    assert veri["genel_durum"] == "basarili"
    assert veri["basarisiz_denetim"] == 0


def test_runtime_8013_portu_dogrulanmistir() -> None:
    veri = sonuc_verisi()

    assert veri["port"] == 8013

    assert (
        veri["base_url"]
        == "http://127.0.0.1:8013"
    )


def test_sekiz_canli_denetim_gecmistir() -> None:
    veri = sonuc_verisi()

    assert veri["toplam_denetim"] == 8
    assert veri["basarili_denetim"] == 8


def test_http_health_gecmistir() -> None:
    veri = sonuc_verisi()

    kayit = next(
        sonuc
        for sonuc in veri["sonuclar"]
        if sonuc["ad"] == "HTTP_HEALTH"
    )

    assert kayit["basarili"] is True
    assert kayit["durum_kodu"] == 200

    assert (
        kayit["ayrintilar"][
            "toplam_ikon"
        ]
        == 215
    )


def test_snapshot_215_ikon_dondurmustur() -> None:
    veri = sonuc_verisi()

    kayit = next(
        sonuc
        for sonuc in veri["sonuclar"]
        if sonuc["ad"] == "HTTP_SNAPSHOT"
    )

    assert kayit["basarili"] is True

    assert (
        kayit["ayrintilar"][
            "dondurulen_ikon"
        ]
        == 215
    )


def test_css_ve_javascript_canli_erisimlidir() -> None:
    veri = sonuc_verisi()

    sonuc_adlari = {
        sonuc["ad"]
        for sonuc in veri["sonuclar"]
        if sonuc["basarili"]
    }

    assert "HTTP_CSS" in sonuc_adlari
    assert "HTTP_JAVASCRIPT" in sonuc_adlari


def test_bulk_rotasi_canli_agda_gecmistir() -> None:
    veri = sonuc_verisi()

    kayit = next(
        sonuc
        for sonuc in veri["sonuclar"]
        if sonuc["ad"] == "HTTP_TOPLU_DURUM"
    )

    assert kayit["basarili"] is True

    assert (
        kayit["ayrintilar"][
            "basarili_ikon"
        ]
        == 3
    )


def test_sse_canli_ikon_olayi_alinmistir() -> None:
    veri = sonuc_verisi()

    kayit = next(
        sonuc
        for sonuc in veri["sonuclar"]
        if sonuc["ad"]
        == "SSE_CANLI_IKON_OLAYI"
    )

    assert kayit["basarili"] is True

    assert (
        kayit["ayrintilar"][
            "olay_turu"
        ]
        == "ikon_durumu"
    )

    assert (
        kayit["ayrintilar"][
            "ikon_kimligi"
        ]
        == "sys-004"
    )

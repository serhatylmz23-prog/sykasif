import json

import pytest
from fastapi.testclient import TestClient

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)
from syk_simulasyon.runtime_olay_gunlugu import (
    RuntimeOlayGunluguButunlukHatasi,
)


def test_saglik_rotasi_gunluk_yokken_hazir_doner(
    monkeypatch,
):
    monkeypatch.delenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        raising=False,
    )

    istemci = TestClient(uygulama_olustur())

    yanit = istemci.get("/runtime/health")
    veri = yanit.json()

    assert yanit.status_code == 200
    assert veri["durum"] == "?al???yor"
    assert veri["hazir"] is True
    assert veri["kalici_gunluk"] == {
        "etkin": False,
        "butunluk": "kullan?lm?yor",
        "yol": None,
        "kayit_sayisi": 0,
    }


def test_saglik_rotasi_saglam_gunlugu_bildirir(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )

    uygulama = uygulama_olustur()

    uygulama.state.runtime_servisi.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0015",
    )

    yanit = TestClient(uygulama).get(
        "/runtime/health"
    )
    veri = yanit.json()

    assert yanit.status_code == 200
    assert veri["hazir"] is True
    assert veri["kalici_gunluk"]["etkin"] is True
    assert (
        veri["kalici_gunluk"]["butunluk"]
        == "sa?lam"
    )
    assert veri["kalici_gunluk"]["kayit_sayisi"] == 1
    assert veri["kalici_gunluk"]["yol"] == str(
        gunluk_yolu
    )


def test_saglik_rotasi_sonradan_bozulan_gunlukte_503_doner(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )

    uygulama = uygulama_olustur()

    uygulama.state.runtime_servisi.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0015",
    )

    kayit = json.loads(
        gunluk_yolu.read_text(encoding="utf-8")
    )

    kayit["olay"]["ortak_veri"]["durum"] = (
        "de?i?tirildi"
    )

    gunluk_yolu.write_text(
        json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    yanit = TestClient(uygulama).get(
        "/runtime/health"
    )
    veri = yanit.json()

    assert yanit.status_code == 503
    assert veri["durum"] == "hatal?"
    assert veri["hazir"] is False
    assert (
        veri["kalici_gunluk"]["butunluk"]
        == "bozuk"
    )


def test_bozuk_gunlukle_uygulama_baslatilmaz(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    gunluk_yolu.write_text(
        "{gecersiz-json}\n",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )

    with pytest.raises(
        RuntimeOlayGunluguButunlukHatasi
    ):
        uygulama_olustur()

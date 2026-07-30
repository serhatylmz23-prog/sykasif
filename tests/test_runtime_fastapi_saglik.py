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
    assert "yol" not in veri["kalici_gunluk"]


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


def test_saglik_rotasi_varsayilan_olarak_ic_hatayi_gizler(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )
    monkeypatch.delenv(
        "SYK_RUNTIME_TANILAMA",
        raising=False,
    )

    uygulama = uygulama_olustur()

    uygulama.state.runtime_servisi.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0016",
    )

    kayit = json.loads(
        gunluk_yolu.read_text(encoding="utf-8")
    )
    kayit["kayit_hash"] = "0" * 64

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
    assert "hata" not in veri
    assert "yol" not in veri["kalici_gunluk"]
    assert str(gunluk_yolu) not in yanit.text


def test_tanilama_etkinken_saglam_gunluk_yolu_gosterilir(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )
    monkeypatch.setenv(
        "SYK_RUNTIME_TANILAMA",
        "1",
    )

    uygulama = uygulama_olustur()

    yanit = TestClient(uygulama).get(
        "/runtime/health"
    )
    veri = yanit.json()

    assert yanit.status_code == 200
    assert (
        veri["kalici_gunluk"]["yol"]
        == str(gunluk_yolu)
    )


def test_tanilama_etkinken_bozukluk_ayrintisi_gosterilir(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )
    monkeypatch.setenv(
        "SYK_RUNTIME_TANILAMA",
        "true",
    )

    uygulama = uygulama_olustur()

    uygulama.state.runtime_servisi.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0016",
    )

    kayit = json.loads(
        gunluk_yolu.read_text(encoding="utf-8")
    )
    kayit["kayit_hash"] = "0" * 64

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
    assert veri["hata"]
    assert (
        veri["kalici_gunluk"]["yol"]
        == str(gunluk_yolu)
    )

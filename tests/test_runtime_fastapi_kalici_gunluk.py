from pathlib import Path

from syk_simulasyon.runtime_fastapi_sunucusu import (
    uygulama_olustur,
)


def test_ortam_degiskani_kalici_gunlugu_devreye_alir(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )

    uygulama = uygulama_olustur()
    servis = uygulama.state.runtime_servisi

    servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0014",
    )

    assert gunluk_yolu.exists()
    assert gunluk_yolu.read_text(
        encoding="utf-8"
    ).strip()

    assert (
        uygulama.state.runtime_olay_gunlugu_yolu
        == str(gunluk_yolu)
    )


def test_yeni_uygulama_ayni_gunlukten_gecmisi_yukler(
    tmp_path,
    monkeypatch,
):
    gunluk_yolu = tmp_path / "runtime-olaylari.jsonl"

    monkeypatch.setenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        str(gunluk_yolu),
    )

    birinci = uygulama_olustur()

    olay = birinci.state.runtime_servisi.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0014",
    )

    ikinci = uygulama_olustur()

    assert (
        ikinci.state.runtime_servisi.olay_gecmisi()
        == (olay,)
    )


def test_ortam_degiskani_yokken_geriye_uyum_korunur(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv(
        "SYK_RUNTIME_OLAY_GUNLUGU",
        raising=False,
    )

    monkeypatch.chdir(tmp_path)

    uygulama = uygulama_olustur()
    servis = uygulama.state.runtime_servisi

    servis.olay_uret(
        arastirma_kimligi="SPR002",
        deney_numarasi="DSP0014",
    )

    assert servis.son_olay() is not None
    assert (
        uygulama.state.runtime_olay_gunlugu_yolu
        is None
    )
    assert not list(
        Path(tmp_path).glob("*.jsonl")
    )

from __future__ import annotations

import json
from pathlib import Path

import pytest

from syk_core.runtime_prototype import (
    PrototipBaslatmaSecenekleri,
    PrototipBaslaticiHatasi,
    PrototipBaslaticisi,
    guvenlik_ayarlari_ortamdan,
    main,
    prototip_ayarlari_olustur,
)


def ortam() -> dict[str, str]:
    return {
        "SYK_ANA_MASAUSTU_ANAHTARI": (
            "MASAUSTU-ANAHTARI"
        ),
        "SYK_SAMSUNG_TABLET_ANAHTARI": (
            "TABLET-ANAHTARI"
        ),
        "SYK_IPHONE_ANAHTARI": (
            "IPHONE-ANAHTARI"
        ),
        "SYK_SAHA_ANA_GIZLI_DEGERI": (
            "SAHA-ANA-GIZLI-DEGERI"
        ),
    }


def test_guvenlik_ayarlari_ortamdan_okunur() -> None:
    ayarlar = guvenlik_ayarlari_ortamdan(
        ortam()
    )

    assert (
        ayarlar.samsung_tablet_anahtari
        == "TABLET-ANAHTARI"
    )


def test_eksik_ortam_degeri_reddedilir() -> None:
    eksik = ortam()
    eksik.pop(
        "SYK_IPHONE_ANAHTARI"
    )

    with pytest.raises(
        PrototipBaslaticiHatasi,
        match="SYK_IPHONE_ANAHTARI",
    ):
        guvenlik_ayarlari_ortamdan(
            eksik
        )


def test_baslatma_ayarlari_olusturulur(
    tmp_path: Path,
) -> None:
    guvenlik = (
        guvenlik_ayarlari_ortamdan(
            ortam()
        )
    )

    ayarlar = prototip_ayarlari_olustur(
        guvenlik=guvenlik,
        secenekler=(
            PrototipBaslatmaSecenekleri(
                durum_dosyasi=str(
                    tmp_path
                    / "durum.json"
                )
            )
        ),
    )

    assert ayarlar.canli_sunucu
    assert (
        ayarlar
        .terminal
        .durum_dosyasi
        == str(tmp_path / "durum.json")
    )


def test_baslatici_prototipi_hazirlar(
    tmp_path: Path,
) -> None:
    guvenlik = (
        guvenlik_ayarlari_ortamdan(
            ortam()
        )
    )

    baslatici = PrototipBaslaticisi(
        ayarlar=prototip_ayarlari_olustur(
            guvenlik=guvenlik,
            secenekler=(
                PrototipBaslatmaSecenekleri(
                    durum_dosyasi=str(
                        tmp_path
                        / "durum.json"
                    )
                )
            ),
        )
    )

    prototip = baslatici.hazirla()

    assert prototip.durum.value == "hazır"


def test_dogrulama_gercek_islemi_kapali_bildirir(
    tmp_path: Path,
) -> None:
    guvenlik = (
        guvenlik_ayarlari_ortamdan(
            ortam()
        )
    )

    baslatici = PrototipBaslaticisi(
        ayarlar=prototip_ayarlari_olustur(
            guvenlik=guvenlik,
            secenekler=(
                PrototipBaslatmaSecenekleri(
                    durum_dosyasi=str(
                        tmp_path
                        / "durum.json"
                    )
                )
            ),
        )
    )

    sonuc = baslatici.dogrula()

    assert sonuc["başarılı"] is True
    assert sonuc["gerçek_işlem"] is False


def test_dogrulama_durum_dosyasi_yazar(
    tmp_path: Path,
) -> None:
    durum_dosyasi = (
        tmp_path
        / "durum.json"
    )

    guvenlik = (
        guvenlik_ayarlari_ortamdan(
            ortam()
        )
    )

    baslatici = PrototipBaslaticisi(
        ayarlar=prototip_ayarlari_olustur(
            guvenlik=guvenlik,
            secenekler=(
                PrototipBaslatmaSecenekleri(
                    durum_dosyasi=str(
                        durum_dosyasi
                    )
                )
            ),
        )
    )

    baslatici.dogrula()

    veri = json.loads(
        durum_dosyasi.read_text(
            encoding="utf-8"
        )
    )

    assert veri["olay"] == "doğrulandı"


def test_main_dogrulama_komutu_calisir(
    tmp_path: Path,
) -> None:
    cikis = main(
        [
            "dogrula",
            "--durum-dosyasi",
            str(tmp_path / "durum.json"),
        ],
        ortam=ortam(),
    )

    assert cikis == 0


def test_canli_baslatma_ve_guvenli_kapatma(
    tmp_path: Path,
) -> None:
    guvenlik = (
        guvenlik_ayarlari_ortamdan(
            ortam()
        )
    )

    baslatici = PrototipBaslaticisi(
        ayarlar=prototip_ayarlari_olustur(
            guvenlik=guvenlik,
            secenekler=(
                PrototipBaslatmaSecenekleri(
                    durum_dosyasi=str(
                        tmp_path
                        / "durum.json"
                    )
                )
            ),
        )
    )

    adres = baslatici.baslat()

    try:
        assert adres.startswith(
            "http://127.0.0.1:"
        )
        assert baslatici.calisiyor_mu
    finally:
        baslatici.durdur()

    assert not baslatici.calisiyor_mu

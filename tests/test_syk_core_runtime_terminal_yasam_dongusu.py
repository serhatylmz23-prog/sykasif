from __future__ import annotations

import json
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from syk_core.runtime_terminal import (
    CalismaKipi,
    SyKasifTerminalUygulamasi,
    TerminalUygulamasiAyarlari,
    YetkiliCihazAyari,
)


class ElleSaat:
    def __init__(
        self,
        simdi: datetime,
    ) -> None:
        self.simdi = simdi

    def oku(self) -> datetime:
        return self.simdi


def ayarlar_olustur(
    gecici_dizin: Path,
) -> TerminalUygulamasiAyarlari:
    return TerminalUygulamasiAyarlari(
        calisma_kipi=(
            CalismaKipi.LABORATUVAR
        ),
        ana_makine="127.0.0.1",
        baglanti_noktasi=8214,
        panel_yolu="/terminal",
        panel_veri_yolu="/terminal/veri",
        ana_makine_cihaz_kimligi=(
            "ANA-MASAUSTU"
        ),
        sykasif_uygulama_kimligi=(
            "SYKASIF"
        ),
        sykasif_calistirma_yolu=str(
            gecici_dizin
        ),
        durum_dosyasi=str(
            gecici_dizin
            / "yasam_dongusu_durumu.json"
        ),
        yetkili_cihazlar=(
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "ANA-MASAUSTU"
                ),
                ad="SyKaşif Ana Makine",
                cihaz_turu="masaüstü",
                yetki_seviyesi=(
                    "Kurucu Kaan"
                ),
                cihaz_parmak_izi=(
                    "MASAUSTU-IZI"
                ),
                baslangicta_bagli=True,
            ),
            YetkiliCihazAyari(
                cihaz_kimligi=(
                    "SAMSUNG-TABLET"
                ),
                ad=(
                    "Samsung Ana Saha Terminali"
                ),
                cihaz_turu="tablet",
                yetki_seviyesi=(
                    "Bilge Kaan"
                ),
                cihaz_parmak_izi=(
                    "TABLET-IZI"
                ),
                baslangicta_bagli=False,
            ),
        ),
    )


def sistem_olustur(
    tmp_path: Path,
) -> tuple[
    ElleSaat,
    SyKasifTerminalUygulamasi,
]:
    saat = ElleSaat(
        datetime(
            2026,
            8,
            5,
            1,
            30,
            tzinfo=UTC,
        )
    )

    sistem = SyKasifTerminalUygulamasi(
        ayarlar=ayarlar_olustur(
            tmp_path
        ),
        saat=saat.oku,
    )

    return saat, sistem


def durum_dosyasini_oku(
    sistem: SyKasifTerminalUygulamasi,
) -> dict[str, Any]:
    yol = (
        sistem.ayarlar
        .durum_dosyasi_yolu()
    )

    return json.loads(
        yol.read_text(
            encoding="utf-8"
        )
    )


def test_uygulama_olusturulurken_on_event_uyarisi_yok(
    tmp_path: Path,
) -> None:
    with warnings.catch_warnings(
        record=True
    ) as yakalananlar:
        warnings.simplefilter(
            "always"
        )

        _, sistem = sistem_olustur(
            tmp_path
        )

        assert sistem.uygulama is not None

    on_event_uyarilari = [
        uyari
        for uyari in yakalananlar
        if (
            "on_event is deprecated"
            in str(uyari.message)
        )
    ]

    assert on_event_uyarilari == []


def test_lifespan_context_kaydedilir(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    yasam_dongusu = (
        sistem.uygulama.router
        .lifespan_context
    )

    assert callable(
        yasam_dongusu
    )

    assert (
        getattr(
            yasam_dongusu,
            "__name__",
            "",
        )
        == "terminal_yasam_dongusu"
    )


def test_testclient_yasam_dongusunu_baslatir(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.get(
            "/saglik"
        )

        assert yanit.status_code == 200
        assert yanit.json()[
            "durum"
        ] == "sağlıklı"


def test_baslangicta_durum_kaydi_yazilir(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    yol = (
        sistem.ayarlar
        .durum_dosyasi_yolu()
    )

    if yol.exists():
        yol.unlink()

    assert not yol.exists()

    with TestClient(
        sistem.uygulama
    ):
        assert yol.exists()

        veri = durum_dosyasini_oku(
            sistem
        )

        assert veri[
            "sistem"
        ] == "SyKaşif"

        assert veri[
            "durum"
        ] == "hazır"


def test_kapanista_etkin_oturum_sonlandirilir(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.post(
            "/oturumlar/ac",
            json={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "TABLET-IZI"
                ),
            },
        )

        assert yanit.status_code == 201

        oturumlar = (
            sistem.oturum_yoneticisi
            .oturumlari_listele()
        )

        assert len(
            oturumlar
        ) == 1

        assert not (
            oturumlar[0]
            .sona_erdi_mi
        )

    oturumlar = (
        sistem.oturum_yoneticisi
        .oturumlari_listele()
    )

    assert len(
        oturumlar
    ) == 1

    assert (
        oturumlar[0]
        .sona_erdi_mi
    )


def test_kapanista_cihaz_araci_durdurulur(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.get(
            "/terminal"
        )

        assert yanit.status_code == 200

        assert (
            sistem.cihaz_araci
            .durum.value
            == "hazır"
        )

    assert (
        sistem.cihaz_araci
        .durum.value
        == "durduruldu"
    )


def test_kapanis_durum_kaydi_gunceller(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.post(
            "/oturumlar/ac",
            json={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "TABLET-IZI"
                ),
            },
        )

        assert yanit.status_code == 201

    veri = durum_dosyasini_oku(
        sistem
    )

    assert veri[
        "cihaz_aracı"
    ][
        "araç_durumu"
    ] == "durduruldu"

    assert veri[
        "oturumlar"
    ][
        "sona_eren_oturum_sayısı"
    ] == 1


def test_guvenli_durdurma_tekrar_cagrilabilir(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    sistem.guvenli_durdur()
    sistem.guvenli_durdur()

    assert (
        sistem.cihaz_araci
        .durum.value
        == "durduruldu"
    )


def test_lifespan_kapanisi_iki_kez_cagrilmaz(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.get(
            "/saglik"
        )

        assert yanit.status_code == 200

    ilk_durdurma_zamani = (
        sistem.cihaz_araci
        .durdurma_zamani
    )

    sistem.guvenli_durdur()

    assert (
        sistem.cihaz_araci
        .durdurma_zamani
        == ilk_durdurma_zamani
    )


def test_lifespan_paneli_canli_tutar(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        panel = istemci.get(
            "/terminal"
        )

        veri = istemci.get(
            "/terminal/veri"
        )

        assert panel.status_code == 200
        assert veri.status_code == 200

        assert (
            "SyKaşif Terminali"
            in panel.text
        )

        assert veri.json()[
            "panel"
        ][
            "toplam_cihaz_sayısı"
        ] == 2


def test_lifespan_ag_gecidini_canli_tutar(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        ana_sayfa = istemci.get(
            "/"
        )

        saglik = istemci.get(
            "/saglik"
        )

        aciklama = istemci.get(
            "/aciklama.json"
        )

        assert (
            ana_sayfa.status_code
            == 200
        )

        assert (
            saglik.status_code
            == 200
        )

        assert (
            aciklama.status_code
            == 200
        )


def test_lifespan_tablet_oturumu_acar(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.post(
            "/oturumlar/ac",
            json={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "TABLET-IZI"
                ),
            },
        )

        assert yanit.status_code == 201

        assert yanit.json()[
            "oturum"
        ][
            "durum"
        ] == "bağlı"

        assert (
            sistem.terminal
            .cihaz_getir(
                "SAMSUNG-TABLET"
            )
            .bagli_mi
        )


def test_lifespan_sonrasi_tablet_cevrimdisi(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ) as istemci:
        yanit = istemci.post(
            "/oturumlar/ac",
            json={
                "cihaz_kimliği": (
                    "SAMSUNG-TABLET"
                ),
                "cihaz_parmak_izi": (
                    "TABLET-IZI"
                ),
            },
        )

        assert yanit.status_code == 201

    cihaz = (
        sistem.terminal
        .cihaz_getir(
            "SAMSUNG-TABLET"
        )
    )

    assert not cihaz.bagli_mi

    assert cihaz.durum.value == (
        "çevrimdışı"
    )


def test_lifespan_durum_dosyasi_turkce_anahtarlar_tasir(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ):
        pass

    veri = durum_dosyasini_oku(
        sistem
    )

    assert "çalışma_kipi" in veri
    assert "ağ_geçidi" in veri
    assert "cihaz_aracı" in veri
    assert "oturumlar" in veri
    assert "panel" in veri


def test_lifespan_durum_dosyasi_gecerli_json(
    tmp_path: Path,
) -> None:
    _, sistem = sistem_olustur(
        tmp_path
    )

    with TestClient(
        sistem.uygulama
    ):
        pass

    yol = (
        sistem.ayarlar
        .durum_dosyasi_yolu()
    )

    ham = yol.read_text(
        encoding="utf-8"
    )

    veri = json.loads(
        ham
    )

    assert isinstance(
        veri,
        dict,
    )

    assert ham.endswith(
        "\n"
    )

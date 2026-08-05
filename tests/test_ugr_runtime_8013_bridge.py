from __future__ import annotations

import json
from pathlib import Path
from threading import Event

import pytest

from syk_ui.icons.ugr.integration import (
    UgrCanliIkonOlayi,
    UgrCanliOlayTuru,
    UgrRuntime8013Bridge,
    UgrRuntime8013EventStream,
)
from syk_ui.icons.ugr.integration.runtime_8013_http_api import (
    UgrRuntime8013HttpApi,
)
from syk_ui.icons.ugr.integration.runtime_8013_store import (
    UgrRuntime8013EventStore,
)
from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
)


MANIFEST = Path(
    "src/syk_ui/icons/ugr/manifests/"
    "ugr_prototype_icons_manifest.json"
)


def bridge_uret() -> UgrRuntime8013Bridge:
    if not MANIFEST.exists():
        pytest.skip(
            "Gerçek 215 ikon manifesti bulunamadı."
        )

    bridge = UgrRuntime8013Bridge()
    ozet = bridge.baslat(MANIFEST)

    assert (
        ozet["ikon_runtime"]["toplam_ikon"]
        == 215
    )

    return bridge


def test_event_store_olay_ekler() -> None:
    store = UgrRuntime8013EventStore(
        kapasite=10
    )

    olay = UgrCanliIkonOlayi(
        olay_turu=(
            UgrCanliOlayTuru.BAGLANTI
        ),
        veri={"durum": "acik"},
    )

    sira = store.ekle(olay)

    assert sira == 1
    assert store.son(1) == (olay,)


def test_event_store_kapasiteyi_asmaz() -> None:
    store = UgrRuntime8013EventStore(
        kapasite=2
    )

    for indeks in range(3):
        store.ekle(
            UgrCanliIkonOlayi(
                olay_turu=(
                    UgrCanliOlayTuru
                    .KALP_ATISI
                ),
                veri={"indeks": indeks},
            )
        )

    assert len(store.tumu()) == 2


def test_sse_verisi_gecerli_bicimde_uretilir() -> None:
    store = UgrRuntime8013EventStore()

    olay = UgrCanliIkonOlayi(
        olay_turu=(
            UgrCanliOlayTuru.IKON_DURUMU
        ),
        ikon_kimligi="sys-001",
        veri={
            "ikon_kimligi": "sys-001",
            "durum": "calisiyor",
        },
    )

    store.ekle(olay)

    stream = UgrRuntime8013EventStream(
        store
    )

    metin = (
        stream
        .tek_seferlik_akisi_uret(
            (olay,)
        )
    )

    assert (
        "event: ikon_durumu"
        in metin
    )
    assert (
        '"ikon_kimligi":"sys-001"'
        in metin
    )
    assert metin.endswith("\n\n")


def test_bridge_215_ikonu_yukler() -> None:
    bridge = bridge_uret()

    ozet = bridge.durum_ozeti()

    assert ozet["baslatildi"] is True
    assert ozet["runtime_portu"] == 8013
    assert (
        ozet["ikon_runtime"]["toplam_ikon"]
        == 215
    )


def test_bridge_iki_kez_baslatilabilir() -> None:
    bridge = bridge_uret()

    ikinci = bridge.baslat(MANIFEST)

    assert ikinci["baslatildi"] is True
    assert (
        ikinci["ikon_runtime"]["toplam_ikon"]
        == 215
    )


def test_bridge_durum_degisimini_canli_yayinlar() -> None:
    bridge = bridge_uret()

    sonuc = bridge.ikon_durumu_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu
            .BASLATILIYOR
        ),
        neden="Canlı test.",
    )

    assert (
        sonuc["ikon"]["durum"]
        == "baslatiliyor"
    )

    assert (
        sonuc["canli_olay"]["olay_turu"]
        == "ikon_durumu"
    )

    assert (
        sonuc["canli_olay"]["veri"][
            "animasyon"
        ]
        == "donus"
    )


def test_bridge_gorunum_degisimini_yayinlar() -> None:
    bridge = bridge_uret()

    sonuc = bridge.ikon_gorunumu_degistir(
        "sys-001",
        IkonGorunumModu.MOD_AR,
    )

    assert (
        sonuc["gorunum_modu"]
        == "ar"
    )

    assert (
        sonuc["canli_olay"]["olay_turu"]
        == "ikon_gorunumu"
    )


def test_bridge_aktiflik_degisimini_yayinlar() -> None:
    bridge = bridge_uret()

    sonuc = bridge.ikon_aktifligi_degistir(
        "sys-001",
        aktif=False,
    )

    assert sonuc["aktif"] is False

    assert (
        sonuc["canli_olay"]["olay_turu"]
        == "ikon_aktifligi"
    )


def test_bridge_snapshot_215_ikon_tasir() -> None:
    bridge = bridge_uret()

    snapshot = bridge.snapshot()

    assert (
        snapshot["olay_turu"]
        == "snapshot"
    )

    assert (
        snapshot["veri"]["toplam_ikon"]
        == 215
    )

    assert len(
        snapshot["veri"]["ikonlar"]
    ) == 215


def test_bridge_toplu_durum_degistirir() -> None:
    bridge = bridge_uret()

    sonuc = bridge.toplu_durum_degistir(
        [
            "sys-001",
            "sys-002",
            "sys-003",
        ],
        yeni_durum=(
            IkonCalismaDurumu.UYARI
        ),
        neden="Toplu uyarı testi.",
        zorla=True,
    )

    assert (
        sonuc["olay_turu"]
        == "toplu_guncelleme"
    )

    assert (
        sonuc["veri"][
            "basarili_ikon_sayisi"
        ]
        == 3
    )

    assert (
        sonuc["veri"][
            "basarisiz_ikon_sayisi"
        ]
        == 0
    )


def test_http_api_saglik_yaniti_200() -> None:
    bridge = bridge_uret()
    api = UgrRuntime8013HttpApi(
        bridge
    )

    yanit = api.saglik()

    assert yanit.durum_kodu == 200
    assert (
        yanit.govde["runtime_portu"]
        == 8013
    )


def test_http_api_snapshot_yaniti() -> None:
    bridge = bridge_uret()
    api = UgrRuntime8013HttpApi(
        bridge
    )

    yanit = api.snapshot()

    assert yanit.durum_kodu == 200
    assert (
        yanit.govde["veri"][
            "toplam_ikon"
        ]
        == 215
    )


def test_http_api_ikon_durumu_degistirir() -> None:
    bridge = bridge_uret()
    api = UgrRuntime8013HttpApi(
        bridge
    )

    yanit = api.ikon_durumu(
        "sys-001",
        durum="hata",
        neden="HTTP test hatası.",
        zorla=True,
    )

    assert yanit.durum_kodu == 200
    assert (
        yanit.govde["ikon"]["durum"]
        == "hata"
    )


def test_http_api_ar_gorunumu_uygular() -> None:
    bridge = bridge_uret()
    api = UgrRuntime8013HttpApi(
        bridge
    )

    yanit = api.ikon_gorunumu(
        "sys-001",
        gorunum_modu="ar",
    )

    assert (
        yanit.govde["gorunum_modu"]
        == "ar"
    )


def test_http_api_sse_basliklari() -> None:
    bridge = bridge_uret()
    api = UgrRuntime8013HttpApi(
        bridge
    )

    bridge.ikon_durumu_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu
            .BASLATILIYOR
        ),
        neden="SSE testi.",
    )

    yanit = api.sse_gecmisi(
        adet=5
    )

    assert yanit.durum_kodu == 200
    assert (
        yanit.icerik_turu
        == "text/event-stream; charset=utf-8"
    )
    assert (
        yanit.basliklar[
            "Cache-Control"
        ]
        == "no-cache"
    )
    assert "event:" in yanit.govde


def test_event_json_serilestirilebilir() -> None:
    olay = UgrCanliIkonOlayi(
        olay_turu=(
            UgrCanliOlayTuru
            .IKON_DURUMU
        ),
        ikon_kimligi="sys-001",
        veri={"durum": "calisiyor"},
    )

    metin = json.dumps(
        olay.json_verisi(),
        ensure_ascii=False,
    )

    assert "sys-001" in metin


def test_kalp_atisi_akisi_uretilir() -> None:
    store = UgrRuntime8013EventStore()

    stream = UgrRuntime8013EventStream(
        store,
        kalp_atisi_suresi=0.01,
    )

    durdurma = Event()

    iterator = stream.akisi_uret(
        durdurma_olayi=durdurma
    )

    metin = next(iterator)
    durdurma.set()

    assert (
        "event: kalp_atisi"
        in metin
    )


def test_runtime_manifesti_gecerli() -> None:
    yol = Path(
        "src/syk_ui/icons/ugr/integration/"
        "runtime_8013_bridge_manifest.json"
    )

    veri = json.loads(
        yol.read_text(
            encoding="utf-8-sig"
        )
    )

    assert veri["runtime_portu"] == 8013
    assert (
        veri["desteklenen_ikon_sayisi"]
        == 215
    )

    assert (
        set(
            veri["canli_kanallar"]
        )
        == {
            "http_json",
            "snapshot",
            "sse",
        }
    )

from __future__ import annotations

import json
from pathlib import Path

import pytest

from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
    IkonRuntimeKaydi,
    UgrDinamikIkonServisi,
)
from syk_ui.icons.ugr.web import (
    IkonWebRenderKaydi,
    IkonWebStili,
    UgrIkonWebRenderServisi,
)


def servis_uret() -> UgrDinamikIkonServisi:
    servis = UgrDinamikIkonServisi()

    servis.ikon_ekle(
        IkonRuntimeKaydi(
            ikon_kimligi="sys-001",
            kategori="ana_sistem",
            etiket="harita",
            dosya_yolu=(
                "src/syk_ui/icons/ugr/"
                "prototype_icons/ana_sistem/"
                "001_harita.png"
            ),
        )
    )

    return servis


def test_web_stili_css_degiskenleri_uretir() -> None:
    stil = IkonWebStili(
        durum="calisiyor",
        animasyon="nabiz",
        renk_rolu="islem",
        animasyon_suresi_ms=1800,
        tekrarli=True,
        parlaklik=1.05,
        saydamlik=1.0,
        olcek=1.02,
    )

    degiskenler = stil.css_degiskenleri()

    assert (
        degiskenler[
            "--syk-icon-duration"
        ]
        == "1800ms"
    )
    assert (
        degiskenler[
            "--syk-icon-iteration"
        ]
        == "infinite"
    )


def test_web_render_kaydi_css_siniflari_uretir() -> None:
    kayit = IkonWebRenderKaydi(
        ikon_kimligi="sys-001",
        kategori="ana_sistem",
        etiket="harita",
        dosya_yolu="/harita.png",
        durum="calisiyor",
        gorunum_modu="2b",
        aktif=True,
        stil=IkonWebStili(
            durum="calisiyor",
            animasyon="nabiz",
            renk_rolu="islem",
            animasyon_suresi_ms=1800,
            tekrarli=True,
            parlaklik=1.05,
            saydamlik=1.0,
            olcek=1.02,
        ),
    )

    siniflar = kayit.css_siniflari()

    assert "syk-ugr-icon" in siniflar
    assert (
        "syk-ugr-state-calisiyor"
        in siniflar
    )
    assert (
        "syk-ugr-view-2b"
        in siniflar
    )


def test_web_render_html_guvenli_nitelikler_uretir() -> None:
    servis = servis_uret()

    render = UgrIkonWebRenderServisi(
        servis
    )

    html = render.html_uret(
        "sys-001"
    )

    assert (
        'data-syk-icon-id="sys-001"'
        in html
    )
    assert (
        'data-syk-state="bekliyor"'
        in html
    )
    assert (
        'data-syk-view="2b"'
        in html
    )
    assert (
        'class="syk-ugr-icon '
        in html
    )


def test_yerel_ikon_yolu_web_yoluna_donusur() -> None:
    servis = servis_uret()

    render = UgrIkonWebRenderServisi(
        servis
    )

    veri = render.json_uret(
        "sys-001"
    )

    assert veri["dosya_yolu"] == (
        "/static/icons/ugr/"
        "prototype_icons/"
        "ana_sistem/"
        "001_harita.png"
    )


def test_runtime_durumu_web_stiline_yansir() -> None:
    servis = servis_uret()

    servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.BASLATILIYOR
        ),
        neden="Başlatılıyor.",
    )

    servis.durum_degistir(
        "sys-001",
        yeni_durum=(
            IkonCalismaDurumu.CALISIYOR
        ),
        neden="Çalışıyor.",
    )

    render = UgrIkonWebRenderServisi(
        servis
    )

    veri = render.json_uret(
        "sys-001"
    )

    assert veri["durum"] == "calisiyor"
    assert (
        veri["stil"]["animasyon"]
        == "nabiz"
    )
    assert (
        veri["stil"]["renk_rolu"]
        == "islem"
    )


@pytest.mark.parametrize(
    ("durum", "animasyon"),
    [
        (
            IkonCalismaDurumu.BEKLIYOR,
            "nefes",
        ),
        (
            IkonCalismaDurumu.TARIYOR,
            "tarama",
        ),
        (
            IkonCalismaDurumu.HATA,
            "titresim",
        ),
        (
            IkonCalismaDurumu.TAMAMLANDI,
            "parlama",
        ),
        (
            IkonCalismaDurumu.CEVRIMDISI,
            "sabit",
        ),
    ],
)
def test_durum_animasyon_eslesmeleri(
    durum: IkonCalismaDurumu,
    animasyon: str,
) -> None:
    servis = servis_uret()

    servis.durum_degistir(
        "sys-001",
        yeni_durum=durum,
        neden="Test.",
        zorla=True,
    )

    render = UgrIkonWebRenderServisi(
        servis
    )

    veri = render.json_uret(
        "sys-001"
    )

    assert (
        veri["stil"]["animasyon"]
        == animasyon
    )


@pytest.mark.parametrize(
    "gorunum",
    [
        IkonGorunumModu.MOD_2B,
        IkonGorunumModu.MOD_3B,
        IkonGorunumModu.MOD_AR,
    ],
)
def test_gorunum_modu_css_sinifina_yansir(
    gorunum: IkonGorunumModu,
) -> None:
    servis = servis_uret()

    servis.gorunum_modu_degistir(
        "sys-001",
        gorunum,
    )

    render = UgrIkonWebRenderServisi(
        servis
    )

    veri = render.json_uret(
        "sys-001"
    )

    assert (
        f"syk-ugr-view-{gorunum.value}"
        in veri["css_siniflari"]
    )


def test_kategori_grid_html_uretilir() -> None:
    servis = servis_uret()

    render = UgrIkonWebRenderServisi(
        servis
    )

    html = render.kategori_html_uret(
        "ana_sistem"
    )

    assert (
        "syk-ugr-icon-library"
        in html
    )
    assert (
        "syk-ugr-icon-grid"
        in html
    )
    assert "1 ikon" in html


def test_css_dosyasi_gerekli_animasyonlari_tasir() -> None:
    css = Path(
        "src/syk_ui/icons/ugr/web/"
        "static/css/"
        "ugr_dynamic_icons.css"
    ).read_text(
        encoding="utf-8-sig"
    )

    zorunlu = {
        "@keyframes syk-ugr-breathe",
        "@keyframes syk-ugr-rotate",
        "@keyframes syk-ugr-scan",
        "@keyframes syk-ugr-data-flow",
        "@keyframes syk-ugr-pulse",
        "@keyframes syk-ugr-shake",
        "@keyframes syk-ugr-glow",
        "@keyframes syk-ugr-fade",
        ".syk-ugr-view-2b",
        ".syk-ugr-view-3b",
        ".syk-ugr-view-ar",
    }

    for ifade in zorunlu:
        assert ifade in css


def test_javascript_runtime_api_tasir() -> None:
    javascript = Path(
        "src/syk_ui/icons/ugr/web/"
        "static/js/"
        "ugr_dynamic_icons.js"
    ).read_text(
        encoding="utf-8-sig"
    )

    zorunlu = {
        "class UgrDynamicIconRuntime",
        "setState(",
        "setView(",
        "setActive(",
        "updateFromPayload(",
        "connectEventSource(",
        "syk:ugr:runtime-ready",
        "syk:ugr:icon-state-changed",
        "syk:ugr:icon-view-changed",
    }

    for ifade in zorunlu:
        assert ifade in javascript


def test_web_manifesti_gecerli_json() -> None:
    yol = Path(
        "src/syk_ui/icons/ugr/web/"
        "ugr_dynamic_icon_web_manifest.json"
    )

    veri = json.loads(
        yol.read_text(
            encoding="utf-8-sig"
        )
    )

    assert (
        veri["desteklenen_ikon_sayisi"]
        == 215
    )
    assert (
        set(
            veri[
                "desteklenen_gorunumler"
            ]
        )
        == {"2b", "3b", "ar"}
    )


def test_gercek_manifestten_demo_uretilebilir(
    tmp_path: Path,
) -> None:
    manifest = Path(
        "src/syk_ui/icons/ugr/manifests/"
        "ugr_prototype_icons_manifest.json"
    )

    if not manifest.exists():
        pytest.skip(
            "Gerçek UGR ikon manifesti bulunamadı."
        )

    servis = UgrDinamikIkonServisi()

    yuklenen = servis.manifest_yukle(
        manifest
    )

    assert yuklenen == 215

    render = UgrIkonWebRenderServisi(
        servis
    )

    kayitlar = (
        servis.kayit_defteri.tumu()[:10]
    )

    html = render.grid_html_uret(
        kayitlar,
        baslik="UGR Test",
    )

    cikti = tmp_path / "demo.html"

    cikti.write_text(
        html,
        encoding="utf-8",
    )

    assert cikti.exists()
    assert html.count(
        'data-syk-icon-id="'
    ) == 10

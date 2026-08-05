"""SyKaşif UGR canlı ikon Runtime 8013 FastAPI rotaları.

Bu modül:

- 215 UGR ikonunu yükler.
- Sağlık durumunu sunar.
- İkon snapshot çıktısını verir.
- Tek ikon bilgisini döndürür.
- İkon durumunu canlı değiştirir.
- 2B, 3B ve AR görünümünü değiştirir.
- İkonu aktif veya pasif yapar.
- Son olayları JSON olarak verir.
- Server-Sent Events canlı kanalını açar.
- UGR ikon, CSS ve JavaScript dosyalarını güvenli biçimde sunar.

Kalıcı ikon kimlikleri prototip sonrasında atanacaktır.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    StreamingResponse,
)

from syk_ui.icons.ugr.integration.runtime_8013_bridge import (
    UgrRuntime8013Bridge,
)
from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
    IkonOnceligi,
)


ugr_router = APIRouter(
    prefix="/api/ugr",
    tags=["SyKaşif UGR"],
)


_REPO_ROOT = Path(__file__).resolve().parents[3]

_UGR_MANIFEST = (
    _REPO_ROOT
    / "src"
    / "syk_ui"
    / "icons"
    / "ugr"
    / "manifests"
    / "ugr_prototype_icons_manifest.json"
)

_UGR_STATIC_ROOT = (
    _REPO_ROOT
    / "src"
    / "syk_ui"
    / "icons"
    / "ugr"
)

_UGR_WEB_ROOT = (
    _UGR_STATIC_ROOT
    / "web"
)

_UGR_CSS = (
    _UGR_WEB_ROOT
    / "static"
    / "css"
    / "ugr_dynamic_icons.css"
)

_UGR_JAVASCRIPT = (
    _UGR_WEB_ROOT
    / "static"
    / "js"
    / "ugr_dynamic_icons.js"
)

_UGR_PREVIEW = (
    _UGR_WEB_ROOT
    / "demo"
    / "ugr_dynamic_icons_preview.html"
)


_bridge = UgrRuntime8013Bridge()


def _bridge_baslat() -> UgrRuntime8013Bridge:
    """UGR köprüsünün yalnızca bir kez başlatılmasını sağlar."""

    if not _bridge.baslatildi:
        if not _UGR_MANIFEST.exists():
            raise RuntimeError(
                "UGR prototip ikon manifesti bulunamadı: "
                f"{_UGR_MANIFEST}"
            )

        _bridge.baslat(
            _UGR_MANIFEST
        )

    return _bridge


def _json_hatasi(
    hata: Exception,
    *,
    durum_kodu: int = 400,
) -> HTTPException:
    """Tutarlı HTTP hata yanıtı üretir."""

    return HTTPException(
        status_code=durum_kodu,
        detail={
            "durum": "hata",
            "hata_turu": type(hata).__name__,
            "aciklama": str(hata),
        },
    )


def _guvenli_statik_yol(
    goreli_yol: str,
) -> Path:
    """Dizin dışına çıkışı engelleyerek statik yolu çözümler."""

    temiz_yol = goreli_yol.replace(
        "\\",
        "/",
    ).lstrip("/")

    aday = (
        _UGR_STATIC_ROOT
        / temiz_yol
    ).resolve()

    kok = _UGR_STATIC_ROOT.resolve()

    try:
        aday.relative_to(kok)
    except ValueError as hata:
        raise HTTPException(
            status_code=403,
            detail={
                "durum": "reddedildi",
                "aciklama": (
                    "UGR statik dizini dışına çıkılamaz."
                ),
            },
        ) from hata

    if not aday.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "durum": "bulunamadi",
                "dosya": temiz_yol,
            },
        )

    if not aday.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "durum": "dosya_degil",
                "dosya": temiz_yol,
            },
        )

    return aday


def _oncelik(
    deger: str | None,
) -> IkonOnceligi:
    """Metin önceliğini enum değerine dönüştürür."""

    if deger is None:
        return IkonOnceligi.NORMAL

    try:
        return IkonOnceligi(
            deger
        )
    except ValueError as hata:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "gecersiz_oncelik",
                "gecerli_degerler": [
                    oncelik.value
                    for oncelik in IkonOnceligi
                ],
            },
        ) from hata


@ugr_router.get(
    "/health",
    summary="UGR canlı ikon sağlık durumu",
)
def ugr_saglik() -> JSONResponse:
    """UGR Runtime 8013 sağlık özetini döndürür."""

    try:
        bridge = _bridge_baslat()
        ozet = bridge.durum_ozeti()

        return JSONResponse(
            status_code=200,
            content={
                "durum": "saglikli",
                "servis": "SyKaşif UGR Runtime",
                "runtime_portu": 8013,
                "toplam_ikon": (
                    ozet[
                        "ikon_runtime"
                    ][
                        "toplam_ikon"
                    ]
                ),
                "desteklenen_durum_sayisi": 13,
                "desteklenen_gorunumler": [
                    "2b",
                    "3b",
                    "ar",
                ],
                "canli_kanallar": (
                    ozet["canli_kanallar"]
                ),
                "kalici_ikon_kimlikleri": (
                    "prototip_sonrasina_ertelendi"
                ),
                "ayrintilar": ozet,
            },
            headers={
                "Cache-Control": "no-store",
            },
        )

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=503,
        ) from hata


@ugr_router.get(
    "/snapshot",
    summary="215 UGR ikonunun canlı snapshot çıktısı",
)
def ugr_snapshot() -> JSONResponse:
    """Bütün UGR ikonlarının anlık durumunu döndürür."""

    try:
        bridge = _bridge_baslat()
        sonuc = bridge.snapshot()

        return JSONResponse(
            status_code=200,
            content=sonuc,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=500,
        ) from hata


@ugr_router.get(
    "/icons",
    summary="UGR ikonlarını listeler",
)
def ugr_ikonlari(
    kategori: str | None = Query(
        default=None,
    ),
    durum: str | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=215,
        ge=1,
        le=215,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> JSONResponse:
    """UGR ikonlarını kategori ve duruma göre listeler."""

    try:
        bridge = _bridge_baslat()

        kayitlar = list(
            bridge
            .ikon_servisi
            .kayit_defteri
            .tumu()
        )

        if kategori:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if kayit.kategori == kategori
            ]

        if durum:
            kayitlar = [
                kayit
                for kayit in kayitlar
                if kayit.durum.value == durum
            ]

        toplam = len(
            kayitlar
        )

        secilen = kayitlar[
            offset:
            offset + limit
        ]

        ikonlar = [
            bridge.ikon_render_verisi(
                kayit.ikon_kimligi
            )
            for kayit in secilen
        ]

        return JSONResponse(
            status_code=200,
            content={
                "toplam_ikon": toplam,
                "offset": offset,
                "limit": limit,
                "ikonlar": ikonlar,
            },
            headers={
                "Cache-Control": "no-store",
            },
        )

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=500,
        ) from hata


@ugr_router.get(
    "/icons/{ikon_kimligi}",
    summary="Tek UGR ikonunun canlı durumunu verir",
)
def ugr_ikon(
    ikon_kimligi: str,
) -> JSONResponse:
    """Tek ikonun render ve durum bilgisini döndürür."""

    try:
        bridge = _bridge_baslat()

        sonuc = (
            bridge
            .ikon_render_verisi(
                ikon_kimligi
            )
        )

        return JSONResponse(
            status_code=200,
            content=sonuc,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except KeyError as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=404,
        ) from hata

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=500,
        ) from hata


@ugr_router.get(
    "/icons/{ikon_kimligi}/html",
    response_class=HTMLResponse,
    summary="Tek UGR ikonunun HTML bileşenini verir",
)
def ugr_ikon_html(
    ikon_kimligi: str,
) -> HTMLResponse:
    """Tek UGR ikonunu tarayıcı bileşeni olarak döndürür."""

    try:
        bridge = _bridge_baslat()

        html = bridge.ikon_html(
            ikon_kimligi
        )

        return HTMLResponse(
            status_code=200,
            content=html,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except KeyError as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=404,
        ) from hata

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=500,
        ) from hata


@ugr_router.post(
    "/icons/bulk/state",
    summary="Birden fazla UGR ikonunun durumunu değiştirir",
)
def ugr_toplu_ikon_durumu(
    veri: dict[str, Any] = Body(...),
) -> JSONResponse:
    """Seçilen ikonlara tek işlemle durum uygular."""

    ikon_kimlikleri = veri.get(
        "ikon_kimlikleri",
        [],
    )

    durum_degeri = str(
        veri.get(
            "durum",
            "",
        )
    ).strip()

    neden = str(
        veri.get(
            "neden",
            "Runtime 8013 toplu ikon güncellemesi.",
        )
    ).strip()

    if not isinstance(
        ikon_kimlikleri,
        list,
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "gecersiz_veri",
                "alan": "ikon_kimlikleri",
            },
        )

    if not ikon_kimlikleri:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "bos_liste",
                "alan": "ikon_kimlikleri",
            },
        )

    try:
        bridge = _bridge_baslat()

        sonuc = bridge.toplu_durum_degistir(
            [
                str(kimlik)
                for kimlik in ikon_kimlikleri
            ],
            yeni_durum=(
                IkonCalismaDurumu(
                    durum_degeri
                )
            ),
            neden=neden,
            zorla=bool(
                veri.get(
                    "zorla",
                    False,
                )
            ),
        )

        return JSONResponse(
            status_code=200,
            content=sonuc,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except ValueError as hata:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "gecersiz_ikon_durumu",
                "gelen_deger": durum_degeri,
                "gecerli_degerler": [
                    durum.value
                    for durum in IkonCalismaDurumu
                ],
            },
        ) from hata

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=400,
        ) from hata

@ugr_router.post(
    "/icons/{ikon_kimligi}/state",
    summary="UGR ikonunun canlı durumunu değiştirir",
)
def ugr_ikon_durumu_degistir(
    ikon_kimligi: str,
    veri: dict[str, Any] = Body(...),
) -> JSONResponse:
    """İkona çalışma durumu ve animasyon davranışı uygular."""

    durum_degeri = str(
        veri.get(
            "durum",
            "",
        )
    ).strip()

    neden = str(
        veri.get(
            "neden",
            "Runtime 8013 canlı durum güncellemesi.",
        )
    ).strip()

    zorla = bool(
        veri.get(
            "zorla",
            False,
        )
    )

    if not durum_degeri:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "eksik_veri",
                "alan": "durum",
            },
        )

    if not neden:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "eksik_veri",
                "alan": "neden",
            },
        )

    try:
        yeni_durum = IkonCalismaDurumu(
            durum_degeri
        )

        bridge = _bridge_baslat()

        sonuc = (
            bridge
            .ikon_durumu_degistir(
                ikon_kimligi,
                yeni_durum=yeni_durum,
                neden=neden,
                oncelik=_oncelik(
                    veri.get(
                        "oncelik"
                    )
                ),
                ek_veri=dict(
                    veri.get(
                        "ek_veri",
                        {},
                    )
                ),
                zorla=zorla,
            )
        )

        return JSONResponse(
            status_code=200,
            content=sonuc,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except ValueError as hata:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "gecersiz_ikon_durumu",
                "gelen_deger": durum_degeri,
                "gecerli_degerler": [
                    durum.value
                    for durum in IkonCalismaDurumu
                ],
            },
        ) from hata

    except KeyError as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=404,
        ) from hata

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=400,
        ) from hata


@ugr_router.post(
    "/icons/{ikon_kimligi}/view",
    summary="UGR ikonunun 2B, 3B veya AR görünümünü değiştirir",
)
def ugr_ikon_gorunumu_degistir(
    ikon_kimligi: str,
    veri: dict[str, Any] = Body(...),
) -> JSONResponse:
    """İkon görünüm modunu değiştirir."""

    gorunum_degeri = str(
        veri.get(
            "gorunum_modu",
            veri.get(
                "gorunum",
                "",
            ),
        )
    ).strip()

    if not gorunum_degeri:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "eksik_veri",
                "alan": "gorunum_modu",
            },
        )

    try:
        gorunum_modu = IkonGorunumModu(
            gorunum_degeri
        )

        bridge = _bridge_baslat()

        sonuc = (
            bridge
            .ikon_gorunumu_degistir(
                ikon_kimligi,
                gorunum_modu,
            )
        )

        return JSONResponse(
            status_code=200,
            content=sonuc,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except ValueError as hata:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "gecersiz_gorunum",
                "gelen_deger": gorunum_degeri,
                "gecerli_degerler": [
                    gorunum.value
                    for gorunum in IkonGorunumModu
                ],
            },
        ) from hata

    except KeyError as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=404,
        ) from hata

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=400,
        ) from hata


@ugr_router.post(
    "/icons/{ikon_kimligi}/active",
    summary="UGR ikonunu aktif veya pasif yapar",
)
def ugr_ikon_aktifligi_degistir(
    ikon_kimligi: str,
    veri: dict[str, Any] = Body(...),
) -> JSONResponse:
    """İkonun kullanıcı etkileşimi durumunu değiştirir."""

    if "aktif" not in veri:
        raise HTTPException(
            status_code=422,
            detail={
                "durum": "eksik_veri",
                "alan": "aktif",
            },
        )

    try:
        bridge = _bridge_baslat()

        sonuc = (
            bridge
            .ikon_aktifligi_degistir(
                ikon_kimligi,
                aktif=bool(
                    veri["aktif"]
                ),
            )
        )

        return JSONResponse(
            status_code=200,
            content=sonuc,
            headers={
                "Cache-Control": "no-store",
            },
        )

    except KeyError as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=404,
        ) from hata

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=400,
        ) from hata




@ugr_router.get(
    "/events/history",
    summary="Son UGR canlı ikon olaylarını verir",
)
def ugr_olay_gecmisi(
    adet: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
) -> JSONResponse:
    """Bellekte tutulan son ikon olaylarını döndürür."""

    try:
        bridge = _bridge_baslat()

        olaylar = [
            olay.json_verisi()
            for olay in (
                bridge
                .olay_deposu
                .son(adet)
            )
        ]

        return JSONResponse(
            status_code=200,
            content={
                "olay_sayisi": len(
                    olaylar
                ),
                "olaylar": olaylar,
            },
            headers={
                "Cache-Control": "no-store",
            },
        )

    except Exception as hata:
        raise _json_hatasi(
            hata,
            durum_kodu=500,
        ) from hata


async def _sse_akisi(
    request: Request,
    *,
    son_sira: int,
    kalp_atisi_suresi: float,
) -> AsyncIterator[str]:
    """İstemci bağlantısı kapanana kadar SSE olaylarını üretir."""

    bridge = _bridge_baslat()
    sira = max(
        0,
        son_sira,
    )

    while True:
        if await request.is_disconnected():
            break

        yeni_sira, olaylar = await asyncio.to_thread(
            bridge.olay_deposu.bekle,
            onceki_sira=sira,
            zaman_asimi=kalp_atisi_suresi,
        )

        if olaylar:
            for olay in olaylar:
                veri = json.dumps(
                    olay.json_verisi(),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )

                yield (
                    f"id: {olay.olay_kimligi}\n"
                    f"event: {olay.olay_turu.value}\n"
                    f"data: {veri}\n\n"
                )

            sira = yeni_sira
            continue

        kalp_atisi = json.dumps(
            {
                "olay_turu": "kalp_atisi",
                "runtime_portu": 8013,
                "son_sira": yeni_sira,
                "durum": "baglanti_acik",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

        yield (
            "event: kalp_atisi\n"
            f"data: {kalp_atisi}\n\n"
        )


@ugr_router.get(
    "/events",
    summary="UGR canlı Server-Sent Events kanalı",
)
async def ugr_canli_olaylar(
    request: Request,
    son_sira: int = Query(
        default=0,
        ge=0,
    ),
    kalp_atisi_suresi: float = Query(
        default=10.0,
        ge=1.0,
        le=60.0,
    ),
) -> StreamingResponse:
    """İkon durum değişikliklerini sayfa yenilemeden yayınlar."""

    _bridge_baslat()

    return StreamingResponse(
        _sse_akisi(
            request,
            son_sira=son_sira,
            kalp_atisi_suresi=(
                kalp_atisi_suresi
            ),
        ),
        media_type=(
            "text/event-stream"
        ),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@ugr_router.get(
    "/preview",
    response_class=HTMLResponse,
    summary="UGR dinamik ikon ön izleme sayfası",
)
def ugr_onizleme() -> HTMLResponse:
    """Dinamik ikonların tarayıcı ön izlemesini döndürür."""

    if _UGR_PREVIEW.exists():
        return HTMLResponse(
            status_code=200,
            content=_UGR_PREVIEW.read_text(
                encoding="utf-8-sig"
            ),
            headers={
                "Cache-Control": "no-store",
            },
        )

    bridge = _bridge_baslat()

    kayitlar = (
        bridge
        .ikon_servisi
        .kayit_defteri
        .tumu()[:30]
    )

    grid = (
        bridge
        .web_render_servisi
        .grid_html_uret(
            kayitlar,
            baslik=(
                "SyKaşif UGR Dinamik İkon Runtime"
            ),
        )
    )

    html = f"""<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>SyKaşif UGR Dinamik İkonlar</title>
    <link
        rel="stylesheet"
        href="/api/ugr/assets/web/static/css/ugr_dynamic_icons.css"
    >
</head>
<body style="
    margin:0;
    min-height:100vh;
    padding:32px;
    background:#07101a;
    font-family:Segoe UI,Arial,sans-serif;
">
    {grid}

    <script
        src="/api/ugr/assets/web/static/js/ugr_dynamic_icons.js"
    ></script>

    <script>
        document.addEventListener(
            "DOMContentLoaded",
            function () {{
                const kutuphane = document.querySelector(
                    "[data-syk-ugr-library]"
                );

                if (!kutuphane) {{
                    return;
                }}

                const olayKaynagi = new EventSource(
                    "/api/ugr/events"
                );

                [
                    "ikon_durumu",
                    "ikon_gorunumu",
                    "ikon_aktifligi"
                ].forEach(function (olayTuru) {{
                    olayKaynagi.addEventListener(
                        olayTuru,
                        function (event) {{
                            const olay = JSON.parse(
                                event.data
                            );

                            const veri = olay.veri || {{}};

                            if (
                                kutuphane.sykUgrRuntime
                                && veri.ikon_kimligi
                            ) {{
                                kutuphane
                                    .sykUgrRuntime
                                    .updateFromPayload(
                                        veri
                                    );
                            }}
                        }}
                    );
                }});
            }}
        );
    </script>
</body>
</html>
"""

    return HTMLResponse(
        status_code=200,
        content=html,
        headers={
            "Cache-Control": "no-store",
        },
    )


@ugr_router.get(
    "/assets/{goreli_yol:path}",
    summary="UGR ikon ve web çalışma dosyalarını sunar",
)
def ugr_statik_dosya(
    goreli_yol: str,
) -> FileResponse:
    """UGR statik dosyalarını güvenli şekilde sunar."""

    dosya = _guvenli_statik_yol(
        goreli_yol
    )

    uzanti = dosya.suffix.lower()

    medya_turleri = {
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".png": "image/png",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".html": "text/html; charset=utf-8",
    }

    return FileResponse(
        path=dosya,
        media_type=medya_turleri.get(
            uzanti,
            "application/octet-stream",
        ),
        filename=None,
        headers={
            "Cache-Control": (
                "public, max-age=3600"
            ),
        },
    )


def ugr_runtime_durum_ozeti() -> dict[str, Any]:
    """Ana runtime tarafından kullanılabilen durum özeti."""

    bridge = _bridge_baslat()

    return bridge.durum_ozeti()


__all__ = [
    "ugr_router",
    "ugr_runtime_durum_ozeti",
]

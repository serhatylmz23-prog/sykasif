from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from terminal_v2.core.panel_broadcast import (
    panel_broadcast_hub,
)
from terminal_v2.core.runtime_state import (
    runtime_state,
)


router = APIRouter(
    prefix="/api/v2/runtime-state",
    tags=["Terminal V2 Ortak Çalışma Durumu"],
)


class SistemDurumuIstegi(BaseModel):
    durum: str = Field(
        min_length=3,
        max_length=32,
    )
    mesaj: str = Field(
        min_length=1,
        max_length=240,
    )
    kaynak: str = Field(
        default="runtime",
        min_length=2,
        max_length=80,
    )


class CihazDurumuIstegi(BaseModel):
    cihaz_turu: str = Field(
        min_length=5,
        max_length=20,
    )
    bagli: bool
    kaynak: str | None = Field(
        default=None,
        max_length=80,
    )


class AktifModulIstegi(BaseModel):
    modul_kodu: str = Field(
        min_length=1,
        max_length=100,
    )
    kaynak: str = Field(
        min_length=2,
        max_length=80,
    )


async def yayinla(
    snapshot: dict[str, Any],
    *,
    mesaj: str,
) -> dict[str, Any]:
    event = await panel_broadcast_hub.publish(
        event_type="runtime_durumu_guncellendi",
        payload={
            "mesaj": mesaj,
            "revision": snapshot["revision"],
            "durum": snapshot["durum"],
        },
    )

    return {
        "sonuc": "BASARILI",
        "mesaj": mesaj,
        "revision": snapshot["revision"],
        "durum": snapshot["durum"],
        "yayin": event,
        "bagli_istemci_sayisi": (
            await panel_broadcast_hub.client_count()
        ),
    }


@router.get("")
async def runtime_durumu() -> dict[str, Any]:
    snapshot = await runtime_state.snapshot()

    return {
        "sonuc": "BASARILI",
        "mesaj": "Ortak çalışma durumu hazır.",
        **snapshot,
    }


@router.post("/sistem")
async def sistem_durumunu_degistir(
    request: SistemDurumuIstegi,
) -> dict[str, Any]:
    try:
        snapshot = await runtime_state.set_system_status(
            durum=request.durum,
            mesaj=request.mesaj,
            kaynak=request.kaynak,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return await yayinla(
        snapshot,
        mesaj="Sistem durumu tüm cihazlara gönderildi.",
    )


@router.post("/cihaz")
async def cihaz_durumunu_degistir(
    request: CihazDurumuIstegi,
) -> dict[str, Any]:
    try:
        snapshot = await runtime_state.set_device(
            cihaz_turu=request.cihaz_turu,
            bagli=request.bagli,
            kaynak=request.kaynak,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    durum_metni = (
        "bağlandı"
        if request.bagli
        else "çevrimdışı oldu"
    )

    return await yayinla(
        snapshot,
        mesaj=(
            f"{request.cihaz_turu.capitalize()} "
            f"{durum_metni}."
        ),
    )


@router.post("/aktif-modul")
async def aktif_modulu_degistir(
    request: AktifModulIstegi,
) -> dict[str, Any]:
    try:
        snapshot = await runtime_state.set_active_module(
            request.modul_kodu,
            kaynak=request.kaynak,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return await yayinla(
        snapshot,
        mesaj=(
            "Aktif modül tüm cihazlarda "
            "eş zamanlı güncellendi."
        ),
    )


@router.delete("")
async def runtime_durumunu_sifirla() -> dict[str, Any]:
    snapshot = await runtime_state.reset()

    return await yayinla(
        snapshot,
        mesaj="Ortak çalışma durumu sıfırlandı.",
    )

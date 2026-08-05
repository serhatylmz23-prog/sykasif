from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from terminal_v2.core.module_cards import (
    modul_durumunu_degistir,
    modul_kartlari,
)
from terminal_v2.core.panel_broadcast import (
    panel_broadcast_hub,
)


router = APIRouter(
    prefix="/api/v2/modul-kartlari",
    tags=["Terminal V2 Canlı Modül Kartları"],
)


class ModulDurumuIstegi(BaseModel):
    modul_kodu: str = Field(
        min_length=1,
        max_length=100,
    )
    durum: str = Field(
        min_length=3,
        max_length=32,
    )
    kaynak: str = Field(
        default="runtime",
        min_length=2,
        max_length=80,
    )


@router.get("")
async def kartlari_getir() -> dict[str, Any]:
    return await modul_kartlari()


@router.post("/durum")
async def kart_durumunu_degistir(
    request: ModulDurumuIstegi,
) -> dict[str, Any]:
    try:
        sonuc = await modul_durumunu_degistir(
            modul_kodu=request.modul_kodu,
            durum=request.durum,
            kaynak=request.kaynak,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    await panel_broadcast_hub.publish(
        event_type="modul_kartlari_guncellendi",
        payload=sonuc,
    )

    return sonuc

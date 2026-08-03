from __future__ import annotations

from dataclasses import asdict

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel, Field

from syk_core.goruntu.goruntu_uzmani_modeli import (
    GoruntuKaydi,
    GoruntuUzmani,
)

from .dtse_attention_routes import (
    dtse_attention_engine,
)
from .goruntu_dtse_adapter import (
    GoruntuDTSEAdapter,
)


router = APIRouter(
    prefix="/goruntu",
    tags=["goruntu-dtse"],
)

goruntu_uzmani = GoruntuUzmani()

goruntu_dtse_adapter = GoruntuDTSEAdapter(
    uzman=goruntu_uzmani,
    dtse=dtse_attention_engine,
)


class GoruntuKaydiRequest(BaseModel):
    veri_kimligi: str
    veri_turu: str
    kaynak: str

    konum_bilgisi: str | None = None

    kare_genisligi: int | None = Field(
        default=None,
        gt=0,
    )

    kare_yuksekligi: int | None = Field(
        default=None,
        gt=0,
    )

    kare_numarasi: int = Field(
        default=0,
        ge=0,
    )

    zaman_ms: int = Field(
        default=0,
        ge=0,
    )


class SupheliBolgeRequest(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)

    genislik: int = Field(gt=0)
    yukseklik: int = Field(gt=0)

    aciklama: str
    guven: float = Field(
        default=75.0,
        ge=0.0,
        le=99.9,
    )

    sinyal_turu: str | None = None


@router.post("/kayitlar")
def goruntu_kaydi_olustur(
    request: GoruntuKaydiRequest,
) -> dict:
    if goruntu_uzmani.getir(
        request.veri_kimligi
    ) is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Görüntü kaydı zaten var: "
                f"{request.veri_kimligi}"
            ),
        )

    kayit = goruntu_uzmani.goruntu_kaydet(
        GoruntuKaydi(
            veri_kimligi=(
                request.veri_kimligi
            ),
            veri_turu=request.veri_turu,
            kaynak=request.kaynak,
            konum_bilgisi=(
                request.konum_bilgisi
            ),
            kare_genisligi=(
                request.kare_genisligi
            ),
            kare_yuksekligi=(
                request.kare_yuksekligi
            ),
            kare_numarasi=(
                request.kare_numarasi
            ),
            zaman_ms=request.zaman_ms,
        )
    )

    return asdict(kayit)


@router.post(
    "/kayitlar/{veri_kimligi}/supheli-bolgeler"
)
def supheli_bolge_ekle(
    veri_kimligi: str,
    request: SupheliBolgeRequest,
) -> dict:
    try:
        bolge = (
            goruntu_uzmani
            .supheli_bolge_isaretle(
                veri_kimligi,
                request.x,
                request.y,
                request.genislik,
                request.yukseklik,
                request.aciklama,
                request.guven,
                request.sinyal_turu,
            )
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    adapter_error = (
        goruntu_dtse_adapter.son_hata
    )

    if (
        adapter_error is not None
        and adapter_error.get(
            "veri_kimligi"
        ) == veri_kimligi
    ):
        raise HTTPException(
            status_code=422,
            detail=adapter_error["reason"],
        )

    return {
        "veri_kimligi": veri_kimligi,
        "bolge": bolge,
        "dtse": (
            goruntu_dtse_adapter
            .son_sonuc
        ),
    }


@router.get(
    "/kayitlar/{veri_kimligi}"
)
def goruntu_kaydi_getir(
    veri_kimligi: str,
) -> dict:
    kayit = goruntu_uzmani.getir(
        veri_kimligi
    )

    if kayit is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Görüntü kaydı bulunamadı: "
                f"{veri_kimligi}"
            ),
        )

    return asdict(kayit)


@router.get("/dtse-adapter-state")
def goruntu_dtse_durumu() -> dict:
    return goruntu_dtse_adapter.durum()
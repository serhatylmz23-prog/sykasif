from __future__ import annotations

from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .theme_engine import theme_engine


router = APIRouter(
    prefix="/themes",
    tags=["sykasif-themes"],
)


class ThemeSelectionRequest(BaseModel):
    theme_id: str


class AutomaticThemeRequest(BaseModel):
    hour: int = Field(
        ge=0,
        le=23,
    )
    weather: str = "clear"
    device: str = "desktop"


@router.get("")
def list_themes() -> dict:
    return theme_engine.snapshot()


@router.get("/current")
def current_theme() -> dict:
    return theme_engine.runtime.snapshot()


@router.put("/current")
def select_theme(
    request: ThemeSelectionRequest,
) -> dict:
    try:
        return theme_engine.runtime.set(
            request.theme_id
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.post("/automatic")
def automatic_theme(
    request: AutomaticThemeRequest,
) -> dict:
    try:
        return theme_engine.runtime.automatic(
            hour=request.hour,
            weather=request.weather,
            device=request.device,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.get(
    "/{theme_id}/assets/{filename}"
)
def theme_asset(
    theme_id: str,
    filename: str,
):
    try:
        path = theme_engine.assets.resolve(
            theme_id,
            filename,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(
        Path(filename).suffix.lower(),
        "application/octet-stream",
    )

    return FileResponse(
        path,
        media_type=media_type,
    )
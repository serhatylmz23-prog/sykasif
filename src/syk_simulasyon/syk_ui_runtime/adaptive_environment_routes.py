from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from .adaptive_environment import (
    AdaptiveEnvironmentEngine,
)


router = APIRouter(
    prefix="/environment",
    tags=["sykasif-environment"],
)

adaptive_environment = (
    AdaptiveEnvironmentEngine()
)


class EnvironmentUpdateRequest(BaseModel):
    weather: str
    temperature_c: float
    wind_speed_kmh: float = Field(
        ge=0.0
    )
    wind_direction_deg: float = 0.0
    cloud_percent: float = Field(
        ge=0.0,
        le=100.0,
    )
    precipitation_percent: float = Field(
        ge=0.0,
        le=100.0,
    )
    timezone: str = "Europe/Istanbul"
    latitude: float | None = None
    longitude: float | None = None
    source: str = "manual_runtime"


@router.get("/current")
def get_current_environment() -> dict:
    return adaptive_environment.current()


@router.patch("/current")
def update_current_environment(
    request: EnvironmentUpdateRequest,
) -> dict:
    try:
        return adaptive_environment.update(
            **request.model_dump()
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.delete("/current")
def clear_current_environment() -> dict:
    return adaptive_environment.clear_manual()
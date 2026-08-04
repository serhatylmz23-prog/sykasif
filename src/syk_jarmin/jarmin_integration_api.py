from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from syk_jarmin.runtime.integration_runtime import (
    jarmin_integration_runtime,
)


router = APIRouter(
    prefix="/jarmin/integration",
    tags=["jarmin-integration"],
)


class JarminSettingsUpdateRequest(
    BaseModel
):
    language: str | None = None
    voice_enabled: bool | None = None
    notification_enabled: (
        bool | None
    ) = None
    wake_word_enabled: bool | None = None
    voice_profile_id: str | None = None
    theme_mode: str | None = None
    device_id: str | None = None


class JarminEventRequest(BaseModel):
    event_type: str = Field(
        min_length=1,
        max_length=100,
    )
    source: str = Field(
        min_length=1,
        max_length=200,
    )
    title: str | None = Field(
        default=None,
        max_length=200,
    )
    message: str = Field(
        min_length=1,
        max_length=5000,
    )
    payload: dict[str, Any] = {}


@router.get("")
def get_integration_state() -> dict:
    return (
        jarmin_integration_runtime
        .snapshot()
    )


@router.get("/settings")
def get_jarmin_settings() -> dict:
    return (
        jarmin_integration_runtime
        .settings
        .snapshot()
    )


@router.patch("/settings")
def update_jarmin_settings(
    request: JarminSettingsUpdateRequest,
) -> dict:
    try:
        changes = {
            key: value
            for key, value
            in request.model_dump().items()
            if value is not None
        }

        return (
            jarmin_integration_runtime
            .update_settings(
                **changes
            )
        )

    except (
        KeyError,
        ValueError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.delete("/settings")
def reset_jarmin_settings() -> dict:
    jarmin_integration_runtime \
        .settings.reset()

    return (
        jarmin_integration_runtime
        .apply_settings()
    )


@router.post("/events")
def ingest_jarmin_event(
    request: JarminEventRequest,
) -> dict:
    try:
        return (
            jarmin_integration_runtime
            .ingest_event(
                event_type=(
                    request.event_type
                ),
                source=request.source,
                title=request.title,
                message=request.message,
                payload=request.payload,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/events")
def list_jarmin_events(
    event_type: str | None = None,
    limit: int = 50,
) -> dict:
    try:
        events = (
            jarmin_integration_runtime
            .event_bridge
            .list(
                event_type=event_type,
                limit=limit,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "event_count": len(events),
        "events": [
            event.as_dict()
            for event in events
        ],
    }
from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from .mobile_control_runtime import (
    mobile_control_runtime,
)


router = APIRouter(
    prefix="/mobile-control",
    tags=["telefon-tablet-kontrol-paneli"],
)


class RegisterControlRequest(BaseModel):
    device_id: str = Field(
        min_length=1,
        max_length=200,
    )
    device_type: str


class UpdateControlRequest(BaseModel):
    camera_state: str | None = None
    microphone_state: str | None = None
    location_state: str | None = None
    notification_permission: (
        str | None
    ) = None
    connection_state: str | None = None
    pairing_state: str | None = None
    offline_queue_count: (
        int | None
    ) = Field(
        default=None,
        ge=0,
    )
    fullscreen: bool | None = None
    wake_lock: bool | None = None
    last_error: str | None = Field(
        default=None,
        max_length=2000,
    )


@router.get("")
def get_mobile_control_runtime() -> dict:
    return mobile_control_runtime \
        .snapshot()


@router.post("/devices")
def register_mobile_control(
    request: RegisterControlRequest,
) -> dict:
    try:
        return mobile_control_runtime \
            .register(
                device_id=(
                    request.device_id
                ),
                device_type=(
                    request.device_type
                ),
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/devices")
def list_mobile_controls() -> list[dict]:
    return mobile_control_runtime.list()


@router.get("/devices/{device_id}")
def get_mobile_control(
    device_id: str,
) -> dict:
    try:
        return mobile_control_runtime.get(
            device_id
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.patch("/devices/{device_id}")
def update_mobile_control(
    device_id: str,
    request: UpdateControlRequest,
) -> dict:
    try:
        return mobile_control_runtime \
            .update(
                device_id,
                camera_state=(
                    request.camera_state
                ),
                microphone_state=(
                    request
                    .microphone_state
                ),
                location_state=(
                    request.location_state
                ),
                notification_permission=(
                    request
                    .notification_permission
                ),
                connection_state=(
                    request.connection_state
                ),
                pairing_state=(
                    request.pairing_state
                ),
                offline_queue_count=(
                    request
                    .offline_queue_count
                ),
                fullscreen=(
                    request.fullscreen
                ),
                wake_lock=(
                    request.wake_lock
                ),
                last_error=(
                    request.last_error
                ),
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


@router.post(
    "/devices/{device_id}/reset"
)
def reset_mobile_control(
    device_id: str,
) -> dict:
    try:
        return mobile_control_runtime \
            .reset(
                device_id
            )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
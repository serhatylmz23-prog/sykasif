from __future__ import annotations

import base64
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import (
    BaseModel,
    Field,
)

from .mobile_sensor_runtime import (
    LocationReading,
    mobile_sensor_runtime,
)


router = APIRouter(
    prefix="/mobile-sensors",
    tags=["telefon-tablet-sensorleri"],
)


class PermissionRequest(BaseModel):
    sensor_type: str
    state: str


class CameraStartRequest(BaseModel):
    facing_mode: str = "environment"
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    frame_rate: float = Field(gt=0)
    stream_id: str | None = None


class MicrophoneStartRequest(BaseModel):
    sample_rate: int = Field(
        default=16000,
        ge=8000,
    )
    channels: int = Field(
        default=1,
        ge=1,
        le=2,
    )
    stream_id: str | None = None


class LocationRequest(BaseModel):
    latitude: float = Field(
        ge=-90.0,
        le=90.0,
    )
    longitude: float = Field(
        ge=-180.0,
        le=180.0,
    )
    accuracy_meters: float = Field(
        ge=0.0,
    )
    altitude_meters: float | None = None
    heading_degrees: float | None = Field(
        default=None,
        ge=0.0,
        le=360.0,
    )
    speed_meters_per_second: (
        float | None
    ) = Field(
        default=None,
        ge=0.0,
    )
    captured_at: str | None = None
    source: str = "browser_geolocation"


class FrameCaptureRequest(BaseModel):
    device_id: str
    data_base64: str
    mime_type: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    source: str = "mobile_camera"


@router.get("")
def get_sensor_runtime() -> dict:
    return mobile_sensor_runtime.snapshot()


@router.patch("/permissions")
def update_sensor_permission(
    request: PermissionRequest,
) -> dict:
    try:
        return (
            mobile_sensor_runtime
            .update_permission(
                sensor_type=(
                    request.sensor_type
                ),
                state=request.state,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post("/camera/start")
def start_camera(
    request: CameraStartRequest,
) -> dict:
    try:
        return (
            mobile_sensor_runtime
            .start_camera(
                facing_mode=(
                    request.facing_mode
                ),
                width=request.width,
                height=request.height,
                frame_rate=(
                    request.frame_rate
                ),
                stream_id=(
                    request.stream_id
                ),
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post("/camera/stop")
def stop_camera() -> dict:
    return mobile_sensor_runtime \
        .stop_camera()


@router.post("/microphone/start")
def start_microphone(
    request: MicrophoneStartRequest,
) -> dict:
    try:
        return (
            mobile_sensor_runtime
            .start_microphone(
                sample_rate=(
                    request.sample_rate
                ),
                channels=request.channels,
                stream_id=(
                    request.stream_id
                ),
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post("/microphone/stop")
def stop_microphone() -> dict:
    return mobile_sensor_runtime \
        .stop_microphone()


@router.post("/location")
def add_location(
    request: LocationRequest,
) -> dict:
    reading = LocationReading(
        latitude=request.latitude,
        longitude=request.longitude,
        accuracy_meters=(
            request.accuracy_meters
        ),
        altitude_meters=(
            request.altitude_meters
        ),
        heading_degrees=(
            request.heading_degrees
        ),
        speed_meters_per_second=(
            request
            .speed_meters_per_second
        ),
        captured_at=(
            request.captured_at
            or datetime.now(
                UTC
            ).isoformat()
        ),
        source=request.source,
    )

    try:
        return mobile_sensor_runtime \
            .add_location(
                reading
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/locations")
def list_locations(
    limit: int = 20,
) -> list[dict]:
    try:
        return (
            mobile_sensor_runtime
            .recent_locations(
                limit=limit
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.post("/frames")
def capture_frame(
    request: FrameCaptureRequest,
) -> dict:
    try:
        data = base64.b64decode(
            request.data_base64,
            validate=True,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=(
                "Görüntü verisi Base64 olarak "
                "çözülemedi."
            ),
        ) from error

    try:
        return (
            mobile_sensor_runtime
            .capture_frame(
                device_id=(
                    request.device_id
                ),
                data=data,
                mime_type=(
                    request.mime_type
                ),
                width=request.width,
                height=request.height,
                source=request.source,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/frames")
def list_frames(
    limit: int = 20,
) -> list[dict]:
    try:
        return (
            mobile_sensor_runtime
            .recent_frames(
                limit=limit
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("/frames/{frame_id}")
def get_frame(
    frame_id: str,
) -> dict:
    try:
        return (
            mobile_sensor_runtime
            .get_frame(
                frame_id
            )
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
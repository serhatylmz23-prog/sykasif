from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)
from pydantic import BaseModel, Field

from syk_core.external_devices import (
    DeviceConnectionState,
)

from .external_device_runtime import (
    external_device_runtime,
)


class MockGarminRegisterRequest(BaseModel):
    latitude: float = Field(
        default=38.7123,
        ge=-90.0,
        le=90.0,
    )
    longitude: float = Field(
        default=38.4521,
        ge=-180.0,
        le=180.0,
    )
    minimum_depth_m: float = Field(
        default=0.35,
        ge=0.0,
    )
    maximum_depth_m: float = Field(
        default=2.0,
        gt=0.0,
    )
    water_temperature_c: float = 19.5
    seed: int = 1903


class FrameReadRequest(BaseModel):
    research_id: str | None = Field(
        default=None,
        max_length=160,
    )
    workspace_id: str | None = Field(
        default=None,
        max_length=160,
    )


external_device_router = APIRouter(
    prefix="/api/syk-ui/external-devices",
    tags=["syk-ui-external-devices"],
)


@external_device_router.get("")
def list_devices() -> dict[str, object]:
    devices = external_device_runtime.list_devices()

    return {
        "count": len(devices),
        "devices": devices,
    }


@external_device_router.post(
    "/garmin/mock",
    status_code=201,
)
def register_mock_garmin(
    request: MockGarminRegisterRequest,
) -> dict[str, object]:
    if (
        request.maximum_depth_m
        < request.minimum_depth_m
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Azami derinlik asgari "
                "derinlikten küçük olamaz."
            ),
        )

    device = (
        external_device_runtime
        .register_mock_garmin(
            latitude=request.latitude,
            longitude=request.longitude,
            minimum_depth_m=(
                request.minimum_depth_m
            ),
            maximum_depth_m=(
                request.maximum_depth_m
            ),
            water_temperature_c=(
                request.water_temperature_c
            ),
            seed=request.seed,
        )
    )

    return device.status_snapshot()


@external_device_router.get(
    "/{device_id}"
)
def get_device(
    device_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    device = external_device_runtime.get_device(
        device_id
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Haricî cihaz bulunamadı.",
        )

    return device.status_snapshot()


@external_device_router.post(
    "/{device_id}/connect"
)
def connect_device(
    device_id: str,
) -> dict[str, object]:
    device = external_device_runtime.connect(
        device_id
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Haricî cihaz bulunamadı.",
        )

    return device.status_snapshot()


@external_device_router.post(
    "/{device_id}/disconnect"
)
def disconnect_device(
    device_id: str,
) -> dict[str, object]:
    device = external_device_runtime.disconnect(
        device_id
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Haricî cihaz bulunamadı.",
        )

    return device.status_snapshot()


@external_device_router.post(
    "/{device_id}/frames",
    status_code=201,
)
def read_sonar_frame(
    device_id: str,
    request: FrameReadRequest,
) -> dict[str, object]:
    device = external_device_runtime.get_device(
        device_id
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Haricî cihaz bulunamadı.",
        )

    if (
        device.connection_state
        != DeviceConnectionState.CONNECTED
    ):
        raise HTTPException(
            status_code=409,
            detail="Haricî cihaz bağlı değil.",
        )

    record = external_device_runtime.read_frame(
        device_id,
        research_id=request.research_id,
        workspace_id=request.workspace_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Haricî cihaz bulunamadı.",
        )

    return record.to_dict()


@external_device_router.get(
    "/records/list"
)
def list_sonar_records(
    device_id: Annotated[
        str | None,
        Query(),
    ] = None,
    research_id: Annotated[
        str | None,
        Query(),
    ] = None,
    workspace_id: Annotated[
        str | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    records = external_device_runtime.list_records(
        device_id=device_id,
        research_id=research_id,
        workspace_id=workspace_id,
    )

    return {
        "count": len(records),
        "records": [
            record.to_dict()
            for record in records
        ],
    }
from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
)
from pydantic import BaseModel, Field

from syk_core.external_devices.connection_model import (
    DeviceTransportType,
)

from .real_device_connection_runtime import (
    real_device_connection_runtime,
)


class ConnectionCreateRequest(BaseModel):
    manufacturer: str = Field(
        min_length=1,
        max_length=120,
    )
    model: str = Field(
        min_length=1,
        max_length=160,
    )
    serial_number: str = Field(
        min_length=1,
        max_length=160,
    )
    device_id: str = Field(
        min_length=1,
        max_length=180,
    )
    transport: DeviceTransportType
    host: str | None = None
    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
    )
    serial_port: str | None = None
    baud_rate: int | None = Field(
        default=None,
        gt=0,
    )
    timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        le=120,
    )


class NmeaIngestRequest(BaseModel):
    sentence: str = Field(
        min_length=1,
        max_length=2048,
    )
    validate_checksum: bool = True


real_device_connection_router = APIRouter(
    prefix="/api/syk-ui/real-device-connections",
    tags=["syk-ui-real-device-connections"],
)


@real_device_connection_router.get("")
def list_connections() -> dict[str, object]:
    connections = (
        real_device_connection_runtime.list()
    )

    return {
        "count": len(connections),
        "connections": [
            connection.to_dict()
            for connection in connections
        ],
    }


@real_device_connection_router.post(
    "",
    status_code=201,
)
def create_connection(
    request: ConnectionCreateRequest,
) -> dict[str, object]:
    try:
        connection = (
            real_device_connection_runtime.create(
                manufacturer=request.manufacturer,
                model=request.model,
                serial_number=request.serial_number,
                device_id=request.device_id,
                transport=request.transport,
                host=request.host,
                port=request.port,
                serial_port=request.serial_port,
                baud_rate=request.baud_rate,
                timeout_seconds=request.timeout_seconds,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return connection.to_dict()


@real_device_connection_router.get(
    "/{connection_id}"
)
def get_connection(
    connection_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    connection = (
        real_device_connection_runtime.get(
            connection_id
        )
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return connection.to_dict()


@real_device_connection_router.post(
    "/{connection_id}/connect"
)
def connect(
    connection_id: str,
) -> dict[str, object]:
    connection = (
        real_device_connection_runtime.connect(
            connection_id
        )
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return connection.to_dict()


@real_device_connection_router.post(
    "/{connection_id}/disconnect"
)
def disconnect(
    connection_id: str,
) -> dict[str, object]:
    connection = (
        real_device_connection_runtime.disconnect(
            connection_id
        )
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return connection.to_dict()


@real_device_connection_router.post(
    "/{connection_id}/heartbeat"
)
def heartbeat(
    connection_id: str,
) -> dict[str, object]:
    try:
        connection = (
            real_device_connection_runtime.heartbeat(
                connection_id
            )
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return connection.to_dict()


@real_device_connection_router.post(
    "/{connection_id}/reconnect"
)
def reconnect(
    connection_id: str,
) -> dict[str, object]:
    connection = (
        real_device_connection_runtime.reconnect(
            connection_id
        )
    )

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return connection.to_dict()


@real_device_connection_router.post(
    "/{connection_id}/nmea"
)
def ingest_nmea(
    connection_id: str,
    request: NmeaIngestRequest,
) -> dict[str, object]:
    try:
        connection = (
            real_device_connection_runtime.ingest_nmea(
                connection_id,
                sentence=request.sentence,
                validate_checksum=(
                    request.validate_checksum
                ),
            )
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    if connection is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return connection.to_dict()


@real_device_connection_router.get(
    "/{connection_id}/manifest"
)
def manifest(
    connection_id: str,
) -> dict[str, object]:
    manifest_record = (
        real_device_connection_runtime.manifest(
            connection_id
        )
    )

    if manifest_record is None:
        raise HTTPException(
            status_code=404,
            detail="Gerçek cihaz bağlantısı bulunamadı.",
        )

    return manifest_record.to_dict()
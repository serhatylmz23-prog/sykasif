from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from threading import RLock
from typing import Any
from uuid import uuid4

from syk_core.external_devices.connection_model import (
    DeviceEndpoint,
    DeviceTransportType,
)
from syk_core.external_devices.device_model import (
    DeviceConnectionState,
    DeviceIdentity,
)
from syk_core.external_devices.garmin_real_adapter import (
    GarminRealAdapter,
)


@dataclass(frozen=True, slots=True)
class ConnectionManifest:
    manifest_id: str
    source_id: str
    device_id: str
    transport: str
    authority: str
    real_device_data: bool
    simulation_data: bool
    vendor_raw_sonar_available: bool
    created_at: str
    digest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RealDeviceConnection:
    connection_id: str
    source_id: str
    adapter: GarminRealAdapter
    created_at: str
    updated_at: str
    last_heartbeat_at: str | None = None
    last_valid_data_at: str | None = None
    heartbeat_count: int = 0
    reconnect_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        snapshot = self.adapter.connection_snapshot()

        return {
            "connection_id": self.connection_id,
            "source_id": self.source_id,
            "device_id": (
                self.adapter.profile.identity.device_id
            ),
            "connection_state": (
                self.adapter.connection_state.value
            ),
            "health": self.adapter.health.value,
            "endpoint": self.adapter.endpoint.to_dict(),
            "protocol": self.adapter.protocol.to_dict(),
            "connection_snapshot": snapshot.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_heartbeat_at": self.last_heartbeat_at,
            "last_valid_data_at": self.last_valid_data_at,
            "heartbeat_count": self.heartbeat_count,
            "reconnect_count": self.reconnect_count,
        }


class RealDeviceConnectionRuntime:
    def __init__(self) -> None:
        self._lock = RLock()
        self._connections: dict[
            str,
            RealDeviceConnection,
        ] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def reset(self) -> None:
        with self._lock:
            connections = tuple(
                self._connections.values()
            )

            self._connections.clear()

        for connection in connections:
            if (
                connection.adapter.connection_state
                == DeviceConnectionState.CONNECTED
            ):
                connection.adapter.disconnect()

    def create(
        self,
        *,
        manufacturer: str,
        model: str,
        serial_number: str,
        device_id: str,
        transport: DeviceTransportType,
        host: str | None = None,
        port: int | None = None,
        serial_port: str | None = None,
        baud_rate: int | None = None,
        timeout_seconds: float = 5.0,
    ) -> RealDeviceConnection:
        if transport == DeviceTransportType.MOCK:
            raise ValueError(
                "Gerçek bağlantı Runtime API mock taşıma kabul etmez."
            )

        endpoint = DeviceEndpoint(
            transport=transport,
            host=host,
            port=port,
            serial_port=serial_port,
            baud_rate=baud_rate,
            timeout_seconds=timeout_seconds,
        )

        identity = DeviceIdentity(
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            device_id=device_id,
        )

        adapter = GarminRealAdapter(
            identity=identity,
            endpoint=endpoint,
        )

        now = self._now()

        connection = RealDeviceConnection(
            connection_id=str(uuid4()),
            source_id=f"external-device:{device_id}",
            adapter=adapter,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            if device_id in {
                item.adapter.profile.identity.device_id
                for item in self._connections.values()
            }:
                raise ValueError(
                    f"Cihaz kimliği zaten kayıtlı: {device_id}"
                )

            self._connections[
                connection.connection_id
            ] = connection

        return connection

    def get(
        self,
        connection_id: str,
    ) -> RealDeviceConnection | None:
        with self._lock:
            return self._connections.get(
                connection_id
            )

    def list(
        self,
    ) -> list[RealDeviceConnection]:
        with self._lock:
            return sorted(
                self._connections.values(),
                key=lambda item: item.created_at,
            )

    def connect(
        self,
        connection_id: str,
    ) -> RealDeviceConnection | None:
        connection = self.get(connection_id)

        if connection is None:
            return None

        connection.adapter.connect()
        connection.updated_at = self._now()

        return connection

    def disconnect(
        self,
        connection_id: str,
    ) -> RealDeviceConnection | None:
        connection = self.get(connection_id)

        if connection is None:
            return None

        connection.adapter.disconnect()
        connection.updated_at = self._now()

        return connection

    def heartbeat(
        self,
        connection_id: str,
    ) -> RealDeviceConnection | None:
        connection = self.get(connection_id)

        if connection is None:
            return None

        if (
            connection.adapter.connection_state
            != DeviceConnectionState.CONNECTED
        ):
            raise RuntimeError(
                "Bağlantı etkin değil."
            )

        now = self._now()

        connection.last_heartbeat_at = now
        connection.updated_at = now
        connection.heartbeat_count += 1

        return connection

    def reconnect(
        self,
        connection_id: str,
    ) -> RealDeviceConnection | None:
        connection = self.get(connection_id)

        if connection is None:
            return None

        if (
            connection.adapter.connection_state
            == DeviceConnectionState.CONNECTED
        ):
            connection.adapter.disconnect()

        connection.adapter.connect()
        connection.reconnect_count += 1
        connection.updated_at = self._now()

        return connection

    def ingest_nmea(
        self,
        connection_id: str,
        *,
        sentence: str,
        validate_checksum: bool = True,
    ) -> RealDeviceConnection | None:
        connection = self.get(connection_id)

        if connection is None:
            return None

        connection.adapter.ingest_nmea(
            sentence,
            validate_checksum=validate_checksum,
        )

        now = self._now()

        connection.last_valid_data_at = now
        connection.updated_at = now

        return connection

    def manifest(
        self,
        connection_id: str,
    ) -> ConnectionManifest | None:
        connection = self.get(connection_id)

        if connection is None:
            return None

        snapshot = connection.adapter.connection_snapshot()

        payload = "|".join(
            (
                connection.source_id,
                connection.adapter.profile.identity.device_id,
                connection.adapter.endpoint.transport.value,
                connection.adapter.protocol.authority.value,
                str(snapshot.real_device_data),
                str(snapshot.vendor_raw_sonar_available),
            )
        )

        digest = sha256(
            payload.encode("utf-8")
        ).hexdigest()

        return ConnectionManifest(
            manifest_id=str(uuid4()),
            source_id=connection.source_id,
            device_id=(
                connection.adapter
                .profile.identity.device_id
            ),
            transport=(
                connection.adapter
                .endpoint.transport.value
            ),
            authority=(
                connection.adapter
                .protocol.authority.value
            ),
            real_device_data=True,
            simulation_data=False,
            vendor_raw_sonar_available=(
                snapshot.vendor_raw_sonar_available
            ),
            created_at=self._now(),
            digest_sha256=digest,
        )


real_device_connection_runtime = (
    RealDeviceConnectionRuntime()
)
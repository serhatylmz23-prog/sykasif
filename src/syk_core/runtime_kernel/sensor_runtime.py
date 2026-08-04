"""SyKaşif sensör çalışma motoru."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from threading import RLock
from typing import Any
from uuid import uuid4

from .event_bus import RuntimeEvent, RuntimeEventBus
from .session_manager import (
    RuntimeSessionManager,
    RuntimeStreamType,
)


class SensorRuntimeError(RuntimeError):
    """Sensör çalışma motoru hatası."""


class SensorType(str, Enum):
    CAMERA = "kamera"
    PHOTO = "fotoğraf"
    VIDEO = "video"
    AUDIO = "ses"
    SONAR = "sonar"
    PROBE = "prob"
    MAGNETOMETER = "manyetometre"
    GRAVIMETER = "gravimetre"
    THERMAL = "termal"
    SPECTRAL = "spektral"
    LIDAR = "lidar"
    GPS = "gps"
    RTK = "rtk"
    WATER = "su_analizi"
    SOIL = "toprak_analizi"
    BOTANICAL = "botanik"


class SensorConnectionState(str, Enum):
    REGISTERED = "kayıtlı"
    CONNECTING = "bağlanıyor"
    CONNECTED = "bağlı"
    RECONNECTING = "yeniden_bağlanıyor"
    DISCONNECTED = "bağlantı_kesildi"
    OFFLINE = "çevrimdışı"
    FAILED = "hata"


class SensorPacketState(str, Enum):
    ACCEPTED = "kabul_edildi"
    BUFFERED = "tamponlandı"
    QUARANTINED = "karantinaya_alındı"
    REJECTED = "reddedildi"


@dataclass(slots=True, frozen=True)
class SensorDescriptor:
    sensor_id: str
    name: str
    sensor_type: SensorType
    source: str
    model: str | None = None
    serial_number: str | None = None
    capabilities: tuple[str, ...] = tuple()
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise ValueError(
                "Sensör kimliği boş olamaz."
            )

        if not self.name.strip():
            raise ValueError(
                "Sensör adı boş olamaz."
            )

        if not self.source.strip():
            raise ValueError(
                "Sensör kaynağı boş olamaz."
            )


@dataclass(slots=True)
class SensorDevice:
    descriptor: SensorDescriptor
    connection_state: SensorConnectionState = (
        SensorConnectionState.REGISTERED
    )
    quality_score: float | None = None
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None
    last_packet_at: datetime | None = None
    last_error: str | None = None
    reconnect_count: int = 0
    accepted_packet_count: int = 0
    buffered_packet_count: int = 0
    quarantined_packet_count: int = 0
    rejected_packet_count: int = 0

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "sensör_kimliği": (
                self.descriptor.sensor_id
            ),
            "ad": self.descriptor.name,
            "tür": self.descriptor.sensor_type.value,
            "kaynak": self.descriptor.source,
            "model": self.descriptor.model,
            "seri_numarası": (
                self.descriptor.serial_number
            ),
            "yetenekler": list(
                self.descriptor.capabilities
            ),
            "bağlantı_durumu": (
                self.connection_state.value
            ),
            "kalite_puanı": self.quality_score,
            "bağlantı_zamanı": (
                self.connected_at.isoformat()
                if self.connected_at
                else None
            ),
            "bağlantı_kesilme_zamanı": (
                self.disconnected_at.isoformat()
                if self.disconnected_at
                else None
            ),
            "son_paket_zamanı": (
                self.last_packet_at.isoformat()
                if self.last_packet_at
                else None
            ),
            "son_hata": self.last_error,
            "yeniden_bağlanma_sayısı": (
                self.reconnect_count
            ),
            "kabul_edilen_paket": (
                self.accepted_packet_count
            ),
            "tamponlanan_paket": (
                self.buffered_packet_count
            ),
            "karantina_paketi": (
                self.quarantined_packet_count
            ),
            "reddedilen_paket": (
                self.rejected_packet_count
            ),
            "veri": dict(
                self.descriptor.metadata
            ),
        }


@dataclass(slots=True, frozen=True)
class SensorPacket:
    packet_id: str
    sensor_id: str
    recorded_at: datetime
    payload: dict[str, Any]
    byte_count: int = 0
    frame_count: int = 1
    quality_score: float | None = None
    session_id: str | None = None
    evidence_id: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.packet_id.strip():
            raise ValueError(
                "Paket kimliği boş olamaz."
            )

        if not self.sensor_id.strip():
            raise ValueError(
                "Sensör kimliği boş olamaz."
            )

        if self.recorded_at.tzinfo is None:
            raise ValueError(
                "Paket zamanı saat dilimi içermelidir."
            )

        if self.byte_count < 0:
            raise ValueError(
                "Bayt sayısı negatif olamaz."
            )

        if self.frame_count < 0:
            raise ValueError(
                "Kare sayısı negatif olamaz."
            )

        if (
            self.quality_score is not None
            and not 0.0 <= self.quality_score <= 1.0
        ):
            raise ValueError(
                "Kalite puanı 0 ile 1 arasında olmalıdır."
            )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "paket_kimliği": self.packet_id,
            "sensör_kimliği": self.sensor_id,
            "zaman": self.recorded_at.isoformat(),
            "kalite_puanı": self.quality_score,
            "bayt_sayısı": self.byte_count,
            "kare_sayısı": self.frame_count,
            "oturum_kimliği": self.session_id,
            "kanıt_kimliği": self.evidence_id,
            "içerik": dict(self.payload),
            "veri": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class SensorPacketRecord:
    packet: SensorPacket
    state: SensorPacketState
    reason: str | None
    processed_at: datetime

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "durum": self.state.value,
            "neden": self.reason,
            "işlenme_zamanı": (
                self.processed_at.isoformat()
            ),
            "paket": self.packet.to_runtime_dict(),
        }


class SensorRuntime:
    """Sensör bağlantısı, veri kalitesi ve tampon yönetimi."""

    def __init__(
        self,
        *,
        event_bus: RuntimeEventBus | None = None,
        session_manager: RuntimeSessionManager | None = None,
        clock: Any | None = None,
        minimum_quality_score: float = 0.60,
        quarantine_quality_score: float = 0.30,
        offline_buffer_limit: int = 1000,
    ) -> None:
        if not 0.0 <= minimum_quality_score <= 1.0:
            raise ValueError(
                "Asgari kalite puanı geçersiz."
            )

        if not 0.0 <= quarantine_quality_score <= 1.0:
            raise ValueError(
                "Karantina kalite puanı geçersiz."
            )

        if (
            quarantine_quality_score
            > minimum_quality_score
        ):
            raise ValueError(
                "Karantina eşiği asgari kalite "
                "eşiğinden yüksek olamaz."
            )

        if offline_buffer_limit <= 0:
            raise ValueError(
                "Çevrimdışı tampon sınırı "
                "sıfırdan büyük olmalıdır."
            )

        self.event_bus = event_bus or RuntimeEventBus()
        self.session_manager = session_manager
        self._clock = clock or (
            lambda: datetime.now(UTC)
        )

        self.minimum_quality_score = (
            minimum_quality_score
        )
        self.quarantine_quality_score = (
            quarantine_quality_score
        )
        self.offline_buffer_limit = (
            offline_buffer_limit
        )

        self._devices: dict[str, SensorDevice] = {}
        self._stream_links: dict[
            tuple[str, str],
            str,
        ] = {}

        self._accepted: list[
            SensorPacketRecord
        ] = []
        self._buffer: list[
            SensorPacketRecord
        ] = []
        self._quarantine: list[
            SensorPacketRecord
        ] = []
        self._rejected: list[
            SensorPacketRecord
        ] = []

        self._lock = RLock()

    def register_sensor(
        self,
        descriptor: SensorDescriptor,
    ) -> SensorDevice:
        sensor_id = descriptor.sensor_id

        with self._lock:
            if sensor_id in self._devices:
                raise SensorRuntimeError(
                    "Sensör zaten kayıtlı: "
                    f"{sensor_id}"
                )

            device = SensorDevice(
                descriptor=descriptor
            )

            self._devices[sensor_id] = device

        self._publish(
            topic="runtime.sensor.registered",
            device=device,
        )

        return device

    def unregister_sensor(
        self,
        sensor_id: str,
    ) -> SensorDevice:
        device = self.get_sensor(sensor_id)

        if device.connection_state in {
            SensorConnectionState.CONNECTED,
            SensorConnectionState.CONNECTING,
            SensorConnectionState.RECONNECTING,
        }:
            raise SensorRuntimeError(
                "Bağlı sensör kaldırılamaz."
            )

        with self._lock:
            removed = self._devices.pop(sensor_id)

        self._publish(
            topic="runtime.sensor.unregistered",
            device=removed,
        )

        return removed

    def connect(
        self,
        sensor_id: str,
    ) -> SensorDevice:
        device = self.get_sensor(sensor_id)

        if (
            device.connection_state
            is SensorConnectionState.CONNECTED
        ):
            return device

        device.connection_state = (
            SensorConnectionState.CONNECTING
        )

        now = self._clock()

        device.connection_state = (
            SensorConnectionState.CONNECTED
        )
        device.connected_at = now
        device.disconnected_at = None
        device.last_error = None

        self._publish(
            topic="runtime.sensor.connected",
            device=device,
        )

        return device

    def disconnect(
        self,
        sensor_id: str,
        *,
        reason: str | None = None,
        offline: bool = False,
    ) -> SensorDevice:
        device = self.get_sensor(sensor_id)

        now = self._clock()

        device.connection_state = (
            SensorConnectionState.OFFLINE
            if offline
            else SensorConnectionState.DISCONNECTED
        )
        device.disconnected_at = now
        device.last_error = reason

        self._publish(
            topic=(
                "runtime.sensor.offline"
                if offline
                else "runtime.sensor.disconnected"
            ),
            device=device,
            extra={"reason": reason},
        )

        return device

    def reconnect(
        self,
        sensor_id: str,
    ) -> SensorDevice:
        device = self.get_sensor(sensor_id)

        if (
            device.connection_state
            is SensorConnectionState.CONNECTED
        ):
            return device

        device.connection_state = (
            SensorConnectionState.RECONNECTING
        )
        device.reconnect_count += 1

        self._publish(
            topic="runtime.sensor.reconnecting",
            device=device,
        )

        self.connect(sensor_id)
        self.flush_offline_buffer(
            sensor_id=sensor_id
        )

        self._publish(
            topic="runtime.sensor.reconnected",
            device=device,
        )

        return device

    def fail_sensor(
        self,
        sensor_id: str,
        *,
        reason: str,
    ) -> SensorDevice:
        device = self.get_sensor(sensor_id)

        device.connection_state = (
            SensorConnectionState.FAILED
        )
        device.last_error = reason
        device.disconnected_at = self._clock()

        self._publish(
            topic="runtime.sensor.failed",
            device=device,
            extra={"reason": reason},
        )

        return device

    def submit_packet(
        self,
        *,
        sensor_id: str,
        payload: dict[str, Any],
        quality_score: float | None = None,
        byte_count: int = 0,
        frame_count: int = 1,
        session_id: str | None = None,
        evidence_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        packet_id: str | None = None,
    ) -> SensorPacketRecord:
        device = self.get_sensor(sensor_id)

        packet = SensorPacket(
            packet_id=(
                packet_id
                or "SYK-PACKET-"
                + uuid4().hex.upper()
            ),
            sensor_id=sensor_id,
            recorded_at=self._clock(),
            payload=dict(payload),
            byte_count=byte_count,
            frame_count=frame_count,
            quality_score=quality_score,
            session_id=session_id,
            evidence_id=evidence_id,
            metadata=dict(metadata or {}),
        )

        if (
            device.connection_state
            is not SensorConnectionState.CONNECTED
        ):
            return self._buffer_packet(
                device,
                packet,
                reason="sensör çevrimdışı",
            )

        return self._process_connected_packet(
            device,
            packet,
        )

    def flush_offline_buffer(
        self,
        *,
        sensor_id: str | None = None,
    ) -> tuple[SensorPacketRecord, ...]:
        processed: list[
            SensorPacketRecord
        ] = []

        remaining: list[
            SensorPacketRecord
        ] = []

        for record in self._buffer:
            if (
                sensor_id is not None
                and record.packet.sensor_id != sensor_id
            ):
                remaining.append(record)
                continue

            device = self.get_sensor(
                record.packet.sensor_id
            )

            if (
                device.connection_state
                is not SensorConnectionState.CONNECTED
            ):
                remaining.append(record)
                continue

            result = self._process_connected_packet(
                device,
                record.packet,
            )
            processed.append(result)

        self._buffer = remaining

        if processed:
            self.event_bus.publish(
                RuntimeEvent(
                    topic=(
                        "runtime.sensor.buffer.flushed"
                    ),
                    source="sensor_runtime",
                    payload={
                        "sensor_id": sensor_id,
                        "packet_count": len(processed),
                    },
                )
            )

        return tuple(processed)

    def get_sensor(
        self,
        sensor_id: str,
    ) -> SensorDevice:
        try:
            return self._devices[sensor_id]
        except KeyError as exc:
            raise SensorRuntimeError(
                f"Sensör bulunamadı: {sensor_id}"
            ) from exc

    def list_sensors(
        self,
    ) -> tuple[SensorDevice, ...]:
        return tuple(
            self._devices[sensor_id]
            for sensor_id in sorted(self._devices)
        )

    @property
    def accepted_packets(
        self,
    ) -> tuple[SensorPacketRecord, ...]:
        return tuple(self._accepted)

    @property
    def buffered_packets(
        self,
    ) -> tuple[SensorPacketRecord, ...]:
        return tuple(self._buffer)

    @property
    def quarantined_packets(
        self,
    ) -> tuple[SensorPacketRecord, ...]:
        return tuple(self._quarantine)

    @property
    def rejected_packets(
        self,
    ) -> tuple[SensorPacketRecord, ...]:
        return tuple(self._rejected)

    def snapshot(self) -> dict[str, Any]:
        devices = self.list_sensors()

        return {
            "toplam_sensör_sayısı": len(devices),
            "bağlı_sensör_sayısı": sum(
                1
                for device in devices
                if device.connection_state
                is SensorConnectionState.CONNECTED
            ),
            "çevrimdışı_sensör_sayısı": sum(
                1
                for device in devices
                if device.connection_state
                is SensorConnectionState.OFFLINE
            ),
            "hatalı_sensör_sayısı": sum(
                1
                for device in devices
                if device.connection_state
                is SensorConnectionState.FAILED
            ),
            "kabul_edilen_paket_sayısı": len(
                self._accepted
            ),
            "tamponlanan_paket_sayısı": len(
                self._buffer
            ),
            "karantina_paketi_sayısı": len(
                self._quarantine
            ),
            "reddedilen_paket_sayısı": len(
                self._rejected
            ),
            "asgari_kalite_puanı": (
                self.minimum_quality_score
            ),
            "karantina_kalite_puanı": (
                self.quarantine_quality_score
            ),
            "sensörler": [
                device.to_runtime_dict()
                for device in devices
            ],
        }

    def _process_connected_packet(
        self,
        device: SensorDevice,
        packet: SensorPacket,
    ) -> SensorPacketRecord:
        quality = packet.quality_score

        if quality is not None:
            device.quality_score = quality

        if (
            quality is not None
            and quality
            < self.quarantine_quality_score
        ):
            return self._quarantine_packet(
                device,
                packet,
                reason="kalite puanı karantina eşiğinin altında",
            )

        if (
            quality is not None
            and quality
            < self.minimum_quality_score
        ):
            return self._reject_packet(
                device,
                packet,
                reason="kalite puanı kabul eşiğinin altında",
            )

        if not packet.payload:
            return self._quarantine_packet(
                device,
                packet,
                reason="boş sensör paketi",
            )

        if packet.session_id is not None:
            self._forward_to_session(
                device=device,
                packet=packet,
            )

        now = self._clock()

        record = SensorPacketRecord(
            packet=packet,
            state=SensorPacketState.ACCEPTED,
            reason=None,
            processed_at=now,
        )

        self._accepted.append(record)

        device.accepted_packet_count += 1
        device.last_packet_at = packet.recorded_at

        self._publish(
            topic="runtime.sensor.packet.accepted",
            device=device,
            extra={
                "packet_id": packet.packet_id,
                "session_id": packet.session_id,
                "evidence_id": packet.evidence_id,
            },
        )

        return record

    def _forward_to_session(
        self,
        *,
        device: SensorDevice,
        packet: SensorPacket,
    ) -> None:
        if self.session_manager is None:
            raise SensorRuntimeError(
                "Oturum bağlantısı için "
                "Session Manager gereklidir."
            )

        session_id = packet.session_id

        assert session_id is not None

        key = (
            session_id,
            device.descriptor.sensor_id,
        )

        stream_id = self._stream_links.get(key)

        if stream_id is None:
            stream = (
                self.session_manager.attach_stream(
                    session_id,
                    stream_type=self._stream_type_for(
                        device.descriptor.sensor_type
                    ),
                    source=(
                        device.descriptor.source
                    ),
                    metadata={
                        "sensor_id": (
                            device.descriptor.sensor_id
                        ),
                        "sensor_name": (
                            device.descriptor.name
                        ),
                    },
                )
            )

            stream_id = stream.stream_id
            self._stream_links[key] = stream_id

        self.session_manager.record_stream_data(
            session_id,
            stream_id,
            byte_count=packet.byte_count,
            frame_count=packet.frame_count,
        )

        if packet.evidence_id is not None:
            session = self.session_manager.get(
                session_id
            )

            already_linked = any(
                link.evidence_id
                == packet.evidence_id
                for link in session.evidence_links
            )

            if not already_linked:
                self.session_manager.link_evidence(
                    session_id,
                    evidence_id=(
                        packet.evidence_id
                    ),
                    evidence_type=(
                        device.descriptor.sensor_type.value
                    ),
                    source_stream_id=stream_id,
                    metadata={
                        "packet_id": packet.packet_id,
                    },
                )

    def _buffer_packet(
        self,
        device: SensorDevice,
        packet: SensorPacket,
        *,
        reason: str,
    ) -> SensorPacketRecord:
        if len(self._buffer) >= self.offline_buffer_limit:
            return self._reject_packet(
                device,
                packet,
                reason="çevrimdışı tampon dolu",
            )

        record = SensorPacketRecord(
            packet=packet,
            state=SensorPacketState.BUFFERED,
            reason=reason,
            processed_at=self._clock(),
        )

        self._buffer.append(record)
        device.buffered_packet_count += 1

        self._publish(
            topic="runtime.sensor.packet.buffered",
            device=device,
            extra={
                "packet_id": packet.packet_id,
                "reason": reason,
            },
        )

        return record

    def _quarantine_packet(
        self,
        device: SensorDevice,
        packet: SensorPacket,
        *,
        reason: str,
    ) -> SensorPacketRecord:
        record = SensorPacketRecord(
            packet=packet,
            state=SensorPacketState.QUARANTINED,
            reason=reason,
            processed_at=self._clock(),
        )

        self._quarantine.append(record)
        device.quarantined_packet_count += 1
        device.last_packet_at = packet.recorded_at

        self._publish(
            topic="runtime.sensor.packet.quarantined",
            device=device,
            extra={
                "packet_id": packet.packet_id,
                "reason": reason,
            },
        )

        return record

    def _reject_packet(
        self,
        device: SensorDevice,
        packet: SensorPacket,
        *,
        reason: str,
    ) -> SensorPacketRecord:
        record = SensorPacketRecord(
            packet=packet,
            state=SensorPacketState.REJECTED,
            reason=reason,
            processed_at=self._clock(),
        )

        self._rejected.append(record)
        device.rejected_packet_count += 1
        device.last_packet_at = packet.recorded_at

        self._publish(
            topic="runtime.sensor.packet.rejected",
            device=device,
            extra={
                "packet_id": packet.packet_id,
                "reason": reason,
            },
        )

        return record

    def _stream_type_for(
        self,
        sensor_type: SensorType,
    ) -> RuntimeStreamType:
        mapping = {
            SensorType.CAMERA: RuntimeStreamType.CAMERA,
            SensorType.PHOTO: RuntimeStreamType.PHOTO,
            SensorType.VIDEO: RuntimeStreamType.VIDEO,
            SensorType.AUDIO: RuntimeStreamType.AUDIO,
            SensorType.SONAR: RuntimeStreamType.SONAR,
            SensorType.GPS: RuntimeStreamType.MAP,
            SensorType.RTK: RuntimeStreamType.MAP,
        }

        return mapping.get(
            sensor_type,
            RuntimeStreamType.SENSOR,
        )

    def _publish(
        self,
        *,
        topic: str,
        device: SensorDevice,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "sensor_id": (
                device.descriptor.sensor_id
            ),
            "sensor_type": (
                device.descriptor.sensor_type.value
            ),
            "connection_state": (
                device.connection_state.value
            ),
        }

        payload.update(extra or {})

        self.event_bus.publish(
            RuntimeEvent(
                topic=topic,
                source="sensor_runtime",
                payload=payload,
            )
        )

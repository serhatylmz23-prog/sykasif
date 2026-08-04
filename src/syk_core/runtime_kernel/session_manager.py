"""SyKaşif canlı çalışma oturumu yönetimi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import RLock
from typing import Any
from uuid import uuid4

from .event_bus import RuntimeEvent, RuntimeEventBus


class RuntimeSessionError(RuntimeError):
    """Canlı oturum yönetim hatası."""


class RuntimeSessionState(str, Enum):
    CREATED = "oluşturuldu"
    STARTING = "başlatılıyor"
    ACTIVE = "aktif"
    PAUSED = "bekliyor"
    STOPPING = "durduruluyor"
    COMPLETED = "tamamlandı"
    TIMED_OUT = "zaman_aşımı"
    FAILED = "hata"


class RuntimeStreamType(str, Enum):
    CAMERA = "kamera"
    PHOTO = "fotoğraf"
    VIDEO = "video"
    AUDIO = "ses"
    SENSOR = "sensör"
    MAP = "harita"
    SONAR = "sonar"
    DRONE = "drone"
    BLUETOOTH = "bluetooth"
    WIFI = "wi-fi"


@dataclass(slots=True, frozen=True)
class RuntimeLocation:
    latitude: float
    longitude: float
    altitude_m: float | None = None
    accuracy_m: float | None = None
    source: str = "bilinmiyor"
    recorded_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(
                "Enlem -90 ile 90 arasında olmalıdır."
            )

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(
                "Boylam -180 ile 180 arasında olmalıdır."
            )

        if (
            self.accuracy_m is not None
            and self.accuracy_m < 0
        ):
            raise ValueError(
                "Konum doğruluğu negatif olamaz."
            )

        if self.recorded_at.tzinfo is None:
            raise ValueError(
                "Konum zamanı saat dilimi içermelidir."
            )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "enlem": self.latitude,
            "boylam": self.longitude,
            "rakım_m": self.altitude_m,
            "doğruluk_m": self.accuracy_m,
            "kaynak": self.source,
            "zaman": self.recorded_at.isoformat(),
        }


@dataclass(slots=True)
class RuntimeStream:
    stream_id: str
    stream_type: RuntimeStreamType
    source: str
    connected_at: datetime
    active: bool = True
    frame_count: int = 0
    byte_count: int = 0
    last_data_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_data(
        self,
        *,
        byte_count: int = 0,
        frame_count: int = 1,
        recorded_at: datetime,
    ) -> None:
        if not self.active:
            raise RuntimeSessionError(
                "Pasif akışa veri eklenemez."
            )

        if byte_count < 0:
            raise ValueError(
                "Bayt sayısı negatif olamaz."
            )

        if frame_count < 0:
            raise ValueError(
                "Kare sayısı negatif olamaz."
            )

        self.byte_count += byte_count
        self.frame_count += frame_count
        self.last_data_at = recorded_at

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "akış_kimliği": self.stream_id,
            "akış_türü": self.stream_type.value,
            "kaynak": self.source,
            "aktif": self.active,
            "kare_sayısı": self.frame_count,
            "bayt_sayısı": self.byte_count,
            "bağlantı_zamanı": (
                self.connected_at.isoformat()
            ),
            "son_veri_zamanı": (
                self.last_data_at.isoformat()
                if self.last_data_at
                else None
            ),
            "veri": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class RuntimeEvidenceLink:
    evidence_id: str
    evidence_type: str
    source_stream_id: str | None
    linked_at: datetime
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "kanıt_kimliği": self.evidence_id,
            "kanıt_türü": self.evidence_type,
            "kaynak_akış": self.source_stream_id,
            "bağlantı_zamanı": (
                self.linked_at.isoformat()
            ),
            "veri": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class RuntimeMapPin:
    pin_id: str
    location: RuntimeLocation
    pin_type: str
    label: str
    confidence: float | None
    created_at: datetime
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if (
            self.confidence is not None
            and not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError(
                "Güven değeri 0 ile 1 arasında olmalıdır."
            )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "pin_kimliği": self.pin_id,
            "pin_türü": self.pin_type,
            "etiket": self.label,
            "güven": self.confidence,
            "oluşturulma_zamanı": (
                self.created_at.isoformat()
            ),
            "konum": self.location.to_runtime_dict(),
            "veri": dict(self.metadata),
        }


@dataclass(slots=True)
class RuntimeSession:
    session_id: str
    name: str
    created_at: datetime
    timeout: timedelta | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    state: RuntimeSessionState = (
        RuntimeSessionState.CREATED
    )
    started_at: datetime | None = None
    paused_at: datetime | None = None
    stopped_at: datetime | None = None
    last_activity_at: datetime | None = None
    pause_count: int = 0
    failure_reason: str | None = None

    streams: dict[str, RuntimeStream] = field(
        default_factory=dict
    )
    evidence_links: list[
        RuntimeEvidenceLink
    ] = field(default_factory=list)
    map_pins: list[RuntimeMapPin] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError(
                "Oturum kimliği boş olamaz."
            )

        if not self.name.strip():
            raise ValueError(
                "Oturum adı boş olamaz."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Oturum zamanı saat dilimi içermelidir."
            )

        if (
            self.timeout is not None
            and self.timeout.total_seconds() <= 0
        ):
            raise ValueError(
                "Oturum zaman aşımı sıfırdan büyük olmalıdır."
            )

    @property
    def is_terminal(self) -> bool:
        return self.state in {
            RuntimeSessionState.COMPLETED,
            RuntimeSessionState.TIMED_OUT,
            RuntimeSessionState.FAILED,
        }

    @property
    def active_stream_count(self) -> int:
        return sum(
            1
            for stream in self.streams.values()
            if stream.active
        )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "oturum_kimliği": self.session_id,
            "ad": self.name,
            "durum": self.state.value,
            "oluşturulma_zamanı": (
                self.created_at.isoformat()
            ),
            "başlangıç_zamanı": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),
            "bekletilme_zamanı": (
                self.paused_at.isoformat()
                if self.paused_at
                else None
            ),
            "bitiş_zamanı": (
                self.stopped_at.isoformat()
                if self.stopped_at
                else None
            ),
            "son_hareket_zamanı": (
                self.last_activity_at.isoformat()
                if self.last_activity_at
                else None
            ),
            "zaman_aşımı_saniye": (
                self.timeout.total_seconds()
                if self.timeout
                else None
            ),
            "bekletme_sayısı": self.pause_count,
            "aktif_akış_sayısı": (
                self.active_stream_count
            ),
            "kanıt_sayısı": len(
                self.evidence_links
            ),
            "harita_pini_sayısı": len(
                self.map_pins
            ),
            "hata": self.failure_reason,
            "akışlar": [
                stream.to_runtime_dict()
                for stream in sorted(
                    self.streams.values(),
                    key=lambda item: item.stream_id,
                )
            ],
            "kanıtlar": [
                evidence.to_runtime_dict()
                for evidence in self.evidence_links
            ],
            "harita_pinleri": [
                pin.to_runtime_dict()
                for pin in self.map_pins
            ],
            "veri": dict(self.metadata),
        }


class RuntimeSessionManager:
    """Canlı saha ve laboratuvar oturumlarını yönetir."""

    def __init__(
        self,
        *,
        event_bus: RuntimeEventBus | None = None,
        clock: callable | None = None,
    ) -> None:
        self.event_bus = event_bus or RuntimeEventBus()
        self._clock = clock or (
            lambda: datetime.now(UTC)
        )
        self._sessions: dict[
            str,
            RuntimeSession,
        ] = {}
        self._active_session_id: str | None = None
        self._lock = RLock()

    def create_session(
        self,
        *,
        name: str,
        timeout: timedelta | None = None,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> RuntimeSession:
        generated_id = (
            session_id
            or "SYK-SESSION-" + uuid4().hex.upper()
        )

        with self._lock:
            if generated_id in self._sessions:
                raise RuntimeSessionError(
                    "Oturum kimliği zaten kayıtlı: "
                    f"{generated_id}"
                )

            session = RuntimeSession(
                session_id=generated_id,
                name=name,
                created_at=self._clock(),
                timeout=timeout,
                metadata=dict(metadata or {}),
            )

            self._sessions[generated_id] = session

        self._publish(
            topic="runtime.session.created",
            session=session,
        )

        return session

    def start(
        self,
        session_id: str,
    ) -> RuntimeSession:
        session = self.get(session_id)

        if session.is_terminal:
            raise RuntimeSessionError(
                "Tamamlanmış oturum yeniden başlatılamaz."
            )

        if session.state is RuntimeSessionState.ACTIVE:
            return session

        if (
            self._active_session_id is not None
            and self._active_session_id != session_id
        ):
            raise RuntimeSessionError(
                "Aynı anda yalnız bir canlı oturum "
                "etkin olabilir."
            )

        now = self._clock()

        session.state = RuntimeSessionState.STARTING
        session.started_at = (
            session.started_at or now
        )
        session.last_activity_at = now
        session.paused_at = None
        session.state = RuntimeSessionState.ACTIVE

        self._active_session_id = session_id

        self._publish(
            topic="runtime.session.started",
            session=session,
        )

        return session

    def pause(
        self,
        session_id: str,
    ) -> RuntimeSession:
        session = self.get(session_id)

        if session.state is not RuntimeSessionState.ACTIVE:
            raise RuntimeSessionError(
                "Yalnız aktif oturum bekletilebilir."
            )

        now = self._clock()

        session.state = RuntimeSessionState.PAUSED
        session.paused_at = now
        session.last_activity_at = now
        session.pause_count += 1

        for stream in session.streams.values():
            stream.active = False

        self._active_session_id = None

        self._publish(
            topic="runtime.session.paused",
            session=session,
        )

        return session

    def resume(
        self,
        session_id: str,
    ) -> RuntimeSession:
        session = self.get(session_id)

        if session.state is not RuntimeSessionState.PAUSED:
            raise RuntimeSessionError(
                "Yalnız bekleyen oturum sürdürülebilir."
            )

        if (
            self._active_session_id is not None
            and self._active_session_id != session_id
        ):
            raise RuntimeSessionError(
                "Başka bir canlı oturum etkin."
            )

        now = self._clock()

        session.state = RuntimeSessionState.ACTIVE
        session.paused_at = None
        session.last_activity_at = now

        self._active_session_id = session_id

        self._publish(
            topic="runtime.session.resumed",
            session=session,
        )

        return session

    def stop(
        self,
        session_id: str,
    ) -> RuntimeSession:
        session = self.get(session_id)

        if session.is_terminal:
            return session

        session.state = RuntimeSessionState.STOPPING

        now = self._clock()

        for stream in session.streams.values():
            stream.active = False

        session.state = RuntimeSessionState.COMPLETED
        session.stopped_at = now
        session.last_activity_at = now

        if self._active_session_id == session_id:
            self._active_session_id = None

        self._publish(
            topic="runtime.session.completed",
            session=session,
        )

        return session

    def fail(
        self,
        session_id: str,
        *,
        reason: str,
    ) -> RuntimeSession:
        session = self.get(session_id)

        if session.is_terminal:
            raise RuntimeSessionError(
                "Tamamlanmış oturum hata durumuna alınamaz."
            )

        now = self._clock()

        for stream in session.streams.values():
            stream.active = False

        session.state = RuntimeSessionState.FAILED
        session.failure_reason = reason
        session.stopped_at = now
        session.last_activity_at = now

        if self._active_session_id == session_id:
            self._active_session_id = None

        self._publish(
            topic="runtime.session.failed",
            session=session,
            extra={"reason": reason},
        )

        return session

    def attach_stream(
        self,
        session_id: str,
        *,
        stream_type: RuntimeStreamType,
        source: str,
        metadata: dict[str, Any] | None = None,
        stream_id: str | None = None,
    ) -> RuntimeStream:
        session = self._require_active_session(
            session_id
        )

        generated_id = (
            stream_id
            or "SYK-STREAM-" + uuid4().hex.upper()
        )

        if generated_id in session.streams:
            raise RuntimeSessionError(
                "Akış kimliği zaten kayıtlı: "
                f"{generated_id}"
            )

        now = self._clock()

        stream = RuntimeStream(
            stream_id=generated_id,
            stream_type=stream_type,
            source=source,
            connected_at=now,
            metadata=dict(metadata or {}),
        )

        session.streams[generated_id] = stream
        session.last_activity_at = now

        self._publish(
            topic="runtime.session.stream.attached",
            session=session,
            extra={
                "stream_id": generated_id,
                "stream_type": stream_type.value,
            },
        )

        return stream

    def detach_stream(
        self,
        session_id: str,
        stream_id: str,
    ) -> RuntimeStream:
        session = self.get(session_id)

        try:
            stream = session.streams[stream_id]
        except KeyError as exc:
            raise RuntimeSessionError(
                f"Akış bulunamadı: {stream_id}"
            ) from exc

        stream.active = False
        session.last_activity_at = self._clock()

        self._publish(
            topic="runtime.session.stream.detached",
            session=session,
            extra={"stream_id": stream_id},
        )

        return stream

    def record_stream_data(
        self,
        session_id: str,
        stream_id: str,
        *,
        byte_count: int = 0,
        frame_count: int = 1,
    ) -> RuntimeStream:
        session = self._require_active_session(
            session_id
        )

        try:
            stream = session.streams[stream_id]
        except KeyError as exc:
            raise RuntimeSessionError(
                f"Akış bulunamadı: {stream_id}"
            ) from exc

        now = self._clock()

        stream.add_data(
            byte_count=byte_count,
            frame_count=frame_count,
            recorded_at=now,
        )

        session.last_activity_at = now

        self._publish(
            topic="runtime.session.stream.data",
            session=session,
            extra={
                "stream_id": stream_id,
                "byte_count": byte_count,
                "frame_count": frame_count,
            },
        )

        return stream

    def link_evidence(
        self,
        session_id: str,
        *,
        evidence_id: str,
        evidence_type: str,
        source_stream_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeEvidenceLink:
        session = self.get(session_id)

        if source_stream_id is not None:
            if source_stream_id not in session.streams:
                raise RuntimeSessionError(
                    "Kanıtın kaynak akışı bulunamadı: "
                    f"{source_stream_id}"
                )

        if any(
            item.evidence_id == evidence_id
            for item in session.evidence_links
        ):
            raise RuntimeSessionError(
                "Kanıt zaten oturuma bağlı: "
                f"{evidence_id}"
            )

        now = self._clock()

        link = RuntimeEvidenceLink(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            source_stream_id=source_stream_id,
            linked_at=now,
            metadata=dict(metadata or {}),
        )

        session.evidence_links.append(link)
        session.last_activity_at = now

        self._publish(
            topic="runtime.session.evidence.linked",
            session=session,
            extra={
                "evidence_id": evidence_id,
                "evidence_type": evidence_type,
            },
        )

        return link

    def add_map_pin(
        self,
        session_id: str,
        *,
        location: RuntimeLocation,
        pin_type: str,
        label: str,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
        pin_id: str | None = None,
    ) -> RuntimeMapPin:
        session = self.get(session_id)

        generated_id = (
            pin_id
            or "SYK-PIN-" + uuid4().hex.upper()
        )

        if any(
            pin.pin_id == generated_id
            for pin in session.map_pins
        ):
            raise RuntimeSessionError(
                "Harita pini zaten kayıtlı: "
                f"{generated_id}"
            )

        now = self._clock()

        pin = RuntimeMapPin(
            pin_id=generated_id,
            location=location,
            pin_type=pin_type,
            label=label,
            confidence=confidence,
            created_at=now,
            metadata=dict(metadata or {}),
        )

        session.map_pins.append(pin)
        session.last_activity_at = now

        self._publish(
            topic="runtime.session.map_pin.created",
            session=session,
            extra={
                "pin_id": generated_id,
                "pin_type": pin_type,
            },
        )

        return pin

    def expire_timed_out_sessions(
        self,
        *,
        now: datetime | None = None,
    ) -> tuple[RuntimeSession, ...]:
        current = now or self._clock()
        expired: list[RuntimeSession] = []

        for session in self._sessions.values():
            if session.is_terminal:
                continue

            if session.timeout is None:
                continue

            reference = (
                session.last_activity_at
                or session.created_at
            )

            if current - reference < session.timeout:
                continue

            for stream in session.streams.values():
                stream.active = False

            session.state = RuntimeSessionState.TIMED_OUT
            session.stopped_at = current

            if self._active_session_id == session.session_id:
                self._active_session_id = None

            expired.append(session)

            self._publish(
                topic="runtime.session.timed_out",
                session=session,
            )

        return tuple(expired)

    def get(
        self,
        session_id: str,
    ) -> RuntimeSession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise RuntimeSessionError(
                f"Oturum bulunamadı: {session_id}"
            ) from exc

    def list_sessions(
        self,
    ) -> tuple[RuntimeSession, ...]:
        return tuple(
            self._sessions[session_id]
            for session_id in sorted(self._sessions)
        )

    def snapshot(
        self,
    ) -> dict[str, Any]:
        sessions = self.list_sessions()

        return {
            "toplam_oturum_sayısı": len(sessions),
            "aktif_oturum_kimliği": (
                self._active_session_id
            ),
            "aktif_oturum_sayısı": sum(
                1
                for session in sessions
                if session.state
                is RuntimeSessionState.ACTIVE
            ),
            "tamamlanan_oturum_sayısı": sum(
                1
                for session in sessions
                if session.state
                is RuntimeSessionState.COMPLETED
            ),
            "zaman_aşımı_oturum_sayısı": sum(
                1
                for session in sessions
                if session.state
                is RuntimeSessionState.TIMED_OUT
            ),
            "hatalı_oturum_sayısı": sum(
                1
                for session in sessions
                if session.state
                is RuntimeSessionState.FAILED
            ),
            "oturumlar": [
                session.to_runtime_dict()
                for session in sessions
            ],
        }

    def _require_active_session(
        self,
        session_id: str,
    ) -> RuntimeSession:
        session = self.get(session_id)

        if session.state is not RuntimeSessionState.ACTIVE:
            raise RuntimeSessionError(
                "İşlem için oturum aktif olmalıdır."
            )

        return session

    def _publish(
        self,
        *,
        topic: str,
        session: RuntimeSession,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "session_id": session.session_id,
            "name": session.name,
            "state": session.state.value,
        }

        payload.update(extra or {})

        self.event_bus.publish(
            RuntimeEvent(
                topic=topic,
                source="runtime_session_manager",
                payload=payload,
            )
        )

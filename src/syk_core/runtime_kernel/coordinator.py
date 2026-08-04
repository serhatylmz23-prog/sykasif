"""SyKaşif ortak çalışma zamanı koordinatörü."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from .evidence_runtime import (
    EvidenceRecord,
    EvidenceReportBlock,
    EvidenceRuntime,
)
from .event_bus import RuntimeEvent, RuntimeEventBus
from .runtime import RuntimeKernel
from .scheduler import RuntimeScheduler
from .sensor_runtime import (
    SensorDescriptor,
    SensorPacketState,
    SensorRuntime,
)
from .session_manager import (
    RuntimeLocation,
    RuntimeMapPin,
    RuntimeSession,
    RuntimeSessionManager,
)


class RuntimeCoordinatorError(RuntimeError):
    """Çalışma zamanı koordinatörü hatası."""


class RuntimeCoordinatorState(str, Enum):
    CREATED = "oluşturuldu"
    STARTING = "başlatılıyor"
    RUNNING = "çalışıyor"
    DEGRADED = "kısmi_çalışıyor"
    STOPPING = "durduruluyor"
    STOPPED = "durdu"
    FAILED = "hata"


@dataclass(slots=True, frozen=True)
class RuntimeCoordinatorIssue:
    component: str
    severity: str
    message: str
    occurred_at: datetime
    recoverable: bool = True
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "bileşen": self.component,
            "önem": self.severity,
            "açıklama": self.message,
            "zaman": self.occurred_at.isoformat(),
            "kurtarılabilir": self.recoverable,
            "veri": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class RuntimeFlowResult:
    session_id: str
    sensor_id: str
    packet_id: str
    packet_state: str
    evidence_id: str | None
    evidence_state: str | None
    report_block_id: str | None
    completed_at: datetime

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "oturum_kimliği": self.session_id,
            "sensör_kimliği": self.sensor_id,
            "paket_kimliği": self.packet_id,
            "paket_durumu": self.packet_state,
            "kanıt_kimliği": self.evidence_id,
            "kanıt_durumu": self.evidence_state,
            "rapor_bloğu_kimliği": (
                self.report_block_id
            ),
            "tamamlanma_zamanı": (
                self.completed_at.isoformat()
            ),
        }


class RuntimeCoordinator:
    """Runtime bileşenlerini tek çalışma akışında birleştirir."""

    def __init__(
        self,
        *,
        event_bus: RuntimeEventBus | None = None,
        kernel: RuntimeKernel | None = None,
        scheduler: RuntimeScheduler | None = None,
        session_manager: RuntimeSessionManager | None = None,
        sensor_runtime: SensorRuntime | None = None,
        evidence_runtime: EvidenceRuntime | None = None,
        clock: Any | None = None,
    ) -> None:
        self.event_bus = event_bus or RuntimeEventBus()
        self._clock = clock or (
            lambda: datetime.now(UTC)
        )

        self.kernel = kernel or RuntimeKernel(
            event_bus=self.event_bus
        )

        self.scheduler = scheduler or RuntimeScheduler(
            event_bus=self.event_bus,
            clock=self._clock,
        )

        self.session_manager = (
            session_manager
            or RuntimeSessionManager(
                event_bus=self.event_bus,
                clock=self._clock,
            )
        )

        self.sensor_runtime = (
            sensor_runtime
            or SensorRuntime(
                event_bus=self.event_bus,
                session_manager=self.session_manager,
                clock=self._clock,
            )
        )

        self.evidence_runtime = (
            evidence_runtime
            or EvidenceRuntime(
                event_bus=self.event_bus,
                session_manager=self.session_manager,
                clock=self._clock,
            )
        )

        self.state = RuntimeCoordinatorState.CREATED
        self.started_at: datetime | None = None
        self.stopped_at: datetime | None = None
        self.last_activity_at: datetime | None = None

        self._issues: list[
            RuntimeCoordinatorIssue
        ] = []

        self._flow_history: list[
            RuntimeFlowResult
        ] = []

    def start(self) -> None:
        if self.state is RuntimeCoordinatorState.RUNNING:
            return

        if self.state is RuntimeCoordinatorState.STARTING:
            raise RuntimeCoordinatorError(
                "Koordinatör zaten başlatılıyor."
            )

        self.state = RuntimeCoordinatorState.STARTING

        try:
            self.kernel.start()

            now = self._clock()

            self.started_at = self.started_at or now
            self.stopped_at = None
            self.last_activity_at = now
            self.state = RuntimeCoordinatorState.RUNNING

            self._publish(
                topic="runtime.coordinator.started",
                payload={
                    "started_at": now.isoformat(),
                },
            )

        except Exception as exc:
            self.state = RuntimeCoordinatorState.FAILED

            self._record_issue(
                component="runtime_kernel",
                severity="kritik",
                message=str(exc),
                recoverable=True,
            )

            raise RuntimeCoordinatorError(
                f"Koordinatör başlatılamadı: {exc}"
            ) from exc

    def stop(self) -> None:
        if self.state is RuntimeCoordinatorState.STOPPED:
            return

        self.state = RuntimeCoordinatorState.STOPPING
        errors: list[str] = []

        for session in self.session_manager.list_sessions():
            if session.is_terminal:
                continue

            try:
                self.session_manager.stop(
                    session.session_id
                )
            except Exception as exc:
                errors.append(
                    f"oturum:{session.session_id}:{exc}"
                )

        for sensor in self.sensor_runtime.list_sensors():
            try:
                self.sensor_runtime.disconnect(
                    sensor.descriptor.sensor_id,
                    reason="Koordinatör güvenli kapanışı",
                )
            except Exception as exc:
                errors.append(
                    "sensör:"
                    f"{sensor.descriptor.sensor_id}:{exc}"
                )

        try:
            self.kernel.stop()
        except Exception as exc:
            errors.append(
                f"çekirdek:{exc}"
            )

        now = self._clock()
        self.stopped_at = now
        self.last_activity_at = now

        if errors:
            self.state = RuntimeCoordinatorState.FAILED

            for error in errors:
                self._record_issue(
                    component="güvenli_kapanış",
                    severity="kritik",
                    message=error,
                    recoverable=True,
                )

            self._publish(
                topic=(
                    "runtime.coordinator.stop_failed"
                ),
                payload={"errors": errors},
            )

            raise RuntimeCoordinatorError(
                "Koordinatör güvenli kapatılamadı: "
                + " | ".join(errors)
            )

        self.state = RuntimeCoordinatorState.STOPPED

        self._publish(
            topic="runtime.coordinator.stopped",
            payload={
                "stopped_at": now.isoformat(),
            },
        )

    def register_sensor(
        self,
        descriptor: SensorDescriptor,
        *,
        connect: bool = True,
    ) -> None:
        self._require_running()

        self.sensor_runtime.register_sensor(
            descriptor
        )

        if connect:
            self.sensor_runtime.connect(
                descriptor.sensor_id
            )

        self.last_activity_at = self._clock()

    def create_live_session(
        self,
        *,
        name: str,
        timeout: timedelta | None = None,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> RuntimeSession:
        self._require_running()

        session = self.session_manager.create_session(
            name=name,
            timeout=timeout,
            metadata=metadata,
            session_id=session_id,
        )

        self.session_manager.start(
            session.session_id
        )

        self.last_activity_at = self._clock()

        return session

    def add_session_pin(
        self,
        session_id: str,
        *,
        location: RuntimeLocation,
        pin_type: str,
        label: str,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeMapPin:
        self._require_running()

        pin = self.session_manager.add_map_pin(
            session_id,
            location=location,
            pin_type=pin_type,
            label=label,
            confidence=confidence,
            metadata=metadata,
        )

        self.last_activity_at = self._clock()

        return pin

    def process_sensor_data(
        self,
        *,
        session_id: str,
        sensor_id: str,
        payload: dict[str, Any],
        evidence_type: str,
        evidence_title: str,
        quality_score: float | None = None,
        byte_count: int = 0,
        frame_count: int = 1,
        metadata: dict[str, Any] | None = None,
        create_report_block: bool = True,
    ) -> RuntimeFlowResult:
        self._require_running()

        packet_record = (
            self.sensor_runtime.submit_packet(
                sensor_id=sensor_id,
                payload=payload,
                quality_score=quality_score,
                byte_count=byte_count,
                frame_count=frame_count,
                session_id=session_id,
                metadata=metadata,
            )
        )

        evidence: EvidenceRecord | None = None
        report_block: EvidenceReportBlock | None = None

        if packet_record.state not in {
            SensorPacketState.REJECTED,
            SensorPacketState.BUFFERED,
        }:
            try:
                evidence = (
                    self.evidence_runtime
                    .create_from_sensor_packet(
                        packet_record,
                        evidence_type=evidence_type,
                        title=evidence_title,
                        metadata=metadata,
                    )
                )

                if create_report_block:
                    report_block = (
                        self.evidence_runtime
                        .create_report_block(
                            evidence.evidence_id,
                            block_type=evidence_type,
                        )
                    )

            except Exception as exc:
                self.state = (
                    RuntimeCoordinatorState.DEGRADED
                )

                self._record_issue(
                    component="evidence_runtime",
                    severity="yüksek",
                    message=str(exc),
                    recoverable=True,
                    metadata={
                        "packet_id": (
                            packet_record
                            .packet
                            .packet_id
                        ),
                    },
                )

                self._publish(
                    topic=(
                        "runtime.coordinator."
                        "evidence_flow_failed"
                    ),
                    payload={
                        "packet_id": (
                            packet_record
                            .packet
                            .packet_id
                        ),
                        "error": str(exc),
                    },
                )

        result = RuntimeFlowResult(
            session_id=session_id,
            sensor_id=sensor_id,
            packet_id=(
                packet_record.packet.packet_id
            ),
            packet_state=(
                packet_record.state.value
            ),
            evidence_id=(
                evidence.evidence_id
                if evidence
                else None
            ),
            evidence_state=(
                evidence.state.value
                if evidence
                else None
            ),
            report_block_id=(
                report_block.block_id
                if report_block
                else None
            ),
            completed_at=self._clock(),
        )

        self._flow_history.append(result)
        self.last_activity_at = result.completed_at

        self._publish(
            topic=(
                "runtime.coordinator.flow.completed"
            ),
            payload=result.to_runtime_dict(),
        )

        return result

    def run_scheduled_tasks(
        self,
        *,
        now: datetime | None = None,
        limit: int | None = None,
    ) -> int:
        self._require_running()

        records = self.scheduler.run_due(
            now=now,
            limit=limit,
        )

        self.last_activity_at = self._clock()

        return len(records)

    def check_timeouts(
        self,
        *,
        now: datetime | None = None,
    ) -> int:
        self._require_running()

        expired = (
            self.session_manager
            .expire_timed_out_sessions(
                now=now
            )
        )

        if expired:
            self._record_issue(
                component="session_manager",
                severity="uyarı",
                message=(
                    f"{len(expired)} oturum "
                    "zaman aşımına uğradı."
                ),
                recoverable=True,
                metadata={
                    "session_ids": [
                        session.session_id
                        for session in expired
                    ],
                },
            )

        return len(expired)

    def approve_evidence(
        self,
        evidence_id: str,
        *,
        actor: str,
        seal: bool = False,
        seal_actor: str | None = None,
    ) -> EvidenceRecord:
        self._require_running()

        record = self.evidence_runtime.approve(
            evidence_id,
            actor=actor,
        )

        if seal:
            record = self.evidence_runtime.seal(
                evidence_id,
                actor=seal_actor or actor,
            )

        self.last_activity_at = self._clock()

        return record

    def recover(self) -> None:
        if self.state not in {
            RuntimeCoordinatorState.DEGRADED,
            RuntimeCoordinatorState.FAILED,
            RuntimeCoordinatorState.STOPPED,
        }:
            raise RuntimeCoordinatorError(
                "Koordinatör kurtarma gerektiren "
                "durumda değil."
            )

        recovery_errors: list[str] = []

        try:
            if self.kernel.state.value != "çalışıyor":
                self.kernel.start()
        except Exception as exc:
            recovery_errors.append(
                f"çekirdek:{exc}"
            )

        for sensor in self.sensor_runtime.list_sensors():
            if sensor.connection_state.value not in {
                "çevrimdışı",
                "bağlantı_kesildi",
                "hata",
            }:
                continue

            try:
                self.sensor_runtime.reconnect(
                    sensor.descriptor.sensor_id
                )
            except Exception as exc:
                recovery_errors.append(
                    "sensör:"
                    f"{sensor.descriptor.sensor_id}:"
                    f"{exc}"
                )

        if recovery_errors:
            self.state = RuntimeCoordinatorState.FAILED

            self._record_issue(
                component="durum_kurtarma",
                severity="kritik",
                message=" | ".join(
                    recovery_errors
                ),
                recoverable=True,
            )

            raise RuntimeCoordinatorError(
                "Durum kurtarma başarısız: "
                + " | ".join(recovery_errors)
            )

        self.state = RuntimeCoordinatorState.RUNNING
        self.last_activity_at = self._clock()

        self._publish(
            topic="runtime.coordinator.recovered",
            payload={
                "recovered_at": (
                    self.last_activity_at.isoformat()
                ),
            },
        )

    def health_snapshot(self) -> dict[str, Any]:
        kernel_health = (
            self.kernel
            .health_report()
            .to_runtime_dict()
        )

        critical_issue_count = sum(
            1
            for issue in self._issues
            if issue.severity == "kritik"
        )

        healthy = (
            self.state
            in {
                RuntimeCoordinatorState.RUNNING,
                RuntimeCoordinatorState.DEGRADED,
            }
            and critical_issue_count == 0
            and kernel_health[
                "hatalı_modül_sayısı"
            ] == 0
        )

        return {
            "koordinatör_durumu": self.state.value,
            "sağlıklı": healthy,
            "kritik_sorun_sayısı": (
                critical_issue_count
            ),
            "toplam_sorun_sayısı": len(
                self._issues
            ),
            "akış_sayısı": len(
                self._flow_history
            ),
            "başlangıç_zamanı": (
                self.started_at.isoformat()
                if self.started_at
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
            "çekirdek": kernel_health,
            "görev_planlayıcı": (
                self.scheduler.snapshot()
            ),
            "oturum_yöneticisi": (
                self.session_manager.snapshot()
            ),
            "sensör_motoru": (
                self.sensor_runtime.snapshot()
            ),
            "kanıt_motoru": (
                self.evidence_runtime.snapshot()
            ),
            "sorunlar": [
                issue.to_runtime_dict()
                for issue in self._issues
            ],
            "akış_geçmişi": [
                flow.to_runtime_dict()
                for flow in self._flow_history
            ],
        }

    @property
    def issues(
        self,
    ) -> tuple[RuntimeCoordinatorIssue, ...]:
        return tuple(self._issues)

    @property
    def flow_history(
        self,
    ) -> tuple[RuntimeFlowResult, ...]:
        return tuple(self._flow_history)

    def _require_running(self) -> None:
        if self.state not in {
            RuntimeCoordinatorState.RUNNING,
            RuntimeCoordinatorState.DEGRADED,
        }:
            raise RuntimeCoordinatorError(
                "İşlem için koordinatör çalışıyor "
                "olmalıdır."
            )

    def _record_issue(
        self,
        *,
        component: str,
        severity: str,
        message: str,
        recoverable: bool,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeCoordinatorIssue:
        issue = RuntimeCoordinatorIssue(
            component=component,
            severity=severity,
            message=message,
            occurred_at=self._clock(),
            recoverable=recoverable,
            metadata=dict(metadata or {}),
        )

        self._issues.append(issue)

        self._publish(
            topic="runtime.coordinator.issue",
            payload=issue.to_runtime_dict(),
        )

        return issue

    def _publish(
        self,
        *,
        topic: str,
        payload: dict[str, Any],
    ) -> None:
        self.event_bus.publish(
            RuntimeEvent(
                topic=topic,
                source="runtime_coordinator",
                payload=payload,
            )
        )

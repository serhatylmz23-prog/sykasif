"""Canlı analiz oturum anlık görüntüsü."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..deserialization import (
    location_from_dict,
    parse_datetime,
)
from ..ecosystem import (
    EcosystemRuntimeContext,
    SalinityType,
    WaterBodyType,
)
from ..live_analysis import (
    DetectionHistoryRecord,
    DetectionState,
    LiveAnalysisSession,
    LiveSessionState,
)
from ..utils import json_safe, utc_now


@dataclass(slots=True)
class LiveSessionSnapshot:
    """Canlı analiz oturumunun geri yüklenebilir kaydı."""

    session_id: str
    state: LiveSessionState
    context: dict[str, Any]
    history_records: tuple[
        dict[str, Any],
        ...,
    ]
    processed_frame_count: int
    failed_frame_count: int
    queued_frame_count: int
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None
    snapshot_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.session_id = self.session_id.strip()

        if not self.session_id:
            raise ValueError(
                "Canlı oturum görüntüsü kimliği boş olamaz."
            )

        for name in (
            "processed_frame_count",
            "failed_frame_count",
            "queued_frame_count",
        ):
            value = int(getattr(self, name))

            if value < 0:
                raise ValueError(
                    f"{name} negatif olamaz."
                )

            setattr(self, name, value)

    @classmethod
    def from_session(
        cls,
        session: LiveAnalysisSession,
    ) -> "LiveSessionSnapshot":
        runtime = session.to_runtime_dict()

        return cls(
            session_id=session.session_id,
            state=session.state,
            context=session.context.to_dict(),
            history_records=tuple(
                record.to_dict()
                for record in session.history.all()
            ),
            processed_frame_count=(
                session.processed_frame_count
            ),
            failed_frame_count=(
                session.failed_frame_count
            ),
            queued_frame_count=len(
                session.frame_queue
            ),
            created_at=session.created_at,
            started_at=session.started_at,
            stopped_at=session.stopped_at,
            metadata={
                **session.metadata,
                "runtime_summary": runtime,
                "dynamic": True,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "session_id": self.session_id,
                "state": self.state,
                "context": self.context,
                "history_records": list(
                    self.history_records
                ),
                "processed_frame_count": (
                    self.processed_frame_count
                ),
                "failed_frame_count": (
                    self.failed_frame_count
                ),
                "queued_frame_count": (
                    self.queued_frame_count
                ),
                "created_at": self.created_at,
                "started_at": self.started_at,
                "stopped_at": self.stopped_at,
                "snapshot_at": self.snapshot_at,
                "metadata": self.metadata,
            }
        )

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "LiveSessionSnapshot":
        created_at = parse_datetime(
            payload.get("created_at")
        )
        snapshot_at = parse_datetime(
            payload.get("snapshot_at")
        )

        if created_at is None:
            raise ValueError(
                "Oturum oluşturma zamanı bulunamadı."
            )

        if snapshot_at is None:
            raise ValueError(
                "Anlık görüntü zamanı bulunamadı."
            )

        return cls(
            session_id=str(payload["session_id"]),
            state=LiveSessionState(
                payload["state"]
            ),
            context=dict(payload["context"]),
            history_records=tuple(
                dict(item)
                for item in (
                    payload.get(
                        "history_records"
                    )
                    or []
                )
            ),
            processed_frame_count=int(
                payload.get(
                    "processed_frame_count",
                    0,
                )
            ),
            failed_frame_count=int(
                payload.get(
                    "failed_frame_count",
                    0,
                )
            ),
            queued_frame_count=int(
                payload.get(
                    "queued_frame_count",
                    0,
                )
            ),
            created_at=created_at,
            started_at=parse_datetime(
                payload.get("started_at")
            ),
            stopped_at=parse_datetime(
                payload.get("stopped_at")
            ),
            snapshot_at=snapshot_at,
            metadata=dict(
                payload.get("metadata") or {}
            ),
        )


def _context_from_dict(
    payload: dict[str, Any],
) -> EcosystemRuntimeContext:
    observed_at = parse_datetime(
        payload.get("gözlem_zamanı")
    )

    if observed_at is None:
        observed_at = utc_now()

    return EcosystemRuntimeContext(
        location=location_from_dict(
            payload["konum"]
        ),
        region_code=str(
            payload["bölge_kodu"]
        ),
        region_name=str(
            payload["bölge_adı"]
        ),
        observed_at=observed_at,
        salinity=SalinityType(
            payload.get(
                "tuzluluk",
                SalinityType.UNKNOWN.value,
            )
        ),
        water_body_type=WaterBodyType(
            payload.get(
                "su_kütlesi_türü",
                WaterBodyType.UNKNOWN.value,
            )
        ),
        water_body_name=payload.get(
            "su_kütlesi_adı"
        ),
        depth_m=payload.get("derinlik_m"),
        water_temperature_c=payload.get(
            "su_sıcaklığı_c"
        ),
        dissolved_oxygen_mg_l=payload.get(
            "çözünmüş_oksijen_mg_l"
        ),
        ph_value=payload.get("ph"),
        conductivity_us_cm=payload.get(
            "iletkenlik_us_cm"
        ),
        altitude_m=payload.get("rakım_m"),
        air_temperature_c=payload.get(
            "hava_sıcaklığı_c"
        ),
        soil_moisture_percent=payload.get(
            "toprak_nemi_yüzde"
        ),
        relative_humidity_percent=payload.get(
            "bağıl_nem_yüzde"
        ),
        slope_degree=payload.get(
            "eğim_derece"
        ),
        online_available=bool(
            payload.get("çevrimiçi", False)
        ),
        device_data_available=bool(
            payload.get("cihaz_verisi", False)
        ),
        metadata=dict(
            payload.get("üst_veri") or {}
        ),
    )


def _history_record_from_dict(
    payload: dict[str, Any],
) -> DetectionHistoryRecord:
    detected_at = parse_datetime(
        payload.get("detected_at")
    )

    if detected_at is None:
        detected_at = utc_now()

    return DetectionHistoryRecord(
        record_id=str(payload["record_id"]),
        entity_type=str(
            payload["entity_type"]
        ),
        detected_label=str(
            payload["detected_label"]
        ),
        confidence_score=float(
            payload["confidence_score"]
        ),
        location=location_from_dict(
            payload["location"]
        ),
        frame_id=str(payload["frame_id"]),
        detected_at=detected_at,
        state=DetectionState(
            payload["state"]
        ),
        track_id=payload.get("track_id"),
        species_id=payload.get("species_id"),
        evidence_ids=set(
            payload.get("evidence_ids") or []
        ),
        metadata=dict(
            payload.get("metadata") or {}
        ),
    )


def restore_live_session(
    snapshot: LiveSessionSnapshot,
    *,
    queue_capacity: int = 120,
) -> LiveAnalysisSession:
    """Kaydedilmiş anlık görüntüden oturumu geri yükler."""

    context = _context_from_dict(
        snapshot.context
    )

    session = LiveAnalysisSession(
        context=context,
        queue_capacity=queue_capacity,
        session_id=snapshot.session_id,
    )

    session.created_at = snapshot.created_at
    session.started_at = snapshot.started_at
    session.stopped_at = snapshot.stopped_at
    session.processed_frame_count = (
        snapshot.processed_frame_count
    )
    session.failed_frame_count = (
        snapshot.failed_frame_count
    )
    session.metadata = dict(
        snapshot.metadata
    )
    session.metadata[
        "restored_from_snapshot"
    ] = True
    session.metadata[
        "previous_queued_frame_count"
    ] = snapshot.queued_frame_count

    for record_payload in (
        snapshot.history_records
    ):
        session.history.add(
            _history_record_from_dict(
                record_payload
            )
        )

    if snapshot.state in {
        LiveSessionState.ACTIVE,
        LiveSessionState.STARTING,
    }:
        session.state = LiveSessionState.PAUSED
        session.metadata[
            "restore_reason"
        ] = (
            "Aktif oturum güvenli geri yükleme "
            "nedeniyle duraklatıldı."
        )
    else:
        session.state = snapshot.state

    return session

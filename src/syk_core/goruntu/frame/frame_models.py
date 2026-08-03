from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FrameSourceKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    LIVE = "live"


class FrameStatus(StrEnum):
    CANDIDATE = "candidate"
    PREVIEW = "preview"


@dataclass(frozen=True, slots=True)
class FramePacket:
    media_id: str
    source_kind: FrameSourceKind | str
    frame_index: int
    timestamp_ms: int
    frame_width: int
    frame_height: int
    payload: bytes
    source_name: str = ""
    source_sha256: str | None = None

    def __post_init__(self) -> None:
        media_id = self.media_id.strip()

        if not media_id:
            raise ValueError(
                "Görüntü kimliği boş olamaz."
            )

        try:
            source_kind = FrameSourceKind(
                self.source_kind
            )
        except ValueError as error:
            raise ValueError(
                "Kaynak türü image, video "
                "veya live olmalıdır."
            ) from error

        if self.frame_index < 0:
            raise ValueError(
                "Kare numarası negatif olamaz."
            )

        if self.timestamp_ms < 0:
            raise ValueError(
                "Zaman damgası negatif olamaz."
            )

        if (
            self.frame_width <= 0
            or self.frame_height <= 0
        ):
            raise ValueError(
                "Kare boyutları sıfırdan "
                "büyük olmalıdır."
            )

        if not isinstance(
            self.payload,
            bytes,
        ):
            raise TypeError(
                "Kare içeriği bytes olmalıdır."
            )

        if not self.payload:
            raise ValueError(
                "Kare içeriği boş olamaz."
            )

        if self.source_sha256 is not None:
            normalized_hash = (
                self.source_sha256
                .strip()
                .lower()
            )

            if (
                len(normalized_hash) != 64
                or any(
                    character
                    not in "0123456789abcdef"
                    for character
                    in normalized_hash
                )
            ):
                raise ValueError(
                    "Kaynak SHA-256 değeri "
                    "64 karakterlik onaltılık "
                    "bir değer olmalıdır."
                )

            object.__setattr__(
                self,
                "source_sha256",
                normalized_hash,
            )

        object.__setattr__(
            self,
            "media_id",
            media_id,
        )

        object.__setattr__(
            self,
            "source_kind",
            source_kind,
        )


@dataclass(frozen=True, slots=True)
class FrameRecord:
    frame_id: str
    media_id: str
    source_kind: FrameSourceKind
    frame_index: int
    timestamp_ms: int
    frame_width: int
    frame_height: int
    payload_size: int
    frame_sha256: str
    source_sha256: str
    status: FrameStatus
    created_at: str

    def as_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "media_id": self.media_id,
            "source_kind": (
                self.source_kind.value
            ),
            "frame_index": self.frame_index,
            "timestamp_ms": self.timestamp_ms,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "payload_size": self.payload_size,
            "frame_sha256": (
                self.frame_sha256
            ),
            "source_sha256": (
                self.source_sha256
            ),
            "status": self.status.value,
            "created_at": self.created_at,
            "analysis_scope": (
                "digital_frame_candidate"
            ),
            "field_validation_required": True,
            "maximum_digital_confidence": 99.9,
        }


@dataclass(frozen=True, slots=True)
class FrameIngestionResult:
    record: FrameRecord
    duplicate: bool
    duplicate_of: str | None

    def as_dict(self) -> dict:
        return {
            "record": self.record.as_dict(),
            "duplicate": self.duplicate,
            "duplicate_of": (
                self.duplicate_of
            ),
        }
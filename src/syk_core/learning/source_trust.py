"""Araştırma kaynağı ve güven değerlendirmesi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..utils import json_safe, utc_now
from .enums import SourceTrustLevel


@dataclass(slots=True)
class ResearchSource:
    """Öğrenme adayını destekleyen araştırma kaynağı."""

    source_id: str
    title: str
    publisher: str
    source_type: str
    uri: str | None = None
    published_at: datetime | None = None
    accessed_at: datetime = field(default_factory=utc_now)
    authority_score: float = 50.0
    methodology_score: float = 50.0
    transparency_score: float = 50.0
    corroboration_score: float = 50.0
    recency_score: float = 50.0
    conflict_of_interest: bool = False
    peer_reviewed: bool = False
    official_source: bool = False
    primary_source: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source_id = self.source_id.strip()
        self.title = self.title.strip()
        self.publisher = self.publisher.strip()
        self.source_type = self.source_type.strip()

        if not self.source_id:
            raise ValueError("Kaynak kimliği boş olamaz.")

        if not self.title:
            raise ValueError("Kaynak başlığı boş olamaz.")

        if not self.publisher:
            raise ValueError("Kaynak yayıncısı boş olamaz.")

        if not self.source_type:
            raise ValueError("Kaynak türü boş olamaz.")

        for field_name in (
            "authority_score",
            "methodology_score",
            "transparency_score",
            "corroboration_score",
            "recency_score",
        ):
            value = float(getattr(self, field_name))

            if not 0.0 <= value <= 100.0:
                raise ValueError(
                    f"{field_name} 0 ile 100 arasında olmalıdır."
                )

            setattr(self, field_name, value)

        if self.published_at is not None:
            if self.published_at.tzinfo is None:
                self.published_at = self.published_at.replace(
                    tzinfo=UTC
                )
            else:
                self.published_at = self.published_at.astimezone(
                    UTC
                )

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "source_id": self.source_id,
                "title": self.title,
                "publisher": self.publisher,
                "source_type": self.source_type,
                "uri": self.uri,
                "published_at": self.published_at,
                "accessed_at": self.accessed_at,
                "authority_score": self.authority_score,
                "methodology_score": self.methodology_score,
                "transparency_score": self.transparency_score,
                "corroboration_score": self.corroboration_score,
                "recency_score": self.recency_score,
                "conflict_of_interest": self.conflict_of_interest,
                "peer_reviewed": self.peer_reviewed,
                "official_source": self.official_source,
                "primary_source": self.primary_source,
                "metadata": self.metadata,
            }
        )


@dataclass(slots=True, frozen=True)
class SourceTrustResult:
    """Kaynak güven değerlendirmesi."""

    source_id: str
    score: float
    level: SourceTrustLevel
    accepted: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kaynak_kimliği": self.source_id,
            "güven_skoru": self.score,
            "güven_düzeyi": self.level.value,
            "kabul_edildi": self.accepted,
            "gerekçeler": list(self.reasons),
            "uyarılar": list(self.warnings),
        }


class SourceTrustEngine:
    """Araştırma kaynaklarını kanıta dayalı puanlar."""

    def __init__(
        self,
        *,
        minimum_acceptance_score: float = 55.0,
    ) -> None:
        self.minimum_acceptance_score = float(
            minimum_acceptance_score
        )

        if not 0.0 <= self.minimum_acceptance_score <= 100.0:
            raise ValueError(
                "Kaynak kabul eşiği 0 ile 100 arasında olmalıdır."
            )

    def evaluate(
        self,
        source: ResearchSource,
    ) -> SourceTrustResult:
        reasons: list[str] = []
        warnings: list[str] = []

        score = (
            source.authority_score * 0.25
            + source.methodology_score * 0.25
            + source.transparency_score * 0.15
            + source.corroboration_score * 0.20
            + source.recency_score * 0.15
        )

        if source.official_source:
            score += 7.0
            reasons.append("Resmî kaynak desteği.")

        if source.peer_reviewed:
            score += 6.0
            reasons.append("Hakemli yayın desteği.")

        if source.primary_source:
            score += 4.0
            reasons.append("Birincil kaynak.")

        if source.conflict_of_interest:
            score -= 12.0
            warnings.append(
                "Kaynakta çıkar çatışması bildirimi bulunuyor."
            )

        if source.methodology_score < 40:
            warnings.append(
                "Yöntem açıklaması yetersiz."
            )

        if source.corroboration_score < 40:
            warnings.append(
                "Bağımsız doğrulama desteği zayıf."
            )

        score = round(
            min(100.0, max(0.0, score)),
            3,
        )

        level = self._resolve_level(score)
        accepted = score >= self.minimum_acceptance_score

        if accepted:
            reasons.append(
                "Kaynak güven eşiğini karşıladı."
            )
        else:
            warnings.append(
                "Kaynak güven eşiğini karşılamadı."
            )

        return SourceTrustResult(
            source_id=source.source_id,
            score=score,
            level=level,
            accepted=accepted,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _resolve_level(
        score: float,
    ) -> SourceTrustLevel:
        if score < 20:
            return SourceTrustLevel.VERY_LOW

        if score < 40:
            return SourceTrustLevel.LOW

        if score < 60:
            return SourceTrustLevel.MEDIUM

        if score < 75:
            return SourceTrustLevel.HIGH

        if score < 90:
            return SourceTrustLevel.VERY_HIGH

        return SourceTrustLevel.AUTHORITATIVE

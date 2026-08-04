"""SyKaşif çekirdek istisnaları."""

from __future__ import annotations


class SykCoreError(Exception):
    """Tüm çekirdek hatalarının ana sınıfı."""


class InvalidCoordinateError(SykCoreError, ValueError):
    """Koordinat doğrulaması başarısız."""


class InvalidEntityStateError(SykCoreError, ValueError):
    """Varlık geçersiz durum geçişi istedi."""


class InvalidLayerError(SykCoreError, ValueError):
    """Katman kaydı geçersiz."""


class DuplicateEvidenceError(SykCoreError, ValueError):
    """Aynı kanıt ikinci defa eklenmeye çalışıldı."""


class EvidenceIntegrityError(SykCoreError, ValueError):
    """Kanıt bütünlük doğrulaması başarısız."""

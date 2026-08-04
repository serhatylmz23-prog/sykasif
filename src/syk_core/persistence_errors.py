"""Kalıcı kayıt ve bütünlük hataları."""

from __future__ import annotations


class PersistenceError(Exception):
    """Kalıcı kayıt sistemi ana hatası."""


class ResearchPointNotFoundError(PersistenceError, KeyError):
    """Araştırma noktası kaydı bulunamadı."""


class ResearchPointAlreadyExistsError(PersistenceError):
    """Araştırma noktası zaten kayıtlı."""


class RepositoryIntegrityError(PersistenceError):
    """Kayıt dosyası bütünlük doğrulaması başarısız."""


class ManifestIntegrityError(PersistenceError):
    """Manifest doğrulaması başarısız."""


class HistoryIntegrityError(PersistenceError):
    """Değişiklik geçmişi zinciri geçersiz."""


class SerializationError(PersistenceError, ValueError):
    """JSON verisi nesneye dönüştürülemedi."""

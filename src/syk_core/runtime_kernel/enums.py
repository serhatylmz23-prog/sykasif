"""Çalışma çekirdeği durum sabitleri."""

from __future__ import annotations

from enum import Enum, IntEnum


class RuntimeState(str, Enum):
    CREATED = "oluşturuldu"
    STARTING = "başlatılıyor"
    RUNNING = "çalışıyor"
    PAUSED = "bekliyor"
    STOPPING = "durduruluyor"
    STOPPED = "durdu"
    FAILED = "hata"


class ModuleState(str, Enum):
    REGISTERED = "kayıtlı"
    STARTING = "başlatılıyor"
    ACTIVE = "aktif"
    PAUSED = "bekliyor"
    STOPPING = "durduruluyor"
    STOPPED = "durdu"
    FAILED = "hata"


class ModuleHealth(str, Enum):
    UNKNOWN = "bilinmiyor"
    HEALTHY = "sağlıklı"
    DEGRADED = "kısmi"
    UNHEALTHY = "sağlıksız"


class RuntimeEventPriority(IntEnum):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40

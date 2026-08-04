from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import hmac
import json
from secrets import randbelow, token_hex
from threading import RLock
from typing import Any
from uuid import uuid4


QUEUE_TYPES = {
    "event",
    "frame",
    "evidence",
    "report",
    "location",
    "jarmin_command",
    "file",
}

QUEUE_STATUSES = {
    "pending",
    "processing",
    "completed",
    "failed",
    "cancelled",
}

PAIRING_STATUSES = {
    "waiting",
    "paired",
    "expired",
    "revoked",
}


@dataclass(frozen=True, slots=True)
class OfflineQueueItem:
    item_id: str
    item_type: str
    device_id: str
    endpoint: str
    method: str
    payload: dict[str, Any]
    payload_sha256: str
    status: str
    attempt_count: int
    maximum_attempts: int
    last_error: str | None
    created_at: str
    updated_at: str
    completed_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-mobile-offline-item/v1"
            ),
            "item_id": self.item_id,
            "item_type": self.item_type,
            "device_id": self.device_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "payload": dict(self.payload),
            "payload_sha256": (
                self.payload_sha256
            ),
            "status": self.status,
            "attempt_count": (
                self.attempt_count
            ),
            "maximum_attempts": (
                self.maximum_attempts
            ),
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": (
                self.completed_at
            ),
        }


@dataclass(frozen=True, slots=True)
class PairingRecord:
    pairing_id: str
    pairing_code: str
    requesting_device_id: str
    requesting_device_title: str
    target_role: str
    status: str
    expires_at: str
    created_at: str
    paired_at: str | None
    paired_device_id: str | None
    pairing_token_sha256: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": (
                "sykasif-device-pairing/v1"
            ),
            "pairing_id": self.pairing_id,
            "pairing_code": (
                self.pairing_code
            ),
            "requesting_device_id": (
                self.requesting_device_id
            ),
            "requesting_device_title": (
                self.requesting_device_title
            ),
            "target_role": self.target_role,
            "status": self.status,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "paired_at": self.paired_at,
            "paired_device_id": (
                self.paired_device_id
            ),
            "pairing_token_sha256": (
                self.pairing_token_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class CacheEntry:
    cache_key: str
    category: str
    value: dict[str, Any]
    value_sha256: str
    created_at: str
    updated_at: str
    expires_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "category": self.category,
            "value": dict(self.value),
            "value_sha256": (
                self.value_sha256
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }


class MobileOfflineRuntime:
    def __init__(
        self,
        *,
        maximum_queue_items: int = 1000,
        maximum_cache_entries: int = 500,
        pairing_lifetime_seconds: int = 300,
    ) -> None:
        if maximum_queue_items <= 0:
            raise ValueError(
                "Azami kuyruk sayısı pozitif "
                "olmalıdır."
            )

        if maximum_cache_entries <= 0:
            raise ValueError(
                "Azami önbellek sayısı pozitif "
                "olmalıdır."
            )

        if pairing_lifetime_seconds < 30:
            raise ValueError(
                "Eşleştirme süresi en az "
                "30 saniye olmalıdır."
            )

        self.maximum_queue_items = (
            maximum_queue_items
        )

        self.maximum_cache_entries = (
            maximum_cache_entries
        )

        self.pairing_lifetime_seconds = (
            pairing_lifetime_seconds
        )

        self._queue: dict[
            str,
            OfflineQueueItem,
        ] = {}

        self._queue_order: list[str] = []

        self._pairings: dict[
            str,
            PairingRecord,
        ] = {}

        self._pairing_code_index: dict[
            str,
            str,
        ] = {}

        self._cache: dict[
            str,
            CacheEntry,
        ] = {}

        self._cache_order: list[str] = []

        self._online = True
        self._lock = RLock()

    def set_online(
        self,
        online: bool,
    ) -> dict[str, Any]:
        with self._lock:
            self._online = bool(online)

        return self.snapshot()

    def enqueue(
        self,
        *,
        item_type: str,
        device_id: str,
        endpoint: str,
        method: str,
        payload: dict[str, Any],
        maximum_attempts: int = 5,
        item_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_type = (
            item_type.strip().lower()
        )

        normalized_device = (
            device_id.strip()
        )

        normalized_endpoint = (
            endpoint.strip()
        )

        normalized_method = (
            method.strip().upper()
        )

        if normalized_type not in QUEUE_TYPES:
            raise ValueError(
                "Geçersiz çevrimdışı kayıt türü."
            )

        if not normalized_device:
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not normalized_endpoint:
            raise ValueError(
                "Hedef adres boş olamaz."
            )

        if normalized_method not in {
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }:
            raise ValueError(
                "Desteklenmeyen istek yöntemi."
            )

        if maximum_attempts <= 0:
            raise ValueError(
                "Azami deneme sayısı pozitif "
                "olmalıdır."
            )

        resolved_id = (
            item_id.strip()
            if item_id
            else f"OFF-{uuid4().hex[:24]}"
        )

        canonical_payload = (
            self._canonical(payload)
        )

        now = self._now()

        item = OfflineQueueItem(
            item_id=resolved_id,
            item_type=normalized_type,
            device_id=normalized_device,
            endpoint=normalized_endpoint,
            method=normalized_method,
            payload=dict(payload),
            payload_sha256=sha256(
                canonical_payload
            ).hexdigest(),
            status="pending",
            attempt_count=0,
            maximum_attempts=(
                maximum_attempts
            ),
            last_error=None,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

        with self._lock:
            existing = self._find_duplicate(
                item
            )

            if existing is not None:
                return {
                    "created": False,
                    "duplicate": True,
                    "item": existing.as_dict(),
                }

            self._queue[
                resolved_id
            ] = item

            self._queue_order.append(
                resolved_id
            )

            self._trim_queue()

        return {
            "created": True,
            "duplicate": False,
            "item": item.as_dict(),
        }

    def pending(
        self,
        *,
        device_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError(
                "Kuyruk sınırı pozitif "
                "olmalıdır."
            )

        with self._lock:
            items = [
                self._queue[item_id]
                for item_id
                in self._queue_order
                if (
                    item_id in self._queue
                    and self._queue[
                        item_id
                    ].status
                    in {
                        "pending",
                        "failed",
                    }
                )
            ]

        if device_id is not None:
            normalized_device = (
                device_id.strip()
            )

            items = [
                item
                for item in items
                if (
                    item.device_id
                    == normalized_device
                )
            ]

        return [
            item.as_dict()
            for item in items[:limit]
        ]

    def begin_processing(
        self,
        item_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require_item(
                item_id
            )

            if current.status in {
                "completed",
                "cancelled",
            }:
                raise ValueError(
                    "Tamamlanan veya iptal edilen "
                    "kayıt işlenemez."
                )

            if (
                current.attempt_count
                >= current.maximum_attempts
            ):
                raise ValueError(
                    "Azami deneme sayısına "
                    "ulaşıldı."
                )

            updated = self._replace_item(
                current,
                status="processing",
                attempt_count=(
                    current.attempt_count
                    + 1
                ),
                last_error=None,
            )

            self._queue[
                item_id
            ] = updated

        return updated.as_dict()

    def complete(
        self,
        item_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require_item(
                item_id
            )

            updated = self._replace_item(
                current,
                status="completed",
                last_error=None,
                completed_at=self._now(),
            )

            self._queue[
                item_id
            ] = updated

        return updated.as_dict()

    def fail(
        self,
        item_id: str,
        *,
        error_message: str,
    ) -> dict[str, Any]:
        normalized_error = (
            error_message.strip()
        )

        if not normalized_error:
            raise ValueError(
                "Hata açıklaması boş olamaz."
            )

        with self._lock:
            current = self._require_item(
                item_id
            )

            final_status = (
                "cancelled"
                if (
                    current.attempt_count
                    >= current.maximum_attempts
                )
                else "failed"
            )

            updated = self._replace_item(
                current,
                status=final_status,
                last_error=normalized_error,
            )

            self._queue[
                item_id
            ] = updated

        return updated.as_dict()

    def cancel(
        self,
        item_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require_item(
                item_id
            )

            updated = self._replace_item(
                current,
                status="cancelled",
            )

            self._queue[
                item_id
            ] = updated

        return updated.as_dict()

    def remove_completed(
        self,
    ) -> int:
        with self._lock:
            completed_ids = [
                item_id
                for item_id
                in self._queue_order
                if (
                    item_id in self._queue
                    and self._queue[
                        item_id
                    ].status
                    in {
                        "completed",
                        "cancelled",
                    }
                )
            ]

            for item_id in completed_ids:
                self._queue.pop(
                    item_id,
                    None,
                )

            self._queue_order = [
                item_id
                for item_id
                in self._queue_order
                if item_id
                not in completed_ids
            ]

        return len(completed_ids)

    def create_pairing(
        self,
        *,
        requesting_device_id: str,
        requesting_device_title: str,
        target_role: str = "trusted_terminal",
    ) -> dict[str, Any]:
        normalized_device = (
            requesting_device_id.strip()
        )

        normalized_title = (
            requesting_device_title.strip()
        )

        normalized_role = (
            target_role.strip().lower()
        )

        if not normalized_device:
            raise ValueError(
                "Eşleştirilecek cihaz kimliği "
                "boş olamaz."
            )

        if not normalized_title:
            raise ValueError(
                "Eşleştirilecek cihaz başlığı "
                "boş olamaz."
            )

        with self._lock:
            self.expire_pairings()

            pairing_id = (
                f"PAIR-{uuid4().hex[:20]}"
            )

            code = self._generate_pairing_code()

            now = datetime.now(UTC)

            record = PairingRecord(
                pairing_id=pairing_id,
                pairing_code=code,
                requesting_device_id=(
                    normalized_device
                ),
                requesting_device_title=(
                    normalized_title
                ),
                target_role=normalized_role,
                status="waiting",
                expires_at=(
                    now
                    + timedelta(
                        seconds=(
                            self
                            .pairing_lifetime_seconds
                        )
                    )
                ).isoformat(),
                created_at=now.isoformat(),
                paired_at=None,
                paired_device_id=None,
                pairing_token_sha256=None,
            )

            self._pairings[
                pairing_id
            ] = record

            self._pairing_code_index[
                code
            ] = pairing_id

        return record.as_dict()

    def confirm_pairing(
        self,
        *,
        pairing_code: str,
        paired_device_id: str,
    ) -> dict[str, Any]:
        normalized_code = (
            pairing_code.strip()
            .replace(" ", "")
        )

        normalized_device = (
            paired_device_id.strip()
        )

        if not normalized_code:
            raise ValueError(
                "Eşleştirme kodu boş olamaz."
            )

        if not normalized_device:
            raise ValueError(
                "Onaylayan cihaz kimliği "
                "boş olamaz."
            )

        with self._lock:
            self.expire_pairings()

            try:
                pairing_id = (
                    self._pairing_code_index[
                        normalized_code
                    ]
                )

                current = self._pairings[
                    pairing_id
                ]

            except KeyError as error:
                raise KeyError(
                    "Eşleştirme kodu bulunamadı."
                ) from error

            if current.status != "waiting":
                raise ValueError(
                    "Eşleştirme kaydı bekleme "
                    "durumunda değil."
                )

            raw_token = token_hex(32)

            token_sha256 = sha256(
                raw_token.encode("utf-8")
            ).hexdigest()

            paired_at = self._now()

            updated = PairingRecord(
                pairing_id=(
                    current.pairing_id
                ),
                pairing_code=(
                    current.pairing_code
                ),
                requesting_device_id=(
                    current
                    .requesting_device_id
                ),
                requesting_device_title=(
                    current
                    .requesting_device_title
                ),
                target_role=(
                    current.target_role
                ),
                status="paired",
                expires_at=(
                    current.expires_at
                ),
                created_at=(
                    current.created_at
                ),
                paired_at=paired_at,
                paired_device_id=(
                    normalized_device
                ),
                pairing_token_sha256=(
                    token_sha256
                ),
            )

            self._pairings[
                pairing_id
            ] = updated

        return {
            "pairing": updated.as_dict(),
            "pairing_token": raw_token,
        }

    def verify_pairing_token(
        self,
        *,
        pairing_id: str,
        pairing_token: str,
    ) -> bool:
        normalized_token = (
            pairing_token.strip()
        )

        if not normalized_token:
            return False

        with self._lock:
            try:
                record = self._pairings[
                    pairing_id
                ]
            except KeyError:
                return False

        if (
            record.status != "paired"
            or not record
                .pairing_token_sha256
        ):
            return False

        candidate = sha256(
            normalized_token
            .encode("utf-8")
        ).hexdigest()

        return hmac.compare_digest(
            candidate,
            record.pairing_token_sha256,
        )

    def revoke_pairing(
        self,
        pairing_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            current = self._require_pairing(
                pairing_id
            )

            updated = PairingRecord(
                pairing_id=(
                    current.pairing_id
                ),
                pairing_code=(
                    current.pairing_code
                ),
                requesting_device_id=(
                    current
                    .requesting_device_id
                ),
                requesting_device_title=(
                    current
                    .requesting_device_title
                ),
                target_role=(
                    current.target_role
                ),
                status="revoked",
                expires_at=(
                    current.expires_at
                ),
                created_at=(
                    current.created_at
                ),
                paired_at=(
                    current.paired_at
                ),
                paired_device_id=(
                    current.paired_device_id
                ),
                pairing_token_sha256=None,
            )

            self._pairings[
                pairing_id
            ] = updated

        return updated.as_dict()

    def expire_pairings(
        self,
    ) -> int:
        now = datetime.now(UTC)
        expired_count = 0

        with self._lock:
            for pairing_id, current in list(
                self._pairings.items()
            ):
                if current.status != "waiting":
                    continue

                expires_at = datetime.fromisoformat(
                    current.expires_at
                )

                if expires_at > now:
                    continue

                updated = PairingRecord(
                    pairing_id=(
                        current.pairing_id
                    ),
                    pairing_code=(
                        current.pairing_code
                    ),
                    requesting_device_id=(
                        current
                        .requesting_device_id
                    ),
                    requesting_device_title=(
                        current
                        .requesting_device_title
                    ),
                    target_role=(
                        current.target_role
                    ),
                    status="expired",
                    expires_at=(
                        current.expires_at
                    ),
                    created_at=(
                        current.created_at
                    ),
                    paired_at=None,
                    paired_device_id=None,
                    pairing_token_sha256=None,
                )

                self._pairings[
                    pairing_id
                ] = updated

                expired_count += 1

        return expired_count

    def list_pairings(
        self,
        *,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        self.expire_pairings()

        with self._lock:
            values = list(
                self._pairings.values()
            )

        if status is not None:
            normalized = (
                status.strip().lower()
            )

            if normalized not in PAIRING_STATUSES:
                raise ValueError(
                    "Geçersiz eşleştirme durumu."
                )

            values = [
                value
                for value in values
                if value.status == normalized
            ]

        return [
            value.as_dict()
            for value in values
        ]

    def cache_put(
        self,
        *,
        cache_key: str,
        category: str,
        value: dict[str, Any],
        lifetime_seconds: int | None = None,
    ) -> dict[str, Any]:
        normalized_key = (
            cache_key.strip()
        )

        normalized_category = (
            category.strip().lower()
        )

        if not normalized_key:
            raise ValueError(
                "Önbellek anahtarı boş olamaz."
            )

        if not normalized_category:
            raise ValueError(
                "Önbellek kategorisi boş "
                "olamaz."
            )

        if (
            lifetime_seconds is not None
            and lifetime_seconds <= 0
        ):
            raise ValueError(
                "Önbellek süresi pozitif "
                "olmalıdır."
            )

        now = datetime.now(UTC)

        with self._lock:
            existing = self._cache.get(
                normalized_key
            )

            created_at = (
                existing.created_at
                if existing
                else now.isoformat()
            )

            entry = CacheEntry(
                cache_key=normalized_key,
                category=normalized_category,
                value=dict(value),
                value_sha256=sha256(
                    self._canonical(value)
                ).hexdigest(),
                created_at=created_at,
                updated_at=now.isoformat(),
                expires_at=(
                    (
                        now
                        + timedelta(
                            seconds=(
                                lifetime_seconds
                            )
                        )
                    ).isoformat()
                    if lifetime_seconds
                    is not None
                    else None
                ),
            )

            self._cache[
                normalized_key
            ] = entry

            if normalized_key not in (
                self._cache_order
            ):
                self._cache_order.append(
                    normalized_key
                )

            self._trim_cache()

        return entry.as_dict()

    def cache_get(
        self,
        cache_key: str,
    ) -> dict[str, Any] | None:
        normalized_key = (
            cache_key.strip()
        )

        with self._lock:
            entry = self._cache.get(
                normalized_key
            )

            if entry is None:
                return None

            if self._cache_expired(entry):
                self._cache.pop(
                    normalized_key,
                    None,
                )

                self._cache_order = [
                    key
                    for key in self._cache_order
                    if key != normalized_key
                ]

                return None

            return entry.as_dict()

    def cache_delete(
        self,
        cache_key: str,
    ) -> bool:
        normalized_key = (
            cache_key.strip()
        )

        with self._lock:
            existed = (
                normalized_key
                in self._cache
            )

            self._cache.pop(
                normalized_key,
                None,
            )

            self._cache_order = [
                key
                for key in self._cache_order
                if key != normalized_key
            ]

        return existed

    def cache_list(
        self,
        *,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        self.cleanup_cache()

        with self._lock:
            values = [
                self._cache[key]
                for key in self._cache_order
                if key in self._cache
            ]

        if category is not None:
            normalized_category = (
                category.strip().lower()
            )

            values = [
                value
                for value in values
                if (
                    value.category
                    == normalized_category
                )
            ]

        return [
            value.as_dict()
            for value in values
        ]

    def cleanup_cache(
        self,
    ) -> int:
        with self._lock:
            expired_keys = [
                key
                for key, entry
                in self._cache.items()
                if self._cache_expired(
                    entry
                )
            ]

            for key in expired_keys:
                self._cache.pop(
                    key,
                    None,
                )

            self._cache_order = [
                key
                for key in self._cache_order
                if key not in expired_keys
            ]

        return len(expired_keys)

    def snapshot(
        self,
    ) -> dict[str, Any]:
        self.expire_pairings()
        self.cleanup_cache()

        with self._lock:
            queue_items = [
                self._queue[item_id]
                for item_id
                in self._queue_order
                if item_id in self._queue
            ]

            pairings = list(
                self._pairings.values()
            )

            cache_entries = list(
                self._cache.values()
            )

            unsigned = {
                "schema": (
                    "sykasif-mobile-offline-runtime/v1"
                ),
                "online": self._online,
                "queue_count": len(
                    queue_items
                ),
                "pending_count": sum(
                    1
                    for item in queue_items
                    if item.status
                    in {
                        "pending",
                        "failed",
                    }
                ),
                "completed_count": sum(
                    1
                    for item in queue_items
                    if item.status
                    == "completed"
                ),
                "pairing_count": len(
                    pairings
                ),
                "active_pairing_count": sum(
                    1
                    for item in pairings
                    if item.status
                    in {
                        "waiting",
                        "paired",
                    }
                ),
                "cache_count": len(
                    cache_entries
                ),
                "status": "ready",
            }

        return {
            **unsigned,
            "snapshot_sha256": sha256(
                self._canonical(unsigned)
            ).hexdigest(),
        }

    def _find_duplicate(
        self,
        candidate: OfflineQueueItem,
    ) -> OfflineQueueItem | None:
        for item in self._queue.values():
            if item.status not in {
                "pending",
                "processing",
                "failed",
            }:
                continue

            if (
                item.device_id
                == candidate.device_id
                and item.endpoint
                == candidate.endpoint
                and item.method
                == candidate.method
                and item.payload_sha256
                == candidate.payload_sha256
            ):
                return item

        return None

    def _replace_item(
        self,
        current: OfflineQueueItem,
        *,
        status: str | None = None,
        attempt_count: int | None = None,
        last_error: str | None = None,
        completed_at: str | None = None,
    ) -> OfflineQueueItem:
        resolved_status = (
            status or current.status
        )

        if resolved_status not in QUEUE_STATUSES:
            raise ValueError(
                "Geçersiz kuyruk durumu."
            )

        return OfflineQueueItem(
            item_id=current.item_id,
            item_type=current.item_type,
            device_id=current.device_id,
            endpoint=current.endpoint,
            method=current.method,
            payload=dict(current.payload),
            payload_sha256=(
                current.payload_sha256
            ),
            status=resolved_status,
            attempt_count=(
                current.attempt_count
                if attempt_count is None
                else attempt_count
            ),
            maximum_attempts=(
                current.maximum_attempts
            ),
            last_error=last_error,
            created_at=current.created_at,
            updated_at=self._now(),
            completed_at=(
                completed_at
                if completed_at is not None
                else current.completed_at
            ),
        )

    def _require_item(
        self,
        item_id: str,
    ) -> OfflineQueueItem:
        try:
            return self._queue[
                item_id
            ]
        except KeyError as error:
            raise KeyError(
                "Çevrimdışı kuyruk kaydı "
                "bulunamadı."
            ) from error

    def _require_pairing(
        self,
        pairing_id: str,
    ) -> PairingRecord:
        try:
            return self._pairings[
                pairing_id
            ]
        except KeyError as error:
            raise KeyError(
                "Cihaz eşleştirme kaydı "
                "bulunamadı."
            ) from error

    def _generate_pairing_code(
        self,
    ) -> str:
        for _ in range(100):
            code = (
                f"{randbelow(1000000):06d}"
            )

            if (
                code
                not in self._pairing_code_index
            ):
                return code

        raise RuntimeError(
            "Eşleştirme kodu üretilemedi."
        )

    def _trim_queue(self) -> None:
        overflow = (
            len(self._queue_order)
            - self.maximum_queue_items
        )

        if overflow <= 0:
            return

        removable = [
            item_id
            for item_id in self._queue_order
            if (
                item_id in self._queue
                and self._queue[
                    item_id
                ].status
                in {
                    "completed",
                    "cancelled",
                }
            )
        ]

        while (
            overflow > 0
            and removable
        ):
            item_id = removable.pop(0)

            self._queue.pop(
                item_id,
                None,
            )

            self._queue_order.remove(
                item_id
            )

            overflow -= 1

        while overflow > 0:
            item_id = self._queue_order.pop(
                0
            )

            self._queue.pop(
                item_id,
                None,
            )

            overflow -= 1

    def _trim_cache(self) -> None:
        overflow = (
            len(self._cache_order)
            - self.maximum_cache_entries
        )

        if overflow <= 0:
            return

        expired_keys = self._cache_order[
            :overflow
        ]

        del self._cache_order[
            :overflow
        ]

        for key in expired_keys:
            self._cache.pop(
                key,
                None,
            )

    @staticmethod
    def _cache_expired(
        entry: CacheEntry,
    ) -> bool:
        if entry.expires_at is None:
            return False

        return (
            datetime.fromisoformat(
                entry.expires_at
            )
            <= datetime.now(UTC)
        )

    @staticmethod
    def _canonical(
        payload: dict[str, Any],
    ) -> bytes:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(
            UTC
        ).isoformat()


mobile_offline_runtime = (
    MobileOfflineRuntime()
)
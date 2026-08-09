from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = ROOT / "runtime" / "trusted_devices.json"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def normalize_device_type(value: str) -> str:
    normalized = value.strip().lower()

    if normalized in {
        "tablet",
        "phone",
        "desktop",
        "mobile",
    }:
        return normalized

    return "unknown"


@dataclass(slots=True)
class TrustedDevice:
    device_id: str
    device_type: str
    device_name: str
    trust_token_hash: str
    created_at: str
    last_seen_at: str
    client_host: str
    user_agent: str
    trusted: bool = True
    connection_count: int = 1

    def public_export(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("trust_token_hash", None)
        return data


class TrustedDeviceRegistry:
    def __init__(
        self,
        store_path: Path = STORE_PATH,
    ) -> None:
        self.store_path = store_path
        self._lock = asyncio.Lock()
        self._devices: dict[str, TrustedDevice] = {}
        self._loaded = False

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        async with self._lock:
            if self._loaded:
                return

            self.store_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if self.store_path.is_file():
                raw = json.loads(
                    self.store_path.read_text(
                        encoding="utf-8",
                    )
                )

                for item in raw.get("devices", []):
                    device = TrustedDevice(**item)
                    self._devices[device.device_id] = device

            self._loaded = True

    async def _save_unlocked(self) -> None:
        payload = {
            "version": 1,
            "updated_at": utc_now(),
            "devices": [
                asdict(device)
                for device in sorted(
                    self._devices.values(),
                    key=lambda item: item.device_id,
                )
            ],
        }

        temporary = self.store_path.with_suffix(
            ".json.tmp"
        )

        temporary.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary.replace(self.store_path)

    async def register(
        self,
        *,
        device_id: str | None,
        device_type: str,
        device_name: str,
        client_host: str,
        user_agent: str,
    ) -> tuple[TrustedDevice, str, bool]:
        await self._ensure_loaded()

        clean_id = (
            device_id.strip()
            if device_id
            else ""
        )

        async with self._lock:
            existing = self._devices.get(clean_id)

            if existing is not None:
                existing.last_seen_at = utc_now()
                existing.client_host = client_host
                existing.user_agent = user_agent
                existing.device_type = normalize_device_type(
                    device_type
                )
                existing.device_name = (
                    device_name.strip()
                    or existing.device_name
                )
                existing.connection_count += 1

                await self._save_unlocked()

                return existing, "", False

            new_device_id = (
                clean_id
                or secrets.token_urlsafe(18)
            )

            trust_token = secrets.token_urlsafe(32)
            timestamp = utc_now()

            device = TrustedDevice(
                device_id=new_device_id,
                device_type=normalize_device_type(
                    device_type
                ),
                device_name=(
                    device_name.strip()
                    or "SyKaşif İstemcisi"
                ),
                trust_token_hash=self.hash_token(
                    trust_token
                ),
                created_at=timestamp,
                last_seen_at=timestamp,
                client_host=client_host,
                user_agent=user_agent,
            )

            self._devices[new_device_id] = device

            await self._save_unlocked()

            return device, trust_token, True

    async def authenticate(
        self,
        *,
        device_id: str,
        trust_token: str,
        client_host: str,
        user_agent: str,
    ) -> TrustedDevice | None:
        await self._ensure_loaded()

        token_hash = self.hash_token(trust_token)

        async with self._lock:
            device = self._devices.get(device_id)

            if device is None:
                return None

            if not device.trusted:
                return None

            if not secrets.compare_digest(
                device.trust_token_hash,
                token_hash,
            ):
                return None

            device.last_seen_at = utc_now()
            device.client_host = client_host
            device.user_agent = user_agent
            device.connection_count += 1

            await self._save_unlocked()

            return device

    async def get(
        self,
        device_id: str,
    ) -> TrustedDevice | None:
        await self._ensure_loaded()

        async with self._lock:
            return self._devices.get(device_id)

    async def revoke(
        self,
        device_id: str,
    ) -> bool:
        await self._ensure_loaded()

        async with self._lock:
            device = self._devices.get(device_id)

            if device is None:
                return False

            device.trusted = False
            device.last_seen_at = utc_now()

            await self._save_unlocked()

            return True

    async def snapshot(self) -> dict[str, Any]:
        await self._ensure_loaded()

        async with self._lock:
            devices = [
                device.public_export()
                for device in self._devices.values()
            ]

        return {
            "trusted_count": sum(
                1
                for device in devices
                if device["trusted"]
            ),
            "total_count": len(devices),
            "devices": devices,
            "timestamp": utc_now(),
        }


trusted_device_registry = TrustedDeviceRegistry()

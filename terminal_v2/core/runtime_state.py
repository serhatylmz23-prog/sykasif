from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


RuntimeListener = Callable[
    [dict[str, Any]],
    Awaitable[None],
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class RuntimeState:
    """Masaüstü, tablet ve telefonun ortak çalışma durumu."""

    VALID_STATUSES = {
        "BEKLIYOR",
        "CALISIYOR",
        "TARIYOR",
        "DOGRULANIYOR",
        "TAMAMLANDI",
        "DURDU",
        "CEVRIMDISI",
        "HATA",
    }

    DEVICE_TYPES = {
        "masaustu",
        "tablet",
        "telefon",
    }

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._revision = 0
        self._listeners: set[RuntimeListener] = set()
        self._state = self._initial_state()

    @staticmethod
    def _initial_state() -> dict[str, Any]:
        return {
            "sistem": {
                "durum": "BEKLIYOR",
                "mesaj": "SyKaşif çalışma alanı hazır.",
            },
            "aktif_modul": "dashboard",
            "cihazlar": {
                "masaustu": {
                    "bagli": True,
                    "durum": "CALISIYOR",
                },
                "tablet": {
                    "bagli": False,
                    "durum": "CEVRIMDISI",
                },
                "telefon": {
                    "bagli": False,
                    "durum": "CEVRIMDISI",
                },
            },
            "moduller": {},
            "bildirimler": [],
            "son_olay": None,
            "guncellenme_zamani": utc_now(),
        }

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            return self._export_unlocked()

    async def set_system_status(
        self,
        *,
        durum: str,
        mesaj: str,
        kaynak: str = "runtime",
    ) -> dict[str, Any]:
        normalized = durum.strip().upper()

        if normalized not in self.VALID_STATUSES:
            raise ValueError(
                f"Geçersiz runtime durumu: {durum}"
            )

        return await self.update(
            {
                "sistem": {
                    "durum": normalized,
                    "mesaj": mesaj.strip(),
                }
            },
            olay_turu="SISTEM_DURUMU_DEGISTI",
            kaynak=kaynak,
        )

    async def set_device(
        self,
        *,
        cihaz_turu: str,
        bagli: bool,
        kaynak: str | None = None,
    ) -> dict[str, Any]:
        normalized = cihaz_turu.strip().lower()

        if normalized not in self.DEVICE_TYPES:
            raise ValueError(
                f"Geçersiz cihaz türü: {cihaz_turu}"
            )

        durum = "CALISIYOR" if bagli else "CEVRIMDISI"

        return await self.update(
            {
                "cihazlar": {
                    normalized: {
                        "bagli": bagli,
                        "durum": durum,
                    }
                }
            },
            olay_turu="CIHAZ_DURUMU_DEGISTI",
            kaynak=kaynak or normalized,
        )

    async def set_active_module(
        self,
        modul_kodu: str,
        *,
        kaynak: str,
    ) -> dict[str, Any]:
        clean_code = modul_kodu.strip().lower()

        if not clean_code:
            raise ValueError(
                "Aktif modül kodu boş olamaz."
            )

        return await self.update(
            {
                "aktif_modul": clean_code,
                "moduller": {
                    clean_code: {
                        "durum": "CALISIYOR",
                    }
                },
            },
            olay_turu="AKTIF_MODUL_DEGISTI",
            kaynak=kaynak,
        )

    async def update(
        self,
        patch: dict[str, Any],
        *,
        olay_turu: str,
        kaynak: str,
    ) -> dict[str, Any]:
        async with self._lock:
            self._merge(
                self._state,
                patch,
            )

            self._revision += 1
            timestamp = utc_now()

            event = {
                "revision": self._revision,
                "olay_turu": olay_turu,
                "kaynak": kaynak,
                "veri": deepcopy(patch),
                "zaman": timestamp,
            }

            self._state["son_olay"] = event
            self._state["guncellenme_zamani"] = timestamp

            snapshot = self._export_unlocked()
            listeners = tuple(self._listeners)

        await self._notify(
            listeners,
            snapshot,
        )

        return snapshot

    async def subscribe(
        self,
        listener: RuntimeListener,
    ) -> None:
        async with self._lock:
            self._listeners.add(listener)

    async def unsubscribe(
        self,
        listener: RuntimeListener,
    ) -> None:
        async with self._lock:
            self._listeners.discard(listener)

    async def reset(self) -> dict[str, Any]:
        async with self._lock:
            self._revision = 0
            self._state = self._initial_state()
            snapshot = self._export_unlocked()
            listeners = tuple(self._listeners)

        await self._notify(
            listeners,
            snapshot,
        )

        return snapshot

    def _export_unlocked(self) -> dict[str, Any]:
        return {
            "revision": self._revision,
            "durum": deepcopy(self._state),
        }

    @staticmethod
    async def _notify(
        listeners: tuple[RuntimeListener, ...],
        snapshot: dict[str, Any],
    ) -> None:
        if not listeners:
            return

        results = await asyncio.gather(
            *(
                listener(deepcopy(snapshot))
                for listener in listeners
            ),
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, BaseException):
                continue

    @classmethod
    def _merge(
        cls,
        target: dict[str, Any],
        patch: dict[str, Any],
    ) -> None:
        for key, value in patch.items():
            if (
                isinstance(value, dict)
                and isinstance(target.get(key), dict)
            ):
                cls._merge(
                    target[key],
                    value,
                )
            else:
                target[key] = deepcopy(value)


runtime_state = RuntimeState()

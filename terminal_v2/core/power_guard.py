from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass
from typing import Final


ES_CONTINUOUS: Final[int] = 0x80000000
ES_SYSTEM_REQUIRED: Final[int] = 0x00000001
ES_DISPLAY_REQUIRED: Final[int] = 0x00000002


@dataclass(slots=True)
class PowerGuardStatus:
    supported: bool
    active: bool
    keep_display_on: bool
    platform: str
    error: str | None = None

    def export(self) -> dict[str, object]:
        return {
            "supported": self.supported,
            "active": self.active,
            "keep_display_on": self.keep_display_on,
            "platform": self.platform,
            "error": self.error,
        }


class PowerGuard:
    def __init__(
        self,
        *,
        keep_display_on: bool = True,
    ) -> None:
        self.keep_display_on = keep_display_on
        self._active = False
        self._error: str | None = None

    @property
    def supported(self) -> bool:
        return platform.system().lower() == "windows"

    @property
    def active(self) -> bool:
        return self._active

    def enable(self) -> PowerGuardStatus:
        self._error = None

        if not self.supported:
            return self.status()

        flags = (
            ES_CONTINUOUS
            | ES_SYSTEM_REQUIRED
        )

        if self.keep_display_on:
            flags |= ES_DISPLAY_REQUIRED

        try:
            result = ctypes.windll.kernel32.SetThreadExecutionState(
                flags
            )

            if result == 0:
                raise OSError(
                    "SetThreadExecutionState başarısız."
                )

            self._active = True
        except Exception as exc:
            self._active = False
            self._error = str(exc)

        return self.status()

    def disable(self) -> PowerGuardStatus:
        self._error = None

        if not self.supported:
            self._active = False
            return self.status()

        try:
            result = ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS
            )

            if result == 0:
                raise OSError(
                    "Power Guard kapatılamadı."
                )

            self._active = False
        except Exception as exc:
            self._error = str(exc)

        return self.status()

    def status(self) -> PowerGuardStatus:
        return PowerGuardStatus(
            supported=self.supported,
            active=self._active,
            keep_display_on=self.keep_display_on,
            platform=platform.system(),
            error=self._error,
        )

    def __enter__(self) -> "PowerGuard":
        self.enable()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.disable()


power_guard = PowerGuard(
    keep_display_on=True,
)

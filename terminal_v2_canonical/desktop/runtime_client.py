from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8013"


def normalize_base_url(value: str) -> str:
    cleaned = value.strip().rstrip("/")

    if not cleaned:
        return DEFAULT_BASE_URL

    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"http://{cleaned}"

    return cleaned


@dataclass(frozen=True)
class RuntimeResponse:
    basarili: bool
    veri: dict[str, Any]
    hata: str = ""


class RuntimeClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 2.5,
    ) -> None:
        self.base_url = normalize_base_url(base_url)
        self.timeout = timeout

    def runtime_durumu(self) -> RuntimeResponse:
        return self._request(
            "GET",
            "/api/v2/runtime-state",
        )

    def modul_kartlari(self) -> RuntimeResponse:
        return self._request(
            "GET",
            "/api/v2/modul-kartlari",
        )

    def masaustunu_bagla(self) -> RuntimeResponse:
        return self._request(
            "POST",
            "/api/v2/runtime-state/cihaz",
            {
                "cihaz_turu": "masaustu",
                "bagli": True,
                "kaynak": "windows_masaustu",
            },
        )

    def aktif_modulu_degistir(
        self,
        modul_kodu: str,
    ) -> RuntimeResponse:
        return self._request(
            "POST",
            "/api/v2/modul-kartlari/aktif",
            {
                "modul_kodu": modul_kodu,
                "kaynak": "windows_masaustu",
            },
        )

    def modul_durumunu_degistir(
        self,
        modul_kodu: str,
        durum: str,
    ) -> RuntimeResponse:
        return self._request(
            "POST",
            "/api/v2/modul-kartlari/durum",
            {
                "modul_kodu": modul_kodu,
                "durum": durum,
                "kaynak": "windows_masaustu",
            },
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> RuntimeResponse:
        data = None
        headers = {
            "Accept": "application/json",
        }

        if payload is not None:
            data = json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8")

            headers["Content-Type"] = "application/json"

        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                body = json.loads(
                    response.read().decode("utf-8")
                )

            return RuntimeResponse(
                basarili=True,
                veri=body,
            )

        except HTTPError as exc:
            return RuntimeResponse(
                basarili=False,
                veri={},
                hata=f"HTTP {exc.code}",
            )

        except URLError:
            return RuntimeResponse(
                basarili=False,
                veri={},
                hata="Çalışma alanına ulaşılamıyor.",
            )

        except (OSError, ValueError, json.JSONDecodeError):
            return RuntimeResponse(
                basarili=False,
                veri={},
                hata="Geçersiz çalışma alanı yanıtı.",
            )

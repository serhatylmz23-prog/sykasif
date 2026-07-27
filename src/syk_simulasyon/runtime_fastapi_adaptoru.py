from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .runtime_http_api import RuntimeHttpApi


@dataclass(frozen=True)
class RuntimeHttpYaniti:
    durum_kodu: int
    icerik_turu: str
    govde: str


class RuntimeFastApiAdaptoru:
    """Runtime HTTP API çıktısını web çatısından bağımsız yanıta dönüştürür."""

    def __init__(self, api: RuntimeHttpApi) -> None:
        self._api = api
        self._rotalar: dict[str, Callable[[], tuple[int, str]]] = {
            "/runtime/json": self._api.json,
            "/runtime/csv": self._api.csv,
            "/runtime/html": self._api.html,
            "/runtime/markdown": self._api.markdown,
            "/runtime/xml": self._api.xml,
            "/runtime/yaml": self._api.yaml,
        }
        self._icerik_turleri = {
            "/runtime/json": "application/json; charset=utf-8",
            "/runtime/csv": "text/csv; charset=utf-8",
            "/runtime/html": "text/html; charset=utf-8",
            "/runtime/markdown": "text/markdown; charset=utf-8",
            "/runtime/xml": "application/xml; charset=utf-8",
            "/runtime/yaml": "application/yaml; charset=utf-8",
        }

    def rota_isle(self, yol: str) -> RuntimeHttpYaniti:
        isleyici = self._rotalar.get(yol)

        if isleyici is None:
            return RuntimeHttpYaniti(
                durum_kodu=404,
                icerik_turu="text/plain; charset=utf-8",
                govde="Kaynak bulunamadı",
            )

        durum_kodu, govde = isleyici()

        return RuntimeHttpYaniti(
            durum_kodu=durum_kodu,
            icerik_turu=self._icerik_turleri[yol],
            govde=govde,
        )
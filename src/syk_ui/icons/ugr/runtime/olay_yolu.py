"""UGR dinamik ikon olay yönlendiricisi."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IkonRuntimeOlayi:
    """Runtime olay taşıyıcısı."""

    olay_turu: str
    ikon_kimligi: str
    veri: dict[str, Any]


OlayDinleyici = Callable[[IkonRuntimeOlayi], None]


class IkonRuntimeOlayYolu:
    """İkon olaylarını dinleyicilere yayınlar."""

    def __init__(self) -> None:
        self._dinleyiciler: dict[
            str,
            list[OlayDinleyici],
        ] = defaultdict(list)

    def abone_ol(
        self,
        olay_turu: str,
        dinleyici: OlayDinleyici,
    ) -> None:
        """Olay türüne dinleyici ekler."""

        self._dinleyiciler[olay_turu].append(
            dinleyici
        )

    def abonelikten_cik(
        self,
        olay_turu: str,
        dinleyici: OlayDinleyici,
    ) -> None:
        """Dinleyiciyi olay türünden çıkarır."""

        dinleyiciler = self._dinleyiciler.get(
            olay_turu,
            [],
        )

        if dinleyici in dinleyiciler:
            dinleyiciler.remove(
                dinleyici
            )

    def yayinla(
        self,
        olay: IkonRuntimeOlayi,
    ) -> None:
        """Olayı kayıtlı dinleyicilere gönderir."""

        for dinleyici in tuple(
            self._dinleyiciler.get(
                olay.olay_turu,
                [],
            )
        ):
            dinleyici(olay)

        for dinleyici in tuple(
            self._dinleyiciler.get(
                "*",
                [],
            )
        ):
            dinleyici(olay)

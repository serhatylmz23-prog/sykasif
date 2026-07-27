from __future__ import annotations

from .runtime_durumu import RuntimeDurumu
from .runtime_olay_adaptoru import runtime_durumunu_olaya_cevir


class RuntimeServisi:
    """SyKaşif ortak runtime servisidir."""

    def __init__(self) -> None:
        self._durum = RuntimeDurumu()

    @property
    def durum(self) -> RuntimeDurumu:
        return self._durum

    def gorunum(self) -> dict[str, object]:
        return self._durum.gorunum()

    def olay_uret(
        self,
        *,
        arastirma_kimligi: str,
        deney_numarasi: str | None = None,
    ):
        return runtime_durumunu_olaya_cevir(
            self._durum,
            arastirma_kimligi=arastirma_kimligi,
            deney_numarasi=deney_numarasi,
        )
from __future__ import annotations

from .runtime_bildirim import RuntimeBildirimMerkezi

from collections import deque
from pathlib import Path
from typing import Deque

from .olay_omurgasi import Olay
from .runtime_olay_gunlugu import RuntimeOlayGunlugu
from .runtime_durumu import RuntimeDurumu
from .runtime_olay_adaptoru import runtime_durumunu_olaya_cevir


class RuntimeServisi:
    """SyKaşif ortak runtime servisidir."""

    OLAY_GECMISI_KAPASITESI = 100

    def __init__(
        self,
        olay_gunlugu_yolu: str | Path | None = None,
    ) -> None:
        self._durum = RuntimeDurumu()
        self._olay_gunlugu = (
            RuntimeOlayGunlugu(olay_gunlugu_yolu)
            if olay_gunlugu_yolu is not None
            else None
        )

        kalici_gecmis = (
            self._olay_gunlugu.olaylari_oku()
            if self._olay_gunlugu is not None
            else ()
        )

        self._olay_gecmisi: Deque[Olay] = deque(
            kalici_gecmis,
            maxlen=self.OLAY_GECMISI_KAPASITESI,
        )
        self._bildirim_merkezi = RuntimeBildirimMerkezi()
    @property
    def durum(self) -> RuntimeDurumu:
        return self._durum
    @property
    def bildirim_merkezi(self) -> RuntimeBildirimMerkezi:
        return self._bildirim_merkezi

    def gorunum(self) -> dict[str, object]:
        return self._durum.gorunum()

    def olay_uret(
        self,
        *,
        arastirma_kimligi: str,
        deney_numarasi: str | None = None,
    ) -> Olay:
        olay = runtime_durumunu_olaya_cevir(
            self._durum,
            arastirma_kimligi=arastirma_kimligi,
            deney_numarasi=deney_numarasi,
        )
        if self._olay_gunlugu is not None:
            self._olay_gunlugu.ekle(olay)

        self._olay_gecmisi.append(olay)
        self._bildirim_merkezi.yayinla(olay)
        return olay

    def olay_gecmisi(self) -> tuple[Olay, ...]:
        return tuple(self._olay_gecmisi)

    def son_olay(self) -> Olay | None:
        if not self._olay_gecmisi:
            return None
        return self._olay_gecmisi[-1]

    def olay_gecmisini_temizle(self) -> None:
        self._olay_gecmisi.clear()
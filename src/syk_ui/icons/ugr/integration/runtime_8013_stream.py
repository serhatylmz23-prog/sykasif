"""UGR Runtime 8013 SSE yayın katmanı."""

from __future__ import annotations

import json
from collections.abc import Iterator
from threading import Event
from typing import Any

from .runtime_8013_events import (
    UgrCanliIkonOlayi,
    UgrCanliOlayTuru,
)
from .runtime_8013_store import (
    UgrRuntime8013EventStore,
)


def sse_verisi(
    olay: UgrCanliIkonOlayi,
) -> str:
    """Bir olayı Server-Sent Events biçimine çevirir."""

    json_metin = json.dumps(
        olay.json_verisi(),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return (
        f"id: {olay.olay_kimligi}\n"
        f"event: {olay.olay_turu.value}\n"
        f"data: {json_metin}\n\n"
    )


class UgrRuntime8013EventStream:
    """Runtime 8013 için canlı SSE olay akışı."""

    def __init__(
        self,
        olay_deposu: UgrRuntime8013EventStore,
        *,
        kalp_atisi_suresi: float = 10.0,
    ) -> None:
        if kalp_atisi_suresi <= 0:
            raise ValueError(
                "kalp_atisi_suresi sıfırdan büyük olmalıdır."
            )

        self.olay_deposu = olay_deposu
        self.kalp_atisi_suresi = (
            kalp_atisi_suresi
        )

    def akisi_uret(
        self,
        *,
        durdurma_olayi: Event | None = None,
        baslangic_sirasi: int = 0,
    ) -> Iterator[str]:
        """SSE uyumlu kesintisiz metin akışı üretir."""

        durdurma = (
            durdurma_olayi
            or Event()
        )

        sira = baslangic_sirasi

        while not durdurma.is_set():
            yeni_sira, olaylar = (
                self.olay_deposu.bekle(
                    onceki_sira=sira,
                    zaman_asimi=(
                        self.kalp_atisi_suresi
                    ),
                )
            )

            if olaylar:
                for olay in olaylar:
                    yield sse_verisi(
                        olay
                    )

                sira = yeni_sira
                continue

            kalp_atisi = UgrCanliIkonOlayi(
                olay_turu=(
                    UgrCanliOlayTuru
                    .KALP_ATISI
                ),
                veri={
                    "durum": "baglanti_acik",
                    "son_sira": yeni_sira,
                },
            )

            yield sse_verisi(
                kalp_atisi
            )

    def tek_seferlik_akisi_uret(
        self,
        olaylar: tuple[
            UgrCanliIkonOlayi,
            ...,
        ],
    ) -> str:
        """Test ve HTTP yanıtı için toplu SSE metni üretir."""

        return "".join(
            sse_verisi(olay)
            for olay in olaylar
        )

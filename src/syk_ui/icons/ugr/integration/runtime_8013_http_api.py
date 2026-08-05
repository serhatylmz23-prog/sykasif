"""UGR Runtime 8013 HTTP bağımsız uç nokta sözleşmesi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
)

from .runtime_8013_bridge import (
    UgrRuntime8013Bridge,
)
from .runtime_8013_stream import (
    UgrRuntime8013EventStream,
)


@dataclass(frozen=True, slots=True)
class UgrHttpYaniti:
    """Sunucu adaptörlerinden bağımsız HTTP yanıt modeli."""

    durum_kodu: int
    icerik_turu: str
    govde: Any
    basliklar: dict[str, str]


class UgrRuntime8013HttpApi:
    """Mevcut UI sunucusuna bağlanabilecek API sözleşmesi."""

    def __init__(
        self,
        bridge: UgrRuntime8013Bridge,
    ) -> None:
        self.bridge = bridge

        self.stream = (
            UgrRuntime8013EventStream(
                bridge.olay_deposu
            )
        )

    def saglik(self) -> UgrHttpYaniti:
        """UGR canlı runtime sağlık yanıtı."""

        ozet = self.bridge.durum_ozeti()

        durum_kodu = (
            200
            if ozet["baslatildi"]
            else 503
        )

        return UgrHttpYaniti(
            durum_kodu=durum_kodu,
            icerik_turu=(
                "application/json; charset=utf-8"
            ),
            govde=ozet,
            basliklar={
                "Cache-Control": "no-store",
            },
        )

    def snapshot(self) -> UgrHttpYaniti:
        """215 ikonun anlık durumunu döndürür."""

        return UgrHttpYaniti(
            durum_kodu=200,
            icerik_turu=(
                "application/json; charset=utf-8"
            ),
            govde=self.bridge.snapshot(),
            basliklar={
                "Cache-Control": "no-store",
            },
        )

    def ikon(
        self,
        ikon_kimligi: str,
    ) -> UgrHttpYaniti:
        """Tek ikon render verisini döndürür."""

        return UgrHttpYaniti(
            durum_kodu=200,
            icerik_turu=(
                "application/json; charset=utf-8"
            ),
            govde=(
                self.bridge
                .ikon_render_verisi(
                    ikon_kimligi
                )
            ),
            basliklar={
                "Cache-Control": "no-store",
            },
        )

    def ikon_durumu(
        self,
        ikon_kimligi: str,
        *,
        durum: str,
        neden: str,
        zorla: bool = False,
    ) -> UgrHttpYaniti:
        """HTTP üzerinden ikon durumunu değiştirir."""

        sonuc = (
            self.bridge
            .ikon_durumu_degistir(
                ikon_kimligi,
                yeni_durum=(
                    IkonCalismaDurumu(
                        durum
                    )
                ),
                neden=neden,
                zorla=zorla,
            )
        )

        return UgrHttpYaniti(
            durum_kodu=200,
            icerik_turu=(
                "application/json; charset=utf-8"
            ),
            govde=sonuc,
            basliklar={
                "Cache-Control": "no-store",
            },
        )

    def ikon_gorunumu(
        self,
        ikon_kimligi: str,
        *,
        gorunum_modu: str,
    ) -> UgrHttpYaniti:
        """HTTP üzerinden 2B, 3B veya AR görünümü uygular."""

        sonuc = (
            self.bridge
            .ikon_gorunumu_degistir(
                ikon_kimligi,
                IkonGorunumModu(
                    gorunum_modu
                ),
            )
        )

        return UgrHttpYaniti(
            durum_kodu=200,
            icerik_turu=(
                "application/json; charset=utf-8"
            ),
            govde=sonuc,
            basliklar={
                "Cache-Control": "no-store",
            },
        )

    def son_olaylar(
        self,
        adet: int = 20,
    ) -> UgrHttpYaniti:
        """Son canlı ikon olaylarını JSON olarak döndürür."""

        olaylar = [
            olay.json_verisi()
            for olay in (
                self.bridge
                .olay_deposu
                .son(adet)
            )
        ]

        return UgrHttpYaniti(
            durum_kodu=200,
            icerik_turu=(
                "application/json; charset=utf-8"
            ),
            govde={
                "olay_sayisi": len(
                    olaylar
                ),
                "olaylar": olaylar,
            },
            basliklar={
                "Cache-Control": "no-store",
            },
        )

    def sse_gecmisi(
        self,
        adet: int = 20,
    ) -> UgrHttpYaniti:
        """Son olayları SSE biçiminde döndürür."""

        olaylar = (
            self.bridge
            .olay_deposu
            .son(adet)
        )

        govde = (
            self.stream
            .tek_seferlik_akisi_uret(
                olaylar
            )
        )

        return UgrHttpYaniti(
            durum_kodu=200,
            icerik_turu=(
                "text/event-stream; charset=utf-8"
            ),
            govde=govde,
            basliklar={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

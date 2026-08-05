"""UGR dinamik ikon durum makinesi."""

from __future__ import annotations

from .durumlar import (
    IkonCalismaDurumu,
    IkonOnceligi,
)
from .gecis_kurallari import gecis_izinli_mi
from .modeller import (
    IkonDurumDegisimi,
    IkonRuntimeKaydi,
)


class GecersizIkonDurumGecisi(ValueError):
    """İzin verilmeyen ikon durum geçişi."""


class IkonDurumMakinesi:
    """İkon durum geçişlerini merkezi kurallarla uygular."""

    def gecis_yap(
        self,
        kayit: IkonRuntimeKaydi,
        *,
        yeni_durum: IkonCalismaDurumu,
        neden: str,
        oncelik: IkonOnceligi = IkonOnceligi.NORMAL,
        ek_veri: dict[str, object] | None = None,
        zorla: bool = False,
    ) -> IkonDurumDegisimi:
        """Kuralları denetleyerek durum geçişini uygular."""

        if not zorla and not gecis_izinli_mi(
            kayit.durum,
            yeni_durum,
        ):
            raise GecersizIkonDurumGecisi(
                f"İzin verilmeyen ikon geçişi: "
                f"{kayit.durum.value} -> {yeni_durum.value}"
            )

        return kayit.durum_degistir(
            yeni_durum=yeni_durum,
            neden=neden,
            oncelik=oncelik,
            ek_veri=dict(ek_veri or {}),
        )

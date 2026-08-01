from dataclasses import dataclass, field


@dataclass
class DegerlendirmeKaydi:

    veri_kimligi: str

    kaynak_sayisi: int = 0

    destekleyen_bulgu: int = 0

    celiski_sayisi: int = 0

    uzman_onerileri: list[str] = field(
        default_factory=list
    )


class GuvenHesapMotoru:


    def guven_hesapla(
        self,
        kayit: DegerlendirmeKaydi,
    ) -> float:

        puan = 0.0

        if kayit.kaynak_sayisi > 0:
            puan += 30

        if kayit.destekleyen_bulgu > 0:
            puan += (
                min(
                    kayit.destekleyen_bulgu,
                    10,
                )
                * 5
            )

        puan -= (
            kayit.celiski_sayisi
            * 5
        )

        if puan < 0:
            return 0.0

        if puan > 100:
            return 100.0

        return puan


    def celiski_degerlendir(
        self,
        kayit: DegerlendirmeKaydi,
    ) -> dict:

        return {
            "veri": kayit.veri_kimligi,
            "celiski_var": (
                kayit.celiski_sayisi > 0
            ),
            "incelenmeli": (
                kayit.celiski_sayisi > 0
            ),
        }

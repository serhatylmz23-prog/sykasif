from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class KanitKaydi:

    kanit_kimligi: str
    veri_turu: str
    kaynak: str

    gerekli_mi: bool = True

    durum: str = "aktif"

    etiketler: list[str] = field(
        default_factory=list
    )

    uzman_incelemeleri: list[str] = field(
        default_factory=list
    )

    arsiv_zamani: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )


class KanitArsivYoneticisi:


    def __init__(self):
        self.kayitlar = {}


    def kanit_kaydet(
        self,
        kanit: KanitKaydi,
    ):

        self.kayitlar[
            kanit.kanit_kimligi
        ] = kanit

        return kanit


    def etiket_ekle(
        self,
        kanit_kimligi: str,
        etiket: str,
    ):

        self.kayitlar[
            kanit_kimligi
        ].etiketler.append(
            etiket
        )


    def uzman_incelemesi_ekle(
        self,
        kanit_kimligi: str,
        yorum: str,
    ):

        self.kayitlar[
            kanit_kimligi
        ].uzman_incelemeleri.append(
            yorum
        )


    def gereksiz_arsivden_cikar(
        self,
        kanit_kimligi: str,
    ):

        kanit = self.kayitlar[
            kanit_kimligi
        ]

        kanit.gerekli_mi = False
        kanit.durum = "arsiv_disari"


    def aktif_kayitlari_getir(
        self,
    ):

        return [
            k
            for k in self.kayitlar.values()
            if k.durum == "aktif"
        ]

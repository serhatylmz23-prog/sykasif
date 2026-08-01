from dataclasses import dataclass, field
from datetime import datetime, timezone


class KanitHatasi(Exception):
    pass


@dataclass
class KaynakKaydi:

    kaynak_kimligi: str
    kaynak_turu: str
    aciklama: str

    guven_puani: float = 0.0

    dogrulama_durumu: str = "bekliyor"

    celiski_kayitlari: list[str] = field(
        default_factory=list
    )

    uzman_notlari: list[str] = field(
        default_factory=list
    )

    olusturma_zamani: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )


class KanitKaynakYoneticisi:


    def __init__(self):
        self.kaynaklar = {}


    def kaynak_ekle(
        self,
        kaynak: KaynakKaydi,
    ):
        self.kaynaklar[
            kaynak.kaynak_kimligi
        ] = kaynak

        return kaynak


    def guven_puani_guncelle(
        self,
        kaynak_kimligi: str,
        puan: float,
    ):

        if puan < 0 or puan > 100:
            raise KanitHatasi(
                "Guven puani 0-100 arasinda olmali."
            )

        kaynak = self.kaynaklar[
            kaynak_kimligi
        ]

        kaynak.guven_puani = puan


    def dogrulama_ekle(
        self,
        kaynak_kimligi: str,
        durum: str,
    ):

        kaynak = self.kaynaklar[
            kaynak_kimligi
        ]

        kaynak.dogrulama_durumu = durum


    def celiski_ekle(
        self,
        kaynak_kimligi: str,
        aciklama: str,
    ):

        kaynak = self.kaynaklar[
            kaynak_kimligi
        ]

        kaynak.celiski_kayitlari.append(
            aciklama
        )


    def uzman_notu_ekle(
        self,
        kaynak_kimligi: str,
        not_: str,
    ):

        kaynak = self.kaynaklar[
            kaynak_kimligi
        ]

        kaynak.uzman_notlari.append(
            not_
        )

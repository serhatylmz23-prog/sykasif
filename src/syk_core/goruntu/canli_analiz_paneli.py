from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CanliGoruntuAkisi:

    akis_kimligi: str

    kaynak_cihaz: str

    aktif: bool = True

    kare_sayisi: int = 0

    anlik_kayitlar: list[str] = field(
        default_factory=list
    )

    supheli_alanlar: list[dict] = field(
        default_factory=list
    )

    operator_notlari: list[str] = field(
        default_factory=list
    )

    olusturma_zamani: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )


class CanliAnalizPaneli:


    def __init__(self):
        self.akislar = {}


    def akis_baslat(
        self,
        akis: CanliGoruntuAkisi,
    ):

        self.akislar[
            akis.akis_kimligi
        ] = akis

        return akis


    def kare_kaydet(
        self,
        akis_kimligi: str,
        aciklama: str,
    ):

        akis = self.akislar[
            akis_kimligi
        ]

        akis.kare_sayisi += 1

        akis.anlik_kayitlar.append(
            aciklama
        )


    def supheli_alan_bildir(
        self,
        akis_kimligi: str,
        aciklama: str,
    ):

        self.akislar[
            akis_kimligi
        ].supheli_alanlar.append(
            {
                "aciklama": aciklama,
                "durum": "uzman_incelemesi",
            }
        )


    def operator_notu_ekle(
        self,
        akis_kimligi: str,
        not_: str,
    ):

        self.akislar[
            akis_kimligi
        ].operator_notlari.append(
            not_
        )


    def analiz_durumu(
        self,
        akis_kimligi: str,
    ):

        akis = self.akislar[
            akis_kimligi
        ]

        return {
            "aktif": akis.aktif,
            "kare": akis.kare_sayisi,
            "supheli_alan": len(
                akis.supheli_alanlar
            ),
        }


    def durdur(
        self,
        akis_kimligi: str,
    ):

        self.akislar[
            akis_kimligi
        ].aktif = False

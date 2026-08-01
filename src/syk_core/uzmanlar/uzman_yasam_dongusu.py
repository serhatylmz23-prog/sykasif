from dataclasses import dataclass, field
from datetime import datetime, timezone


class UzmanYasamHatasi(Exception):
    pass


@dataclass
class UzmanYasamKaydi:

    uzman_kimligi: str
    uzman_adi: str
    bilim_ailesi: str

    durum: str = "aktif"

    egitim_kaydi: list[str] = field(
        default_factory=list
    )

    deneyim_kaydi: list[str] = field(
        default_factory=list
    )

    aktarilan_bilgi: list[str] = field(
        default_factory=list
    )

    olusturma_zamani: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )


class UzmanYasamYoneticisi:

    def __init__(self):
        self.uzmanlar = {}


    def uzman_olustur(
        self,
        kayit: UzmanYasamKaydi,
    ):
        self.uzmanlar[
            kayit.uzman_kimligi
        ] = kayit

        return kayit


    def egitim_ekle(
        self,
        uzman_kimligi: str,
        bilgi: str,
    ):

        uzman = self.uzmanlar[
            uzman_kimligi
        ]

        uzman.egitim_kaydi.append(
            bilgi
        )


    def deneyim_ekle(
        self,
        uzman_kimligi: str,
        deneyim: str,
    ):

        uzman = self.uzmanlar[
            uzman_kimligi
        ]

        uzman.deneyim_kaydi.append(
            deneyim
        )


    def bilgiyi_aktar(
        self,
        eski_uzman: str,
        yeni_uzman: str,
        bilgi: str,
    ):

        eski = self.uzmanlar[
            eski_uzman
        ]

        yeni = self.uzmanlar[
            yeni_uzman
        ]

        yeni.aktarilan_bilgi.append(
            bilgi
        )

        eski.deneyim_kaydi.append(
            "aktarim:"+bilgi
        )


    def emekliye_ayir(
        self,
        uzman_kimligi: str,
    ):

        uzman = self.uzmanlar[
            uzman_kimligi
        ]

        uzman.durum = "emekli"


    def aktif_mi(
        self,
        uzman_kimligi: str,
    ) -> bool:

        return (
            self.uzmanlar[
                uzman_kimligi
            ].durum
            ==
            "aktif"
        )

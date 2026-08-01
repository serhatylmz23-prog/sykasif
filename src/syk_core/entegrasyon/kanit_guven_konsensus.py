from dataclasses import dataclass, field


@dataclass
class KanitDegerlendirme:

    olay_kimligi: str

    kanitlar: list[str] = field(
        default_factory=list
    )

    guven_puani: float = 0.0

    konsensus_puani: float = 0.0

    durum: str = "beklemede"



class KanitGuvenKonsensusBaglantisi:


    def __init__(self):

        self.kayitlar = {}


    def olay_kaydet(
        self,
        olay_kimligi: str,
    ):

        kayit = KanitDegerlendirme(
            olay_kimligi
        )

        self.kayitlar[
            olay_kimligi
        ] = kayit

        return kayit


    def kanit_ekle(
        self,
        olay_kimligi: str,
        kanit: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].kanitlar.append(
            kanit
        )


    def guven_puani_ekle(
        self,
        olay_kimligi: str,
        puan: float,
    ):

        self.kayitlar[
            olay_kimligi
        ].guven_puani = puan


    def konsensus_puani_ekle(
        self,
        olay_kimligi: str,
        puan: float,
    ):

        self.kayitlar[
            olay_kimligi
        ].konsensus_puani = puan


    def degerlendir(
        self,
        olay_kimligi: str,
    ):

        kayit = self.kayitlar[
            olay_kimligi
        ]

        toplam = (
            kayit.guven_puani
            +
            kayit.konsensus_puani
        ) / 2


        if toplam >= 80:
            kayit.durum = "guclu_destek"

        elif toplam >= 50:
            kayit.durum = "inceleme_gerekli"

        else:
            kayit.durum = "zayif_destek"


        return kayit


    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

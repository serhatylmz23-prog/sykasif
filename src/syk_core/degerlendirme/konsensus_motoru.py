from dataclasses import dataclass, field


@dataclass
class KonsensusKaydi:

    degerlendirme_kimligi: str

    kaynak_guven_puani: float = 0.0

    uzman_destek_sayisi: int = 0

    uzman_red_sayisi: int = 0

    celiski_sayisi: int = 0

    uzman_notlari: list[str] = field(
        default_factory=list
    )

    konsensus_puani: float = 0.0

    durum: str = "beklemede"



class KonsensusMotoru:


    def __init__(self):
        self.kayitlar = {}


    def kaydet(
        self,
        kayit: KonsensusKaydi,
    ):
        self.kayitlar[
            kayit.degerlendirme_kimligi
        ] = kayit

        return kayit


    def uzman_destek_ekle(
        self,
        kimlik: str,
        not_: str,
    ):

        kayit = self.kayitlar[kimlik]

        kayit.uzman_destek_sayisi += 1

        kayit.uzman_notlari.append(
            not_
        )


    def uzman_red_ekle(
        self,
        kimlik: str,
        not_: str,
    ):

        kayit = self.kayitlar[kimlik]

        kayit.uzman_red_sayisi += 1

        kayit.uzman_notlari.append(
            not_
        )


    def celiski_ekle(
        self,
        kimlik: str,
    ):

        self.kayitlar[
            kimlik
        ].celiski_sayisi += 1


    def hesapla(
        self,
        kimlik: str,
    ):

        kayit = self.kayitlar[kimlik]

        puan = kayit.kaynak_guven_puani

        puan += (
            kayit.uzman_destek_sayisi * 10
        )

        puan -= (
            kayit.uzman_red_sayisi * 10
        )

        puan -= (
            kayit.celiski_sayisi * 5
        )


        if puan < 0:
            puan = 0


        if puan > 100:
            puan = 100


        kayit.konsensus_puani = puan


        if puan >= 80:
            kayit.durum = "guclu_destek"

        elif puan >= 50:
            kayit.durum = "inceleme_gerekli"

        else:
            kayit.durum = "zayif_destek"


        return kayit


    def getir(
        self,
        kimlik: str,
    ):

        return self.kayitlar.get(
            kimlik
        )

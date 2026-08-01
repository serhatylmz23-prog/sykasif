from dataclasses import dataclass, field



@dataclass
class UzmanSonucu:

    uzman_adi: str

    sonuc: str

    puan: float



@dataclass
class KanitAgKaydi:

    olay_kimligi: str

    kanitlar: list[str] = field(
        default_factory=list
    )

    uzman_sonuclari: list[UzmanSonucu] = field(
        default_factory=list
    )



class UzmanSonucAgMotoru:


    def __init__(self):

        self.kayitlar = {}



    def olay_olustur(
        self,
        olay_kimligi: str,
    ):

        kayit = KanitAgKaydi(
            olay_kimligi
        )

        self.kayitlar[
            olay_kimligi
        ] = kayit


        return kayit



    def kanit_bagla(
        self,
        olay_kimligi: str,
        kanit: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].kanitlar.append(
            kanit
        )



    def uzman_sonucu_ekle(
        self,
        olay_kimligi: str,
        uzman_adi: str,
        sonuc: str,
        puan: float,
    ):

        self.kayitlar[
            olay_kimligi
        ].uzman_sonuclari.append(
            UzmanSonucu(
                uzman_adi,
                sonuc,
                puan,
            )
        )



    def konsensus_hesapla(
        self,
        olay_kimligi: str,
    ):

        kayit = self.kayitlar[
            olay_kimligi
        ]


        if not kayit.uzman_sonuclari:

            return 0


        toplam = sum(
            x.puan
            for x in kayit.uzman_sonuclari
        )


        return (
            toplam
            /
            len(
                kayit.uzman_sonuclari
            )
        )



    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

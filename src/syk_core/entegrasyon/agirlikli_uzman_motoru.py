from dataclasses import dataclass, field



@dataclass
class UzmanDugumu:

    uzman_adi: str

    sonuc: str

    puan: float

    agirlik: float



@dataclass
class KanitGrafikKaydi:

    olay_kimligi: str

    kanitlar: list[str] = field(
        default_factory=list
    )

    uzmanlar: list[UzmanDugumu] = field(
        default_factory=list
    )



class AgirlikliUzmanKararMotoru:


    def __init__(self):

        self.kayitlar = {}



    def olay_olustur(
        self,
        olay_kimligi: str,
    ):

        kayit = KanitGrafikKaydi(
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



    def uzman_ekle(
        self,
        olay_kimligi: str,
        uzman_adi: str,
        sonuc: str,
        puan: float,
        agirlik: float,
    ):

        dugum = UzmanDugumu(
            uzman_adi,
            sonuc,
            puan,
            agirlik,
        )

        self.kayitlar[
            olay_kimligi
        ].uzmanlar.append(
            dugum
        )



    def agirlikli_konsensus(
        self,
        olay_kimligi: str,
    ):

        kayit = self.kayitlar[
            olay_kimligi
        ]


        if not kayit.uzmanlar:

            return 0


        toplam = 0

        agirlik_toplam = 0


        for uzman in kayit.uzmanlar:

            toplam += (
                uzman.puan
                *
                uzman.agirlik
            )

            agirlik_toplam += (
                uzman.agirlik
            )


        if agirlik_toplam == 0:

            return 0


        return (
            toplam
            /
            agirlik_toplam
        )



    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

from dataclasses import dataclass, field


@dataclass
class TekOlayDegerlendirme:

    olay_kimligi: str

    kanitlar: list[str] = field(
        default_factory=list
    )

    goruntuler: list[str] = field(
        default_factory=list
    )

    materyaller: list[str] = field(
        default_factory=list
    )

    konsensuslar: list[str] = field(
        default_factory=list
    )

    durum: str = "beklemede"



class TekOlayAkisYoneticisi:


    def __init__(self):

        self.kayitlar = {}


    def olay_olustur(
        self,
        olay_kimligi: str,
    ):

        kayit = TekOlayDegerlendirme(
            olay_kimligi
        )

        self.kayitlar[
            olay_kimligi
        ] = kayit

        return kayit


    def kanit_ekle(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].kanitlar.append(
            veri
        )


    def goruntu_ekle(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].goruntuler.append(
            veri
        )


    def materyal_ekle(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].materyaller.append(
            veri
        )


    def konsensus_ekle(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].konsensuslar.append(
            veri
        )


    def tamamla(
        self,
        olay_kimligi: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].durum = "degerlendirildi"


    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

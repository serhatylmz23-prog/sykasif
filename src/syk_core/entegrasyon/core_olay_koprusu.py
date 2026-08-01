from dataclasses import dataclass, field


@dataclass
class CoreOlaySonucu:

    olay_kimligi: str

    kanit_kaydi: list[str] = field(
        default_factory=list
    )

    goruntu_kaydi: list[str] = field(
        default_factory=list
    )

    materyal_kaydi: list[str] = field(
        default_factory=list
    )

    konsensus_kaydi: list[str] = field(
        default_factory=list
    )

    durum: str = "beklemede"



class CoreOlayKoprusu:


    def __init__(self):
        self.sonuclar = {}


    def olay_baslat(
        self,
        olay_kimligi: str,
    ):

        sonuc = CoreOlaySonucu(
            olay_kimligi
        )

        self.sonuclar[
            olay_kimligi
        ] = sonuc

        return sonuc


    def kanit_bagla(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.sonuclar[
            olay_kimligi
        ].kanit_kaydi.append(
            veri
        )


    def goruntu_bagla(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.sonuclar[
            olay_kimligi
        ].goruntu_kaydi.append(
            veri
        )


    def materyal_bagla(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.sonuclar[
            olay_kimligi
        ].materyal_kaydi.append(
            veri
        )


    def konsensus_bagla(
        self,
        olay_kimligi: str,
        veri: str,
    ):

        self.sonuclar[
            olay_kimligi
        ].konsensus_kaydi.append(
            veri
        )


    def tamamla(
        self,
        olay_kimligi: str,
    ):

        self.sonuclar[
            olay_kimligi
        ].durum = "hazir"


    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.sonuclar.get(
            olay_kimligi
        )

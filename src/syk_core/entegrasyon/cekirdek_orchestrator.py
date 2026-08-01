from dataclasses import dataclass, field


@dataclass
class CekirdekDegerlendirmeSonucu:

    olay_kimligi: str

    kanitlar: list[str] = field(
        default_factory=list
    )

    goruntu_sonuclari: list[str] = field(
        default_factory=list
    )

    materyal_sonuclari: list[str] = field(
        default_factory=list
    )

    guven_puani: float = 0.0

    konsensus_puani: float = 0.0

    durum: str = "beklemede"



class CekirdekDegerlendirmeOrkestratoru:


    def __init__(self):

        self.kayitlar = {}


    def olay_baslat(
        self,
        olay_kimligi: str,
    ):

        sonuc = CekirdekDegerlendirmeSonucu(
            olay_kimligi
        )

        self.kayitlar[
            olay_kimligi
        ] = sonuc

        return sonuc


    def kanit_aktar(
        self,
        olay_kimligi: str,
        kanit: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].kanitlar.append(
            kanit
        )


    def goruntu_aktar(
        self,
        olay_kimligi: str,
        sonuc: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].goruntu_sonuclari.append(
            sonuc
        )


    def materyal_aktar(
        self,
        olay_kimligi: str,
        sonuc: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].materyal_sonuclari.append(
            sonuc
        )


    def puanlari_aktar(
        self,
        olay_kimligi: str,
        guven: float,
        konsensus: float,
    ):

        kayit = self.kayitlar[
            olay_kimligi
        ]

        kayit.guven_puani = guven
        kayit.konsensus_puani = konsensus


    def tamamla(
        self,
        olay_kimligi: str,
    ):

        kayit = self.kayitlar[
            olay_kimligi
        ]

        ortalama = (
            kayit.guven_puani
            +
            kayit.konsensus_puani
        ) / 2


        if ortalama >= 80:
            kayit.durum = "guclu_destek"

        elif ortalama >= 50:
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

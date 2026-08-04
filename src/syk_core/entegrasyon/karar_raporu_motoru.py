from dataclasses import dataclass, field



@dataclass
class GerekceBloku:

    baslik: str

    aciklama: str



@dataclass
class KararRaporu:

    olay_kimligi: str

    karar: str

    guven_puani: float

    gerekceler: list[GerekceBloku] = field(
        default_factory=list
    )



class KararRaporuMotoru:


    def olustur(
        self,
        olay_kimligi: str,
        karar: str,
        guven_puani: float,
        kanitlar: list[str],
        uzmanlar: list[str],
    ):


        gerekceler = []


        gerekceler.append(
            GerekceBloku(
                "KANIT_DURUMU",
                f"{len(kanitlar)} adet kanit baglandi"
            )
        )


        gerekceler.append(
            GerekceBloku(
                "UZMAN_DEGERLENDIRME",
                f"{len(uzmanlar)} uzman sonucu kullanildi"
            )
        )


        gerekceler.append(
            GerekceBloku(
                "GUVEN_SEVIYESI",
                f"Kalibre guven puani {guven_puani}"
            )
        )


        return KararRaporu(
            olay_kimligi,
            karar,
            guven_puani,
            gerekceler,
        )

from dataclasses import dataclass, field



@dataclass
class TamKanitPaketi:

    olay_kimligi: str

    kanitlar: list[str]

    uzman_sonuclari: list[str]

    karar: str

    guven_puani: float

    gerekceler: list[str]

    durum: str = "hazir"



class TekOlayRaporPaketleyici:


    def olustur(
        self,
        olay_kimligi: str,
        kanitlar: list[str],
        uzman_sonuclari: list[str],
        karar: str,
        guven_puani: float,
        gerekceler: list[str],
    ):


        return TamKanitPaketi(
            olay_kimligi,
            kanitlar,
            uzman_sonuclari,
            karar,
            guven_puani,
            gerekceler,
        )

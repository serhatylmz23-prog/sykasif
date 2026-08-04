from dataclasses import dataclass



@dataclass
class SonEntegrasyonSonucu:

    olay_kimligi: str

    kanit_sayisi: int

    uzman_sayisi: int

    karar: str

    guven_puani: float

    rapor_hashi: str

    teslim_muhru: str

    durum: str = "dogrulandi"



class SonMuhurEntegrasyonKontrolu:


    def kontrol_et(
        self,
        olay_kimligi: str,
        kanitlar: list,
        uzmanlar: list,
        karar: str,
        guven_puani: float,
        rapor_hashi: str,
        teslim_muhru: str,
    ):


        if not olay_kimligi:

            return None



        if not kanitlar:

            return None



        if not uzmanlar:

            return None



        if len(rapor_hashi) != 64:

            return None



        if len(teslim_muhru) != 64:

            return None



        return SonEntegrasyonSonucu(

            olay_kimligi,

            len(kanitlar),

            len(uzmanlar),

            karar,

            guven_puani,

            rapor_hashi,

            teslim_muhru,

        )

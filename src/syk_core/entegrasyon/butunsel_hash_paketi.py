from dataclasses import dataclass, field
import hashlib
import json



@dataclass
class ButunselHashKaydi:

    olay_kimligi: str

    paket_hashi: str

    durum: str = "kayitli"



class ButunselHashPaketi:


    def __init__(self):

        self.kayitlar = {}



    def paket_olustur(
        self,
        olay_kimligi: str,
        kanitlar: list[str],
        uzman_sonuclari: list[str],
        guven_puani: float,
        konsensus_puani: float,
    ):

        veri = {
            "olay_kimligi": olay_kimligi,
            "kanitlar": kanitlar,
            "uzman_sonuclari": uzman_sonuclari,
            "guven_puani": guven_puani,
            "konsensus_puani": konsensus_puani,
        }


        temiz_veri = json.dumps(
            veri,
            sort_keys=True,
            ensure_ascii=False,
        )


        hash_degeri = hashlib.sha256(
            temiz_veri.encode("utf-8")
        ).hexdigest()



        kayit = ButunselHashKaydi(
            olay_kimligi,
            hash_degeri,
        )


        self.kayitlar[
            olay_kimligi
        ] = kayit


        return kayit



    def dogrula(
        self,
        olay_kimligi: str,
        kanitlar: list[str],
        uzman_sonuclari: list[str],
        guven_puani: float,
        konsensus_puani: float,
    ):


        eski = self.kayitlar.get(
            olay_kimligi
        )


        if eski is None:
            return False


        veri = {
            "olay_kimligi": olay_kimligi,
            "kanitlar": kanitlar,
            "uzman_sonuclari": uzman_sonuclari,
            "guven_puani": guven_puani,
            "konsensus_puani": konsensus_puani,
        }


        temiz_veri = json.dumps(
            veri,
            sort_keys=True,
            ensure_ascii=False,
        )


        yeni_hash = hashlib.sha256(
            temiz_veri.encode("utf-8")
        ).hexdigest()


        return (
            yeni_hash
            ==
            eski.paket_hashi
        )



    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

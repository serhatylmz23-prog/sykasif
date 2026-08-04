from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timezone



@dataclass
class TeslimMuhurKaydi:

    olay_kimligi: str

    teslim_kimligi: str

    kanit_hashi: str

    rapor_hashi: str

    manifest_hashi: str

    zaman: str

    durum: str = "teslim_muhurlendi"



class TeslimMuhurZinciri:


    def __init__(self):

        self.kayitlar = {}



    def hash_uret(
        self,
        veri: dict,
    ):

        temiz = json.dumps(
            veri,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            temiz.encode("utf-8")
        ).hexdigest()



    def teslim_olustur(
        self,
        olay_kimligi: str,
        kanit_hashi: str,
        rapor_hashi: str,
        manifest_hashi: str,
    ):

        paket = {

            "olay_kimligi":
                olay_kimligi,

            "kanit_hashi":
                kanit_hashi,

            "rapor_hashi":
                rapor_hashi,

            "manifest_hashi":
                manifest_hashi,

        }


        teslim_hashi = self.hash_uret(
            paket
        )


        kayit = TeslimMuhurKaydi(

            olay_kimligi,

            teslim_hashi,

            kanit_hashi,

            rapor_hashi,

            manifest_hashi,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            olay_kimligi
        ] = kayit


        return kayit



    def dogrula(
        self,
        olay_kimligi: str,
    ):

        kayit = self.kayitlar.get(
            olay_kimligi
        )


        if kayit is None:

            return False


        tekrar = {

            "olay_kimligi":
                kayit.olay_kimligi,

            "kanit_hashi":
                kayit.kanit_hashi,

            "rapor_hashi":
                kayit.rapor_hashi,

            "manifest_hashi":
                kayit.manifest_hashi,

        }


        return (
            self.hash_uret(tekrar)
            ==
            kayit.teslim_kimligi
        )



    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

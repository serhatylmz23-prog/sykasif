from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSTeslimArsivKaydi:

    teslim_id: str
    rapor_id: str
    kanit_id: str
    arsiv_id: str
    sha256: str
    durum: str
    zaman: str



class VBPSTeslimArsivBaglantiMotoru:


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



    def bagla(
        self,
        teslim_id: str,
        rapor_id: str,
        kanit_id: str,
        arsiv_id: str,
    ):

        veri = {

            "teslim_id":
                teslim_id,

            "rapor_id":
                rapor_id,

            "kanit_id":
                kanit_id,

            "arsiv_id":
                arsiv_id,

        }


        sha256 = self.hash_uret(
            veri
        )


        kayit = VBPSTeslimArsivKaydi(

            teslim_id,

            rapor_id,

            kanit_id,

            arsiv_id,

            sha256,

            "TESLIM_ZINCIRI_HAZIR",

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            teslim_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSTeslimArsivKaydi,
    ):

        veri = {

            "teslim_id":
                kayit.teslim_id,

            "rapor_id":
                kayit.rapor_id,

            "kanit_id":
                kayit.kanit_id,

            "arsiv_id":
                kayit.arsiv_id,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

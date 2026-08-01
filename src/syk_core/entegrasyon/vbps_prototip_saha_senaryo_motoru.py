from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSahaSenaryoKaydi:

    senaryo_id: str
    cihaz: str
    veri: str
    analiz: str
    rapor: str
    arsiv: str
    sonuc: str
    sha256: str
    zaman: str



class VBPSPrototipSahaSenaryoMotoru:


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



    def calistir(
        self,
        senaryo_id: str,
        cihaz: str,
        veri: str,
        analiz: str,
        rapor: str,
        arsiv: str,
    ):

        veri_seti = {

            "senaryo_id":
                senaryo_id,

            "cihaz":
                cihaz,

            "veri":
                veri,

            "analiz":
                analiz,

            "rapor":
                rapor,

            "arsiv":
                arsiv,

        }


        sha256 = self.hash_uret(
            veri_seti
        )


        adimlar = [
            veri,
            analiz,
            rapor,
            arsiv,
        ]


        if all(
            x == "HAZIR"
            for x in adimlar
        ):

            sonuc = (
                "SAHA_SENARYO_BASARILI"
            )

        else:

            sonuc = (
                "INCELEME_GEREKLI"
            )



        kayit = VBPSahaSenaryoKaydi(

            senaryo_id,

            cihaz,

            veri,

            analiz,

            rapor,

            arsiv,

            sonuc,

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            senaryo_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSahaSenaryoKaydi,
    ):

        veri_seti = {

            "senaryo_id":
                kayit.senaryo_id,

            "cihaz":
                kayit.cihaz,

            "veri":
                kayit.veri,

            "analiz":
                kayit.analiz,

            "rapor":
                kayit.rapor,

            "arsiv":
                kayit.arsiv,

        }


        return (
            self.hash_uret(veri_seti)
            ==
            kayit.sha256
        )

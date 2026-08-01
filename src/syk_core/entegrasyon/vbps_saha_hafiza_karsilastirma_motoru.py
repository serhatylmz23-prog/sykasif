from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSSahaHafizaKaydi:

    kayit_id: str
    eski_veri: str
    yeni_veri: str
    saha_adi: str
    degisim_durumu: str
    analiz_durumu: str
    sha256: str
    zaman: str



class VBPSSahaHafizaKarsilastirmaMotoru:


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



    def karsilastir(
        self,
        kayit_id: str,
        eski_veri: str,
        yeni_veri: str,
        saha_adi: str,
    ):

        veri = {

            "kayit_id":
                kayit_id,

            "eski_veri":
                eski_veri,

            "yeni_veri":
                yeni_veri,

            "saha_adi":
                saha_adi,

        }


        sha256 = self.hash_uret(
            veri
        )


        if eski_veri == yeni_veri:

            degisim_durumu = (
                "DEGISIM_YOK"
            )

        else:

            degisim_durumu = (
                "DEGISIM_VAR"
            )



        kayit = VBPSSahaHafizaKaydi(

            kayit_id,

            eski_veri,

            yeni_veri,

            saha_adi,

            degisim_durumu,

            "KARSILASTIRMA_TAMAM",

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            kayit_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSSahaHafizaKaydi,
    ):

        veri = {

            "kayit_id":
                kayit.kayit_id,

            "eski_veri":
                kayit.eski_veri,

            "yeni_veri":
                kayit.yeni_veri,

            "saha_adi":
                kayit.saha_adi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

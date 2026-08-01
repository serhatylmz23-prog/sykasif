from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSVeriKaydi:

    veri_id: str
    cihaz_id: str
    sensor_tipi: str
    veri_tipi: str
    veri_durumu: str
    analiz_hazirligi: str
    sha256: str
    zaman: str



class VBPSVeriAkisSensorYonetimMotoru:


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



    def veri_kaydet(
        self,
        veri_id: str,
        cihaz_id: str,
        sensor_tipi: str,
        veri_tipi: str,
        veri_durumu: str,
    ):

        veri = {

            "veri_id":
                veri_id,

            "cihaz_id":
                cihaz_id,

            "sensor_tipi":
                sensor_tipi,

            "veri_tipi":
                veri_tipi,

            "veri_durumu":
                veri_durumu,

        }


        sha256 = self.hash_uret(
            veri
        )


        if veri_durumu == "YETERLI":

            analiz_hazirligi = (
                "ANALIZE_HAZIR"
            )

        else:

            analiz_hazirligi = (
                "VERI_EKSIK"
            )



        kayit = VBPSVeriKaydi(

            veri_id,

            cihaz_id,

            sensor_tipi,

            veri_tipi,

            veri_durumu,

            analiz_hazirligi,

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            veri_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSVeriKaydi,
    ):

        veri = {

            "veri_id":
                kayit.veri_id,

            "cihaz_id":
                kayit.cihaz_id,

            "sensor_tipi":
                kayit.sensor_tipi,

            "veri_tipi":
                kayit.veri_tipi,

            "veri_durumu":
                kayit.veri_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSGoruntuSensorKaydi:

    veri_id: str
    cihaz_id: str
    cihaz_tipi: str
    veri_tipi: str
    kaynak_dogrulama: str
    konum_kaydi: str
    analiz_durumu: str
    sha256: str
    zaman: str



class VBPSGoruntuSensorVeriMotoru:


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



    def kaydet(
        self,
        veri_id: str,
        cihaz_id: str,
        cihaz_tipi: str,
        veri_tipi: str,
        kaynak_dogrulama: str,
        konum_kaydi: str,
    ):

        veri = {

            "veri_id":
                veri_id,

            "cihaz_id":
                cihaz_id,

            "cihaz_tipi":
                cihaz_tipi,

            "veri_tipi":
                veri_tipi,

            "kaynak_dogrulama":
                kaynak_dogrulama,

            "konum_kaydi":
                konum_kaydi,

        }


        sha256 = self.hash_uret(
            veri
        )


        if kaynak_dogrulama == "DOGRULANDI":

            analiz_durumu = (
                "ANALIZE_HAZIR"
            )

        else:

            analiz_durumu = (
                "KAYNAK_INCELEME"
            )



        kayit = VBPSGoruntuSensorKaydi(

            veri_id,

            cihaz_id,

            cihaz_tipi,

            veri_tipi,

            kaynak_dogrulama,

            konum_kaydi,

            analiz_durumu,

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
        kayit: VBPSGoruntuSensorKaydi,
    ):

        veri = {

            "veri_id":
                kayit.veri_id,

            "cihaz_id":
                kayit.cihaz_id,

            "cihaz_tipi":
                kayit.cihaz_tipi,

            "veri_tipi":
                kayit.veri_tipi,

            "kaynak_dogrulama":
                kayit.kaynak_dogrulama,

            "konum_kaydi":
                kayit.konum_kaydi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SYKCihazKaydi:

    cihaz_id: str
    cihaz_tipi: str
    baglanti_tipi: str
    model: str
    eslesme_durumu: str
    yetki_durumu: str
    sha256: str
    zaman: str



class SYKCihazEslesmeYetkilendirmeMotoru:


    def __init__(self):

        self.cihazlar = {}



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



    def cihaz_kaydet(
        self,
        cihaz_id: str,
        cihaz_tipi: str,
        baglanti_tipi: str,
        model: str,
    ):

        veri = {

            "cihaz_id":
                cihaz_id,

            "cihaz_tipi":
                cihaz_tipi,

            "baglanti_tipi":
                baglanti_tipi,

            "model":
                model,

        }


        sha256 = self.hash_uret(
            veri
        )


        kayit = SYKCihazKaydi(

            cihaz_id,

            cihaz_tipi,

            baglanti_tipi,

            model,

            "ESLESME_TAMAM",

            "YETKILI",

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.cihazlar[
            cihaz_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: SYKCihazKaydi,
    ):

        veri = {

            "cihaz_id":
                kayit.cihaz_id,

            "cihaz_tipi":
                kayit.cihaz_tipi,

            "baglanti_tipi":
                kayit.baglanti_tipi,

            "model":
                kayit.model,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

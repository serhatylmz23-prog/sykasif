from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SYKEntegrasyonKontrolKaydi:

    kontrol_id: str
    cihaz_durumu: str
    veri_durumu: str
    rapor_durumu: str
    arsiv_durumu: str
    zincir_durumu: str
    sha256: str
    zaman: str



class VBPSYKCekirdekEntegrasyonKontrolMotoru:


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



    def kontrol_et(
        self,
        kontrol_id: str,
        cihaz_durumu: str,
        veri_durumu: str,
        rapor_durumu: str,
        arsiv_durumu: str,
    ):

        veri = {

            "kontrol_id":
                kontrol_id,

            "cihaz_durumu":
                cihaz_durumu,

            "veri_durumu":
                veri_durumu,

            "rapor_durumu":
                rapor_durumu,

            "arsiv_durumu":
                arsiv_durumu,

        }


        sha256 = self.hash_uret(
            veri
        )


        durumlar = [
            cihaz_durumu,
            veri_durumu,
            rapor_durumu,
            arsiv_durumu,
        ]


        if all(
            x == "HAZIR"
            for x in durumlar
        ):

            zincir_durumu = (
                "ENTEGRASYON_TAMAM"
            )

        else:

            zincir_durumu = (
                "INCELEME_GEREKLI"
            )



        kayit = SYKEntegrasyonKontrolKaydi(

            kontrol_id,

            cihaz_durumu,

            veri_durumu,

            rapor_durumu,

            arsiv_durumu,

            zincir_durumu,

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            kontrol_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: SYKEntegrasyonKontrolKaydi,
    ):

        veri = {

            "kontrol_id":
                kayit.kontrol_id,

            "cihaz_durumu":
                kayit.cihaz_durumu,

            "veri_durumu":
                kayit.veri_durumu,

            "rapor_durumu":
                kayit.rapor_durumu,

            "arsiv_durumu":
                kayit.arsiv_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

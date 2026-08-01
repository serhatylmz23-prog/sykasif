from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSKomutKaydi:

    komut_id: str
    cihaz_id: str
    kullanim_modu: str
    komut_tipi: str
    yon: str
    onay_durumu: str
    sonuc: str
    sha256: str
    zaman: str



class VBPSOperasyonKomutaMotoru:


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



    def komut_kaydet(
        self,
        komut_id: str,
        cihaz_id: str,
        kullanim_modu: str,
        komut_tipi: str,
        yon: str,
        onay_durumu: str,
    ):

        veri = {

            "komut_id":
                komut_id,

            "cihaz_id":
                cihaz_id,

            "kullanim_modu":
                kullanim_modu,

            "komut_tipi":
                komut_tipi,

            "yon":
                yon,

            "onay_durumu":
                onay_durumu,

        }


        sha256 = self.hash_uret(
            veri
        )


        if onay_durumu == "ONAYLANDI":

            sonuc = (
                "KOMUT_UYGULAMA_HAZIR"
            )

        else:

            sonuc = (
                "BEKLIYOR"
            )



        kayit = VBPSKomutKaydi(

            komut_id,

            cihaz_id,

            kullanim_modu,

            komut_tipi,

            yon,

            onay_durumu,

            sonuc,

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            komut_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSKomutKaydi,
    ):

        veri = {

            "komut_id":
                kayit.komut_id,

            "cihaz_id":
                kayit.cihaz_id,

            "kullanim_modu":
                kayit.kullanim_modu,

            "komut_tipi":
                kayit.komut_tipi,

            "yon":
                kayit.yon,

            "onay_durumu":
                kayit.onay_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

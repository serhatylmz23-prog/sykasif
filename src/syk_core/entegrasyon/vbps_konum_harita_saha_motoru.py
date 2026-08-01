from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSKonumKaydi:

    kayit_id: str
    cihaz_id: str
    enlem: float
    boylam: float
    saha_adi: str
    veri_baglantisi: str
    tekrar_ziyaret: str
    sha256: str
    zaman: str



class VBPSKonumHaritaSahaMotoru:


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
        kayit_id: str,
        cihaz_id: str,
        enlem: float,
        boylam: float,
        saha_adi: str,
        veri_baglantisi: str,
    ):

        veri = {

            "kayit_id":
                kayit_id,

            "cihaz_id":
                cihaz_id,

            "enlem":
                enlem,

            "boylam":
                boylam,

            "saha_adi":
                saha_adi,

            "veri_baglantisi":
                veri_baglantisi,

        }


        sha256 = self.hash_uret(
            veri
        )


        tekrar_ziyaret = (
            "KAYITLI_SAHA"
        )


        kayit = VBPSKonumKaydi(

            kayit_id,

            cihaz_id,

            enlem,

            boylam,

            saha_adi,

            veri_baglantisi,

            tekrar_ziyaret,

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
        kayit: VBPSKonumKaydi,
    ):

        veri = {

            "kayit_id":
                kayit.kayit_id,

            "cihaz_id":
                kayit.cihaz_id,

            "enlem":
                kayit.enlem,

            "boylam":
                kayit.boylam,

            "saha_adi":
                kayit.saha_adi,

            "veri_baglantisi":
                kayit.veri_baglantisi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

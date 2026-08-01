from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSRaporKaydi:

    rapor_id: str
    cihaz_bilgisi: str
    konum_bilgisi: str
    veri_ozeti: str
    dogrulama_durumu: str
    kanit_sha256: str
    durum: str
    zaman: str



class VBPSRaporKanitPaketiMotoru:


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



    def olustur(
        self,
        rapor_id: str,
        cihaz_bilgisi: str,
        konum_bilgisi: str,
        veri_ozeti: str,
        dogrulama_durumu: str,
    ):

        veri = {

            "rapor_id":
                rapor_id,

            "cihaz_bilgisi":
                cihaz_bilgisi,

            "konum_bilgisi":
                konum_bilgisi,

            "veri_ozeti":
                veri_ozeti,

            "dogrulama_durumu":
                dogrulama_durumu,

        }


        kanit_sha256 = self.hash_uret(
            veri
        )


        if dogrulama_durumu == "DOGRULANDI":

            durum = (
                "KANIT_PAKETI_HAZIR"
            )

        else:

            durum = (
                "INCELEME_GEREKLI"
            )



        kayit = VBPSRaporKaydi(

            rapor_id,

            cihaz_bilgisi,

            konum_bilgisi,

            veri_ozeti,

            dogrulama_durumu,

            kanit_sha256,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            rapor_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSRaporKaydi,
    ):

        veri = {

            "rapor_id":
                kayit.rapor_id,

            "cihaz_bilgisi":
                kayit.cihaz_bilgisi,

            "konum_bilgisi":
                kayit.konum_bilgisi,

            "veri_ozeti":
                kayit.veri_ozeti,

            "dogrulama_durumu":
                kayit.dogrulama_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.kanit_sha256
        )

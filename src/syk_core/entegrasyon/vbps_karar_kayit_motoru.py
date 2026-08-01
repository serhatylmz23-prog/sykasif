from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSKaydi:

    kayit_id: str
    cihaz_tipi: str
    baglanti_tipi: str
    cihaz_dogrulama: str
    kullanim_modu: str
    veri_durumu: str
    ek_cihaz_talebi: str
    onay_durumu: str
    sonuc: str
    sha256: str
    zaman: str



class VBPSKararKayitMotoru:


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
        cihaz_tipi: str,
        baglanti_tipi: str,
        cihaz_dogrulama: str,
        kullanim_modu: str,
        veri_durumu: str,
        ek_cihaz_talebi: str,
        onay_durumu: str,
        sonuc: str,
    ):

        veri = {

            "kayit_id":
                kayit_id,

            "cihaz_tipi":
                cihaz_tipi,

            "baglanti_tipi":
                baglanti_tipi,

            "cihaz_dogrulama":
                cihaz_dogrulama,

            "kullanim_modu":
                kullanim_modu,

            "veri_durumu":
                veri_durumu,

            "ek_cihaz_talebi":
                ek_cihaz_talebi,

            "onay_durumu":
                onay_durumu,

            "sonuc":
                sonuc,

        }


        sha256 = self.hash_uret(
            veri
        )


        kayit = VBPSKaydi(

            kayit_id,

            cihaz_tipi,

            baglanti_tipi,

            cihaz_dogrulama,

            kullanim_modu,

            veri_durumu,

            ek_cihaz_talebi,

            onay_durumu,

            sonuc,

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
        kayit: VBPSKaydi,
    ):

        veri = {

            "kayit_id":
                kayit.kayit_id,

            "cihaz_tipi":
                kayit.cihaz_tipi,

            "baglanti_tipi":
                kayit.baglanti_tipi,

            "cihaz_dogrulama":
                kayit.cihaz_dogrulama,

            "kullanim_modu":
                kayit.kullanim_modu,

            "veri_durumu":
                kayit.veri_durumu,

            "ek_cihaz_talebi":
                kayit.ek_cihaz_talebi,

            "onay_durumu":
                kayit.onay_durumu,

            "sonuc":
                kayit.sonuc,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class VBPSVeriYetersizlikKaydi:

    talep_id: str
    mevcut_veri: str
    eksik_veri: str
    ek_cihaz_talebi: str
    konum_kaydi: str
    onay_durumu: str
    sonuc: str
    sha256: str
    zaman: str



class VBPSVeriYetersizligiTalepMotoru:


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
        talep_id: str,
        mevcut_veri: str,
        eksik_veri: str,
        ek_cihaz_talebi: str,
        konum_kaydi: str,
        onay_durumu: str,
    ):

        veri = {

            "talep_id":
                talep_id,

            "mevcut_veri":
                mevcut_veri,

            "eksik_veri":
                eksik_veri,

            "ek_cihaz_talebi":
                ek_cihaz_talebi,

            "konum_kaydi":
                konum_kaydi,

            "onay_durumu":
                onay_durumu,

        }


        sha256 = self.hash_uret(
            veri
        )


        if mevcut_veri == "YETERSIZ":

            sonuc = (
                "EK_VERI_VEYA_CIHAZ_GEREKLI"
            )

        else:

            sonuc = (
                "ANALIZ_DEVAM"
            )



        kayit = VBPSVeriYetersizlikKaydi(

            talep_id,

            mevcut_veri,

            eksik_veri,

            ek_cihaz_talebi,

            konum_kaydi,

            onay_durumu,

            sonuc,

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            talep_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: VBPSVeriYetersizlikKaydi,
    ):

        veri = {

            "talep_id":
                kayit.talep_id,

            "mevcut_veri":
                kayit.mevcut_veri,

            "eksik_veri":
                kayit.eksik_veri,

            "ek_cihaz_talebi":
                kayit.ek_cihaz_talebi,

            "konum_kaydi":
                kayit.konum_kaydi,

            "onay_durumu":
                kayit.onay_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

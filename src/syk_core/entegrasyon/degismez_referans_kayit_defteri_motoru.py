from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class DegismezReferansKaydi:

    cekirdek_kimligi: str

    referans_adi: str

    onceki_sha256: str

    yeni_sha256: str

    degisim_tipi: str

    surum_bilgisi: str

    durum: str

    kayit_sha256: str

    zaman: str



class DegismezReferansKayitDefteriMotoru:


    def __init__(self):

        self.kayitlar = []



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
        cekirdek_kimligi: str,
        referans_adi: str,
        onceki_sha256: str,
        yeni_sha256: str,
        degisim_tipi: str,
        surum_bilgisi: str,
    ):


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "referans_adi":
                referans_adi,

            "onceki_sha256":
                onceki_sha256,

            "yeni_sha256":
                yeni_sha256,

            "degisim_tipi":
                degisim_tipi,

            "surum_bilgisi":
                surum_bilgisi,

        }


        kayit_sha256 = self.hash_uret(
            veri
        )


        kayit = DegismezReferansKaydi(

            cekirdek_kimligi,

            referans_adi,

            onceki_sha256,

            yeni_sha256,

            degisim_tipi,

            surum_bilgisi,

            "degismez_referans_kaydi_hazir",

            kayit_sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar.append(
            kayit
        )


        return kayit



    def dogrula(
        self,
        kayit: DegismezReferansKaydi,
    ):


        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "referans_adi":
                kayit.referans_adi,

            "onceki_sha256":
                kayit.onceki_sha256,

            "yeni_sha256":
                kayit.yeni_sha256,

            "degisim_tipi":
                kayit.degisim_tipi,

            "surum_bilgisi":
                kayit.surum_bilgisi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.kayit_sha256
        )

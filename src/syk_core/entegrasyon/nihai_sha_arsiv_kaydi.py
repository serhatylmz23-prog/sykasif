from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class ArsivSHAKaydi:

    cekirdek_kimligi: str

    zincir_baslangic: str

    zincir_bitis: str

    toplam_kayit: int

    arsiv_sha256: str

    durum: str

    zaman: str



class NihaiSHAArsivKaydi:


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



    def arsiv_olustur(
        self,
        cekirdek_kimligi: str,
        sprint_listesi: list[str],
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprint_listesi":
                sprint_listesi,

        }


        sha = self.hash_uret(
            veri
        )


        kayit = ArsivSHAKaydi(

            cekirdek_kimligi,

            sprint_listesi[0],

            sprint_listesi[-1],

            len(
                sprint_listesi
            ),

            sha,

            "bagimsiz_sha_arsiv_kaydi",

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            cekirdek_kimligi
        ] = kayit


        return kayit



    def dogrula(
        self,
        cekirdek_kimligi: str,
        sprint_listesi: list[str],
    ):


        kayit = self.kayitlar.get(
            cekirdek_kimligi
        )


        if kayit is None:

            return False



        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprint_listesi":
                sprint_listesi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.arsiv_sha256
        )

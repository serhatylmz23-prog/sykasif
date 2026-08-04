from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class TeslimManifestKaydi:

    cekirdek_kimligi: str

    sprint_sayisi: int

    durum: str

    manifest_hashi: str

    zaman: str



class KaliciTeslimManifesti:


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
        cekirdek_kimligi: str,
        sprint_listesi: list[str],
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprint_listesi":
                sprint_listesi,

        }


        hash_degeri = self.hash_uret(
            veri
        )


        kayit = TeslimManifestKaydi(

            cekirdek_kimligi,

            len(
                sprint_listesi
            ),

            "kalici_teslim_adayi",

            hash_degeri,

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
            kayit.manifest_hashi
        )



    def getir(
        self,
        cekirdek_kimligi: str,
    ):

        return self.kayitlar.get(
            cekirdek_kimligi
        )

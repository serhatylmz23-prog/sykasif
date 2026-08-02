from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class NihaiMuhurAdayi:

    cekirdek_kimligi: str

    sprint_sayisi: int

    modul_sayisi: int

    durum: str

    dogrulama_durumu: str

    sha256: str

    zaman: str



class NihaiMuhurAdayiOzet:


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
        modul_listesi: list[str],
        dogrulama_durumu: str,
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprint_listesi":
                sprint_listesi,

            "modul_listesi":
                modul_listesi,

            "dogrulama_durumu":
                dogrulama_durumu,

        }


        sha = self.hash_uret(
            veri
        )


        kayit = NihaiMuhurAdayi(

            cekirdek_kimligi,

            len(
                sprint_listesi
            ),

            len(
                modul_listesi
            ),

            "nihai_muhur_adayi",

            dogrulama_durumu,

            sha,

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
        modul_listesi: list[str],
        dogrulama_durumu: str,
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

            "modul_listesi":
                modul_listesi,

            "dogrulama_durumu":
                dogrulama_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

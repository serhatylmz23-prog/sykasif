from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class CekirdekMuhurKaydi:

    cekirdek_kimligi: str

    sprint_listesi: list[str]

    durum: str

    sha256: str

    zaman: str



class CekirdekMuhurAdayi:


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


        sha = self.hash_uret(
            veri
        )


        kayit = CekirdekMuhurKaydi(

            cekirdek_kimligi,

            sprint_listesi,

            "muhur_adayi",

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
    ):


        kayit = self.kayitlar.get(
            cekirdek_kimligi
        )


        if kayit is None:

            return False


        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "sprint_listesi":
                kayit.sprint_listesi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )



    def getir(
        self,
        cekirdek_kimligi: str,
    ):

        return self.kayitlar.get(
            cekirdek_kimligi
        )

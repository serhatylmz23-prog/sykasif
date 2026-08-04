from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class DevirNihaiRaporu:

    cekirdek_kimligi: str

    sprint_sayisi: int

    modul_sayisi: int

    durum: str

    rapor_hashi: str

    zaman: str



class DevirNihaiDurumRaporu:


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
    ):


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprint_listesi":
                sprint_listesi,

            "modul_listesi":
                modul_listesi,

        }


        rapor_hashi = self.hash_uret(
            veri
        )


        kayit = DevirNihaiRaporu(

            cekirdek_kimligi,

            len(
                sprint_listesi
            ),

            len(
                modul_listesi
            ),

            "devir_raporu_hazir",

            rapor_hashi,

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

        }


        return (

            self.hash_uret(veri)

            ==

            kayit.rapor_hashi

        )

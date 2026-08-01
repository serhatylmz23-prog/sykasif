from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class CekirdekKanitZinciri:

    cekirdek_kimligi: str

    kanit_hashi: str

    durum_hashi: str

    manifest_hashi: str

    muhur_hashi: str

    toplam_bilesen: int

    zincir_hashi: str

    durum: str

    zaman: str



class CekirdekKanitZinciriBirlestirme:


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



    def birlestir(
        self,
        cekirdek_kimligi: str,
        kanit_hashi: str,
        durum_hashi: str,
        manifest_hashi: str,
        muhur_hashi: str,
    ):


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "kanit_hashi":
                kanit_hashi,

            "durum_hashi":
                durum_hashi,

            "manifest_hashi":
                manifest_hashi,

            "muhur_hashi":
                muhur_hashi,

        }


        zincir_hashi = self.hash_uret(
            veri
        )


        kayit = CekirdekKanitZinciri(

            cekirdek_kimligi,

            kanit_hashi,

            durum_hashi,

            manifest_hashi,

            muhur_hashi,

            4,

            zincir_hashi,

            "birlesik_zincir_hazir",

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

            "kanit_hashi":
                kayit.kanit_hashi,

            "durum_hashi":
                kayit.durum_hashi,

            "manifest_hashi":
                kayit.manifest_hashi,

            "muhur_hashi":
                kayit.muhur_hashi,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.zincir_hashi
        )

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class KapanisPaketi:


    cekirdek_kimligi: str

    toplam_bilesen: int

    sha256_kaydi: str

    manifest_kaydi: str

    rapor_kaydi: str

    kapanis_hash: str

    durum: str

    zaman: str




class SHA256KapanisPaketiUretici:


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
        sha256_kaydi: str,
        manifest_kaydi: str,
        rapor_kaydi: str,
    ):


        veri = {


            "cekirdek_kimligi":
                cekirdek_kimligi,


            "sha256_kaydi":
                sha256_kaydi,


            "manifest_kaydi":
                manifest_kaydi,


            "rapor_kaydi":
                rapor_kaydi,


        }



        kapanis_hash = self.hash_uret(
            veri
        )



        paket = KapanisPaketi(

            cekirdek_kimligi,

            3,

            sha256_kaydi,

            manifest_kaydi,

            rapor_kaydi,

            kapanis_hash,

            "son_arsiv_kapanis_hazir",

            datetime.now(
                timezone.utc
            ).isoformat(),

        )



        self.kayitlar[
            cekirdek_kimligi
        ] = paket



        return paket



    def dogrula(
        self,
        paket: KapanisPaketi,
    ):


        veri = {


            "cekirdek_kimligi":
                paket.cekirdek_kimligi,


            "sha256_kaydi":
                paket.sha256_kaydi,


            "manifest_kaydi":
                paket.manifest_kaydi,


            "rapor_kaydi":
                paket.rapor_kaydi,


        }



        return (
            self.hash_uret(veri)
            ==
            paket.kapanis_hash
        )

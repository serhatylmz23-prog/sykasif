from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class BirlesikTeslimZinciri:

    cekirdek_kimligi: str

    artefakt_sha256: str

    manifest_sha256: str

    muhur_sha256: str

    toplam_bilesen: int

    zincir_sha256: str

    durum: str

    zaman: str



class GercekTeslimZinciriUretici:


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
            temiz.encode(
                "utf-8"
            )
        ).hexdigest()



    def olustur(
        self,
        cekirdek_kimligi: str,
        artefakt_sha256: str,
        manifest_sha256: str,
        muhur_sha256: str,
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "artefakt_sha256":
                artefakt_sha256,

            "manifest_sha256":
                manifest_sha256,

            "muhur_sha256":
                muhur_sha256,

        }


        zincir_sha256 = self.hash_uret(
            veri
        )


        kayit = BirlesikTeslimZinciri(

            cekirdek_kimligi,

            artefakt_sha256,

            manifest_sha256,

            muhur_sha256,

            3,

            zincir_sha256,

            "birlesik_teslim_zinciri_hazir",

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
        kayit: BirlesikTeslimZinciri,
    ):

        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "artefakt_sha256":
                kayit.artefakt_sha256,

            "manifest_sha256":
                kayit.manifest_sha256,

            "muhur_sha256":
                kayit.muhur_sha256,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.zincir_sha256
        )

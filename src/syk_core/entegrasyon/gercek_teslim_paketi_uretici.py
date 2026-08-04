from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class GercekTeslimPaketi:

    cekirdek_kimligi: str

    artefakt_sha256: str

    manifest_sha256: str

    teslim_zinciri_sha256: str

    toplam_bilesen: int

    paket_sha256: str

    durum: str

    zaman: str



class GercekTeslimPaketiUretici:


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
        artefakt_sha256: str,
        manifest_sha256: str,
        teslim_zinciri_sha256: str,
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "artefakt_sha256":
                artefakt_sha256,

            "manifest_sha256":
                manifest_sha256,

            "teslim_zinciri_sha256":
                teslim_zinciri_sha256,

        }


        paket_sha256 = self.hash_uret(
            veri
        )


        kayit = GercekTeslimPaketi(

            cekirdek_kimligi,

            artefakt_sha256,

            manifest_sha256,

            teslim_zinciri_sha256,

            3,

            paket_sha256,

            "gercek_teslim_paketi_hazir",

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
        kayit: GercekTeslimPaketi,
    ):

        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "artefakt_sha256":
                kayit.artefakt_sha256,

            "manifest_sha256":
                kayit.manifest_sha256,

            "teslim_zinciri_sha256":
                kayit.teslim_zinciri_sha256,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.paket_sha256
        )

from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timezone


@dataclass
class ManifestKaydi:

    cekirdek_kimligi: str

    artefakt_sayisi: int

    manifest_sha256: str

    durum: str

    zaman: str



class GercekManifestUretici:


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



    def manifest_uret(
        self,
        cekirdek_kimligi: str,
        artefaktlar: list,
    ):

        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "artefaktlar":
                artefaktlar,

        }


        sha = self.hash_uret(
            veri
        )


        kayit = ManifestKaydi(

            cekirdek_kimligi,

            len(
                artefaktlar
            ),

            sha,

            "gercek_manifest_uretildi",

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
        artefaktlar: list,
    ):

        kayit = self.kayitlar.get(
            cekirdek_kimligi
        )


        if kayit is None:

            return False


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "artefaktlar":
                artefaktlar,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.manifest_sha256
        )

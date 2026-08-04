from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class BirlesikKontrolSonucu:

    cekirdek_kimligi: str

    artefakt_kontrol: bool

    sha_kontrol: bool

    manifest_kontrol: bool

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    sonuc_sha256: str

    durum: str

    zaman: str



class GercekArtefaktManifestSHASonKontrol:


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



    def kontrol_et(
        self,
        cekirdek_kimligi: str,
        artefakt_kontrol: bool,
        sha_kontrol: bool,
        manifest_kontrol: bool,
    ):


        kontroller = {

            "ARTEFAKT":
                artefakt_kontrol,

            "SHA":
                sha_kontrol,

            "MANIFEST":
                manifest_kontrol,

        }


        basarili = 0

        hatali = 0

        riskler = []


        for ad, sonuc in kontroller.items():

            if sonuc:

                basarili += 1

            else:

                hatali += 1

                riskler.append(
                    ad
                )



        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "kontroller":
                kontroller,

        }


        sonuc_sha256 = self.hash_uret(
            veri
        )


        if hatali == 0:

            durum = (
                "birlesik_son_kontrol_tamam"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        kayit = BirlesikKontrolSonucu(

            cekirdek_kimligi,

            artefakt_kontrol,

            sha_kontrol,

            manifest_kontrol,

            3,

            basarili,

            hatali,

            riskler,

            sonuc_sha256,

            durum,

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
        kayit: BirlesikKontrolSonucu,
    ):


        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "kontroller":
            {

                "ARTEFAKT":
                    kayit.artefakt_kontrol,

                "SHA":
                    kayit.sha_kontrol,

                "MANIFEST":
                    kayit.manifest_kontrol,

            },

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sonuc_sha256
        )

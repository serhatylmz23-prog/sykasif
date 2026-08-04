from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class BagimsizDogrulamaSonucu:

    cekirdek_kimligi: str

    artefakt_kontrol: bool

    manifest_kontrol: bool

    teslim_zinciri_kontrol: bool

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    dogrulama_sha256: str

    durum: str

    zaman: str



class TeslimPaketiBagimsizDogrulamaMotoru:


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



    def dogrula(
        self,
        cekirdek_kimligi: str,
        artefakt_sha256: str,
        manifest_sha256: str,
        teslim_zinciri_sha256: str,
    ):


        kontroller = {

            "ARTEFAKT":
                len(artefakt_sha256) == 64,

            "MANIFEST":
                len(manifest_sha256) == 64,

            "TESLIM_ZINCIRI":
                len(teslim_zinciri_sha256) == 64,

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


        dogrulama_sha256 = self.hash_uret(
            veri
        )


        if hatali == 0:

            durum = (
                "bagimsiz_dogrulandi"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        kayit = BagimsizDogrulamaSonucu(

            cekirdek_kimligi,

            kontroller["ARTEFAKT"],

            kontroller["MANIFEST"],

            kontroller["TESLIM_ZINCIRI"],

            3,

            basarili,

            hatali,

            riskler,

            dogrulama_sha256,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            cekirdek_kimligi
        ] = kayit


        return kayit

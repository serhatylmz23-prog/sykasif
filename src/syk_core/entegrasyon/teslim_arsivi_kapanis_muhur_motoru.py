from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class KapanisMuhurSonucu:

    cekirdek_kimligi: str

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    kapanis_muhur_sha256: str

    durum: str

    zaman: str



class TeslimArsiviKapanisMuhurMotoru:


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
        kontroller: dict,
    ):

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


        kapanis_hash = self.hash_uret(
            veri
        )


        if hatali == 0:

            durum = (
                "teslim_arsivi_kapanis_muhur_tamam"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )


        kayit = KapanisMuhurSonucu(

            cekirdek_kimligi,

            len(
                kontroller
            ),

            basarili,

            hatali,

            riskler,

            kapanis_hash,

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
        sonuc: KapanisMuhurSonucu,
        kontroller: dict,
    ):

        veri = {

            "cekirdek_kimligi":
                sonuc.cekirdek_kimligi,

            "kontroller":
                kontroller,

        }


        return (
            self.hash_uret(veri)
            ==
            sonuc.kapanis_muhur_sha256
        )

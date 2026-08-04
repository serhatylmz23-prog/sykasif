from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class KaliciSonMuhurKaydi:

    cekirdek_kimligi: str

    onceki_durum: str

    yeni_durum: str

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    son_muhur_sha256: str

    durum: str

    zaman: str



class KaliciTeslimArsiviSonMuhurlemeMotoru:


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



    def muhurle(
        self,
        cekirdek_kimligi: str,
        onceki_durum: str,
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

            "onceki_durum":
                onceki_durum,

            "kontroller":
                kontroller,

        }


        son_muhur_sha256 = self.hash_uret(
            veri
        )


        if hatali == 0:

            yeni_durum = (
                "kalici_teslim_arsivi_son_muhur_tamam"
            )

        else:

            yeni_durum = (
                "inceleme_gerekli"
            )



        kayit = KaliciSonMuhurKaydi(

            cekirdek_kimligi,

            onceki_durum,

            yeni_durum,

            len(
                kontroller
            ),

            basarili,

            hatali,

            riskler,

            son_muhur_sha256,

            yeni_durum,

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
        kayit: KaliciSonMuhurKaydi,
        kontroller: dict,
    ):

        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "onceki_durum":
                kayit.onceki_durum,

            "kontroller":
                kontroller,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.son_muhur_sha256
        )

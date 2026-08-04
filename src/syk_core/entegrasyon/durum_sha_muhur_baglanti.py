from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class DurumSHAKaydi:

    eski_durum: str

    yeni_durum: str

    aciklama: str

    sha256: str

    durum: str

    zaman: str



class DurumSHAMuhurBaglanti:



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
        eski_durum: str,
        yeni_durum: str,
        aciklama: str,
    ):

        veri = {

            "eski_durum":
                eski_durum,

            "yeni_durum":
                yeni_durum,

            "aciklama":
                aciklama,

        }


        sha = self.hash_uret(
            veri
        )


        kayit = DurumSHAKaydi(

            eski_durum,

            yeni_durum,

            aciklama,

            sha,

            "muhurlendi",

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        anahtar = sha


        self.kayitlar[
            anahtar
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: DurumSHAKaydi,
    ):


        veri = {

            "eski_durum":
                kayit.eski_durum,

            "yeni_durum":
                kayit.yeni_durum,

            "aciklama":
                kayit.aciklama,

        }


        yeni_sha = self.hash_uret(
            veri
        )


        return (
            yeni_sha
            ==
            kayit.sha256
        )



    def getir(
        self,
        sha256: str,
    ):

        return self.kayitlar.get(
            sha256
        )

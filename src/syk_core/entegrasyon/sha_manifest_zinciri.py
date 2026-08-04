from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class ManifestVersiyonKaydi:

    kanit_kimligi: str

    versiyon: int

    onceki_hash: str

    yeni_hash: str

    zaman: str

    durum: str = "kayitli"



class SHAManifestZinciri:


    def __init__(self):

        self.kayitlar = {}



    def hash_uret(
        self,
        veri,
    ):

        temiz = json.dumps(
            veri,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            temiz.encode("utf-8")
        ).hexdigest()



    def yeni_versiyon_olustur(
        self,
        kanit_kimligi: str,
        veri: dict,
    ):

        onceki = self.kayitlar.get(
            kanit_kimligi
        )


        if onceki is None:

            onceki_hash = ""

            versiyon = 1

        else:

            onceki_hash = (
                onceki.yeni_hash
            )

            versiyon = (
                onceki.versiyon + 1
            )


        yeni_hash = self.hash_uret(
            veri
        )


        kayit = ManifestVersiyonKaydi(
            kanit_kimligi,
            versiyon,
            onceki_hash,
            yeni_hash,
            datetime.now(
                timezone.utc
            ).isoformat(),
        )


        self.kayitlar[
            kanit_kimligi
        ] = kayit


        return kayit



    def zincir_dogrula(
        self,
        kanit_kimligi: str,
    ):

        kayit = self.kayitlar.get(
            kanit_kimligi
        )


        if kayit is None:

            return False


        if kayit.versiyon == 1:

            return (
                kayit.onceki_hash
                ==
                ""
            )


        return (
            kayit.onceki_hash
            !=
            ""
        )



    def getir(
        self,
        kanit_kimligi: str,
    ):

        return self.kayitlar.get(
            kanit_kimligi
        )

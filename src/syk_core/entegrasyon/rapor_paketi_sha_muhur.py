from dataclasses import dataclass
import hashlib
import json
from datetime import datetime, timezone


@dataclass
class RaporMuhurKaydi:

    rapor_kimligi: str

    paket_hashi: str

    zaman: str

    durum: str = "muhurlendi"



class RaporPaketiSHAMuhur:


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
        rapor_kimligi: str,
        paket: dict,
    ):

        hash_degeri = self.hash_uret(
            paket
        )


        kayit = RaporMuhurKaydi(
            rapor_kimligi,
            hash_degeri,
            datetime.now(
                timezone.utc
            ).isoformat(),
        )


        self.kayitlar[
            rapor_kimligi
        ] = kayit


        return kayit



    def dogrula(
        self,
        rapor_kimligi: str,
        paket: dict,
    ):

        kayit = self.kayitlar.get(
            rapor_kimligi
        )


        if kayit is None:

            return False


        yeni_hash = self.hash_uret(
            paket
        )


        return (
            yeni_hash
            ==
            kayit.paket_hashi
        )



    def getir(
        self,
        rapor_kimligi: str,
    ):

        return self.kayitlar.get(
            rapor_kimligi
        )

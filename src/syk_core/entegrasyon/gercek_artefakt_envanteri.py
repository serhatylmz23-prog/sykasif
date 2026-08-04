from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class ArtefaktKaydi:

    dosya_adi: str

    dosya_turu: str

    sprint: str

    sha256: str

    durum: str

    zaman: str



class GercekArtefaktEnvanteri:


    def __init__(self):

        self.kayitlar = []



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



    def kaydet(
        self,
        dosya_adi: str,
        dosya_turu: str,
        sprint: str,
    ):

        veri = {

            "dosya_adi":
                dosya_adi,

            "dosya_turu":
                dosya_turu,

            "sprint":
                sprint,

        }


        sha = self.hash_uret(
            veri
        )


        kayit = ArtefaktKaydi(

            dosya_adi,

            dosya_turu,

            sprint,

            sha,

            "envantere_alindi",

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar.append(
            kayit
        )


        return kayit



    def kontrol_et(
        self,
        dosya_adi: str,
    ):

        for kayit in self.kayitlar:

            if kayit.dosya_adi == dosya_adi:

                return True


        return False



    def toplam_getir(
        self,
    ):

        return len(
            self.kayitlar
        )

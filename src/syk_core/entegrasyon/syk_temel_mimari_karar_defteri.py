from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SYKTemelMimariKarari:

    karar_id: str
    baslik: str
    kategori: str
    aciklama: str
    karar_sahibi: str
    hazirlayan: str
    durum: str
    sha256: str
    zaman: str



class SYKTemelMimariKararDefteri:


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



    def karar_ekle(
        self,
        karar_id: str,
        baslik: str,
        kategori: str,
        aciklama: str,
    ):

        veri = {

            "karar_id":
                karar_id,

            "baslik":
                baslik,

            "kategori":
                kategori,

            "aciklama":
                aciklama,

            "karar_sahibi":
                "KASIF_KURUCU",

            "hazirlayan":
                "BILGE_KAAN",

        }


        sha256 = self.hash_uret(
            veri
        )


        kayit = SYKTemelMimariKarari(

            karar_id,

            baslik,

            kategori,

            aciklama,

            "KASIF_KURUCU",

            "BILGE_KAAN",

            "MUHURLENDI",

            sha256,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            karar_id
        ] = kayit


        return kayit



    def dogrula(
        self,
        kayit: SYKTemelMimariKarari,
    ):

        veri = {

            "karar_id":
                kayit.karar_id,

            "baslik":
                kayit.baslik,

            "kategori":
                kayit.kategori,

            "aciklama":
                kayit.aciklama,

            "karar_sahibi":
                kayit.karar_sahibi,

            "hazirlayan":
                kayit.hazirlayan,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.sha256
        )

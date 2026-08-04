from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SYKKararKaydi:

    karar_id: str

    baslik: str

    kategori: str

    aciklama: str

    durum: str

    versiyon: str

    karar_sahibi: str

    hazirlayan: str

    onay_durumu: str

    sha256: str

    zaman: str



class SYKKararKayitAltyapiMotoru:


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



    def karar_kaydet(
        self,
        karar_id: str,
        baslik: str,
        kategori: str,
        aciklama: str,
        versiyon: str,
        karar_sahibi: str,
        hazirlayan: str,
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

            "versiyon":
                versiyon,

            "karar_sahibi":
                karar_sahibi,

            "hazirlayan":
                hazirlayan,

        }


        sha256 = self.hash_uret(
            veri
        )


        kayit = SYKKararKaydi(

            karar_id,

            baslik,

            kategori,

            aciklama,

            "MUHURLENDI",

            versiyon,

            karar_sahibi,

            hazirlayan,

            "ONAYLANDI",

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
        kayit: SYKKararKaydi,
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

            "versiyon":
                kayit.versiyon,

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

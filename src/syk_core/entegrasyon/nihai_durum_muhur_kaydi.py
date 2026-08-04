from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class NihaiDurumMuhurKaydi:

    cekirdek_kimligi: str

    onceki_durum: str

    yeni_durum: str

    toplam_sprint: int

    toplam_katman: int

    karar_durumu: str

    muhur_sha256: str

    durum: str

    zaman: str



class NihaiDurumMuhurKayitMotoru:


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



    def muhur_olustur(
        self,
        cekirdek_kimligi: str,
        onceki_durum: str,
        yeni_durum: str,
        sprintler: list[str],
        katmanlar: list[str],
        karar_durumu: str,
    ):


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "onceki_durum":
                onceki_durum,

            "yeni_durum":
                yeni_durum,

            "sprintler":
                sprintler,

            "katmanlar":
                katmanlar,

            "karar_durumu":
                karar_durumu,

        }


        muhur_sha256 = self.hash_uret(
            veri
        )


        kayit = NihaiDurumMuhurKaydi(

            cekirdek_kimligi,

            onceki_durum,

            yeni_durum,

            len(
                sprintler
            ),

            len(
                katmanlar
            ),

            karar_durumu,

            muhur_sha256,

            "nihai_muhur_kaydi",

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
        kayit: NihaiDurumMuhurKaydi,
        sprintler: list[str],
        katmanlar: list[str],
        karar_durumu: str,
    ):


        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "onceki_durum":
                kayit.onceki_durum,

            "yeni_durum":
                kayit.yeni_durum,

            "sprintler":
                sprintler,

            "katmanlar":
                katmanlar,

            "karar_durumu":
                karar_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.muhur_sha256
        )

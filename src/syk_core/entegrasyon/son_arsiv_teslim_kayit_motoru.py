from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SonArsivTeslimKaydi:

    cekirdek_kimligi: str

    baslangic_sprint: str

    bitis_sprint: str

    toplam_sprint: int

    toplam_katman: int

    kontrol_durumu: str

    teslim_sha256: str

    durum: str

    zaman: str



class SonArsivTeslimKayitMotoru:


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



    def olustur(
        self,
        cekirdek_kimligi: str,
        sprintler: list[str],
        katmanlar: list[str],
        kontrol_durumu: str,
    ):


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprintler":
                sprintler,

            "katmanlar":
                katmanlar,

            "kontrol_durumu":
                kontrol_durumu,

        }


        teslim_sha256 = self.hash_uret(
            veri
        )


        kayit = SonArsivTeslimKaydi(

            cekirdek_kimligi,

            sprintler[0],

            sprintler[-1],

            len(
                sprintler
            ),

            len(
                katmanlar
            ),

            kontrol_durumu,

            teslim_sha256,

            "son_arsiv_teslim_adayi",

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
        kayit: SonArsivTeslimKaydi,
        sprintler: list[str],
        katmanlar: list[str],
        kontrol_durumu: str,
    ):


        veri = {

            "cekirdek_kimligi":
                kayit.cekirdek_kimligi,

            "sprintler":
                sprintler,

            "katmanlar":
                katmanlar,

            "kontrol_durumu":
                kontrol_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            kayit.teslim_sha256
        )

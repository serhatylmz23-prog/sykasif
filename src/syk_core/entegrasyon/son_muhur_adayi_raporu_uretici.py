from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class SonMuhurAdayiRaporu:

    cekirdek_kimligi: str

    baslangic_sprint: str

    bitis_sprint: str

    toplam_sprint: int

    toplam_katman: int

    kontrol_durumu: str

    teslim_durumu: str

    rapor_sha256: str

    durum: str

    zaman: str



class SonMuhurAdayiRaporUretici:


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
        teslim_durumu: str,
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

            "teslim_durumu":
                teslim_durumu,

        }


        rapor_sha256 = self.hash_uret(
            veri
        )


        kayit = SonMuhurAdayiRaporu(

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

            teslim_durumu,

            rapor_sha256,

            "son_muhur_adayi",

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
        rapor: SonMuhurAdayiRaporu,
        sprintler: list[str],
        katmanlar: list[str],
        kontrol_durumu: str,
        teslim_durumu: str,
    ):


        veri = {

            "cekirdek_kimligi":
                rapor.cekirdek_kimligi,

            "sprintler":
                sprintler,

            "katmanlar":
                katmanlar,

            "kontrol_durumu":
                kontrol_durumu,

            "teslim_durumu":
                teslim_durumu,

        }


        return (
            self.hash_uret(veri)
            ==
            rapor.rapor_sha256
        )

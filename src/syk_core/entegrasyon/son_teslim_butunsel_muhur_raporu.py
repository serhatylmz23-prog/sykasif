from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class SonTeslimButunselRapor:

    cekirdek_kimligi: str

    baslangic_sprint: str

    bitis_sprint: str

    toplam_sprint: int

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    zincir_durumu: str

    rapor_sha256: str

    durum: str

    zaman: str



class SonTeslimButunselMuhurRaporUretici:


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
        kontroller: dict,
        zincir_durumu: str,
    ):

        basarili = 0

        hatali = 0


        for sonuc in kontroller.values():

            if sonuc:

                basarili += 1

            else:

                hatali += 1



        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprintler":
                sprintler,

            "kontroller":
                kontroller,

            "zincir_durumu":
                zincir_durumu,

        }



        rapor_sha256 = self.hash_uret(
            veri
        )



        if hatali == 0:

            durum = (
                "son_teslim_butunsel_dogrulandi"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        rapor = SonTeslimButunselRapor(

            cekirdek_kimligi,

            sprintler[0],

            sprintler[-1],

            len(
                sprintler
            ),

            len(
                kontroller
            ),

            basarili,

            hatali,

            zincir_durumu,

            rapor_sha256,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )



        self.kayitlar[
            cekirdek_kimligi
        ] = rapor



        return rapor



    def dogrula(
        self,
        rapor: SonTeslimButunselRapor,
        sprintler: list[str],
        kontroller: dict,
        zincir_durumu: str,
    ):

        veri = {

            "cekirdek_kimligi":
                rapor.cekirdek_kimligi,

            "sprintler":
                sprintler,

            "kontroller":
                kontroller,

            "zincir_durumu":
                zincir_durumu,

        }



        return (
            self.hash_uret(veri)
            ==
            rapor.rapor_sha256
        )

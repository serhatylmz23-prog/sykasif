from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class NihaiTeslimRaporu:

    cekirdek_kimligi: str

    baslangic_sprint: str

    bitis_sprint: str

    toplam_sprint: int

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    durum: str

    rapor_sha256: str

    zaman: str



class NihaiTeslimRaporUretici:


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

        }



        rapor_sha256 = self.hash_uret(
            veri
        )



        if hatali == 0:

            durum = (
                "nihai_teslim_raporu_hazir"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        rapor = NihaiTeslimRaporu(

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

            durum,

            rapor_sha256,

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
        rapor: NihaiTeslimRaporu,
        sprintler: list[str],
        kontroller: dict,
    ):


        veri = {

            "cekirdek_kimligi":
                rapor.cekirdek_kimligi,

            "sprintler":
                sprintler,

            "kontroller":
                kontroller,

        }


        return (
            self.hash_uret(veri)
            ==
            rapor.rapor_sha256
        )

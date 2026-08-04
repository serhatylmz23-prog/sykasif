from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class KaliciTeslimArsivi:

    cekirdek_kimligi: str

    baslangic_sprint: str

    bitis_sprint: str

    toplam_kayit: int

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    arsiv_sha256: str

    durum: str

    zaman: str



class KaliciTeslimArsiviOlusturmaMotoru:


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
        kayitlar: list[str],
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

            "kayitlar":
                kayitlar,

            "kontroller":
                kontroller,

        }



        arsiv_sha256 = self.hash_uret(
            veri
        )



        if hatali == 0:

            durum = (
                "kalici_teslim_arsivi_hazir"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        arsiv = KaliciTeslimArsivi(

            cekirdek_kimligi,

            kayitlar[0],

            kayitlar[-1],

            len(
                kayitlar
            ),

            len(
                kontroller
            ),

            basarili,

            hatali,

            arsiv_sha256,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )



        self.kayitlar[
            cekirdek_kimligi
        ] = arsiv



        return arsiv



    def dogrula(
        self,
        arsiv: KaliciTeslimArsivi,
        kayitlar: list[str],
        kontroller: dict,
    ):

        veri = {

            "cekirdek_kimligi":
                arsiv.cekirdek_kimligi,

            "kayitlar":
                kayitlar,

            "kontroller":
                kontroller,

        }



        return (
            self.hash_uret(veri)
            ==
            arsiv.arsiv_sha256
        )

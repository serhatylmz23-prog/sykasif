from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json



@dataclass
class YenidenDogrulamaSonucu:

    cekirdek_kimligi: str

    toplam_katman: int

    basarili_katman: int

    hatali_katman: int

    eksikler: list[str]

    zincir_hashi: str

    durum: str

    zaman: str



class TamBagimsizYenidenDogrulamaMotoru:


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



    def calistir(
        self,
        cekirdek_kimligi: str,
        katmanlar: dict,
    ):


        basarili = 0

        hatali = 0

        eksikler = []


        for ad, sonuc in katmanlar.items():

            if sonuc:

                basarili += 1

            else:

                hatali += 1

                eksikler.append(
                    ad
                )



        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "katmanlar":
                katmanlar,

        }


        zincir_hashi = self.hash_uret(
            veri
        )


        if hatali == 0:

            durum = (
                "yeniden_dogrulandi"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        sonuc = YenidenDogrulamaSonucu(

            cekirdek_kimligi,

            len(
                katmanlar
            ),

            basarili,

            hatali,

            eksikler,

            zincir_hashi,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            cekirdek_kimligi
        ] = sonuc


        return sonuc



    def dogrula(
        self,
        sonuc: YenidenDogrulamaSonucu,
        katmanlar: dict,
    ):


        veri = {

            "cekirdek_kimligi":
                sonuc.cekirdek_kimligi,

            "katmanlar":
                katmanlar,

        }


        return (
            self.hash_uret(veri)
            ==
            sonuc.zincir_hashi
        )

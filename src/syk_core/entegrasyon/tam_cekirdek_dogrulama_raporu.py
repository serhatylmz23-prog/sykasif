from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class TamCekirdekDogrulamaRaporu:

    cekirdek_kimligi: str

    sprint_sayisi: int

    modul_sayisi: int

    artefakt_sayisi: int

    kontrol_sayisi: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    rapor_sha256: str

    durum: str

    zaman: str



class TamCekirdekDogrulamaRaporuUretici:


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
        moduller: list[str],
        artefaktlar: list[str],
        kontroller: dict,
    ):


        basarili = 0

        hatali = 0

        riskler = []


        for ad, sonuc in kontroller.items():

            if sonuc:

                basarili += 1

            else:

                hatali += 1

                riskler.append(
                    ad
                )


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "sprintler":
                sprintler,

            "moduller":
                moduller,

            "artefaktlar":
                artefaktlar,

            "kontroller":
                kontroller,

        }


        rapor_sha256 = self.hash_uret(
            veri
        )


        if hatali == 0:

            durum = (
                "tam_dogrulandi"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )


        rapor = TamCekirdekDogrulamaRaporu(

            cekirdek_kimligi,

            len(
                sprintler
            ),

            len(
                moduller
            ),

            len(
                artefaktlar
            ),

            len(
                kontroller
            ),

            basarili,

            hatali,

            riskler,

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
        rapor: TamCekirdekDogrulamaRaporu,
        sprintler: list[str],
        moduller: list[str],
        artefaktlar: list[str],
        kontroller: dict,
    ):


        veri = {

            "cekirdek_kimligi":
                rapor.cekirdek_kimligi,

            "sprintler":
                sprintler,

            "moduller":
                moduller,

            "artefaktlar":
                artefaktlar,

            "kontroller":
                kontroller,

        }


        return (
            self.hash_uret(veri)
            ==
            rapor.rapor_sha256
        )

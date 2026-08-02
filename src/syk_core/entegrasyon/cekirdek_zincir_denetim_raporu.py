from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ZincirDenetimRaporu:

    cekirdek_kimligi: str

    toplam_bilesen: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    durum: str

    zaman: str



class CekirdekZincirDenetimRaporuUretici:


    def __init__(self):

        self.raporlar = {}



    def denetle(
        self,
        cekirdek_kimligi: str,
        bilesenler: list,
        kontrol_fonksiyonu,
    ):


        toplam = len(
            bilesenler
        )

        basarili = 0

        hatali = 0

        riskler = []


        for bilesen in bilesenler:


            sonuc = kontrol_fonksiyonu(
                bilesen
            )


            if sonuc:

                basarili += 1


            else:

                hatali += 1

                riskler.append(
                    bilesen
                )



        if hatali == 0:

            durum = (
                "zincir_saglikli"
            )

        else:

            durum = (
                "zincir_riskli"
            )



        rapor = ZincirDenetimRaporu(

            cekirdek_kimligi,

            toplam,

            basarili,

            hatali,

            riskler,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.raporlar[
            cekirdek_kimligi
        ] = rapor


        return rapor



    def getir(
        self,
        cekirdek_kimligi: str,
    ):

        return self.raporlar.get(
            cekirdek_kimligi
        )

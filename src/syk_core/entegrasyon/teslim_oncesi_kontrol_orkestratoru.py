from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class KontrolOrkestrasyonSonucu:

    cekirdek_kimligi: str

    toplam_kontrol: int

    basarili_kontrol: int

    basarisiz_kontrol: int

    eksikler: list[str]

    durum: str

    zaman: str



class TeslimOncesiKontrolOrkestratoru:


    def __init__(self):

        self.kayitlar = {}



    def calistir(
        self,
        cekirdek_kimligi: str,
        kontroller: dict,
    ):


        toplam = len(
            kontroller
        )

        basarili = 0

        basarisiz = 0

        eksikler = []



        for ad, sonuc in kontroller.items():


            if sonuc:

                basarili += 1


            else:

                basarisiz += 1

                eksikler.append(
                    ad
                )



        if basarisiz == 0:

            durum = (
                "teslime_hazir"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )



        kayit = KontrolOrkestrasyonSonucu(

            cekirdek_kimligi,

            toplam,

            basarili,

            basarisiz,

            eksikler,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            cekirdek_kimligi
        ] = kayit


        return kayit



    def getir(
        self,
        cekirdek_kimligi: str,
    ):

        return self.kayitlar.get(
            cekirdek_kimligi
        )

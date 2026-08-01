from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class ZincirSonucRaporu:

    cekirdek_kimligi: str

    zincir_durumu: str

    toplam_bilesen: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    sonuc_hashi: str

    durum: str

    zaman: str



class CekirdekKanitZinciriSonucRaporuUretici:


    def __init__(self):

        self.raporlar = {}



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
        zincir_durumu: str,
        toplam_bilesen: int,
        basarili_kontrol: int,
        hatali_kontrol: int,
        riskler: list[str],
    ):


        veri = {

            "cekirdek_kimligi":
                cekirdek_kimligi,

            "zincir_durumu":
                zincir_durumu,

            "toplam_bilesen":
                toplam_bilesen,

            "basarili_kontrol":
                basarili_kontrol,

            "hatali_kontrol":
                hatali_kontrol,

            "riskler":
                riskler,

        }


        sonuc_hashi = self.hash_uret(
            veri
        )


        if hatali_kontrol == 0:

            durum = (
                "sonuc_onayli"
            )

        else:

            durum = (
                "sonuc_inceleme_gerekli"
            )


        rapor = ZincirSonucRaporu(

            cekirdek_kimligi,

            zincir_durumu,

            toplam_bilesen,

            basarili_kontrol,

            hatali_kontrol,

            riskler,

            sonuc_hashi,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.raporlar[
            cekirdek_kimligi
        ] = rapor


        return rapor



    def dogrula(
        self,
        rapor: ZincirSonucRaporu,
    ):


        veri = {

            "cekirdek_kimligi":
                rapor.cekirdek_kimligi,

            "zincir_durumu":
                rapor.zincir_durumu,

            "toplam_bilesen":
                rapor.toplam_bilesen,

            "basarili_kontrol":
                rapor.basarili_kontrol,

            "hatali_kontrol":
                rapor.hatali_kontrol,

            "riskler":
                rapor.riskler,

        }


        return (
            self.hash_uret(veri)
            ==
            rapor.sonuc_hashi
        )

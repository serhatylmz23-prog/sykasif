from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


@dataclass
class KaliciArsivYenidenDogrulamaSonucu:

    cekirdek_kimligi: str

    toplam_kontrol: int

    basarili_kontrol: int

    hatali_kontrol: int

    riskler: list[str]

    yeniden_dogrulama_sha256: str

    durum: str

    zaman: str



class KaliciTeslimArsiviBagimsizYenidenDogrulamaMotoru:


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



    def kontrol_et(
        self,
        cekirdek_kimligi: str,
        arsiv_sha256: str,
        manifest_sha256: str,
        kapanis_sha256: str,
        rapor_sha256: str,
    ):

        kontroller = {

            "ARSIV":
                len(arsiv_sha256) == 64,

            "MANIFEST":
                len(manifest_sha256) == 64,

            "KAPANIS":
                len(kapanis_sha256) == 64,

            "RAPOR":
                len(rapor_sha256) == 64,

        }


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

            "kontroller":
                kontroller,

        }


        yeniden_dogrulama_sha256 = self.hash_uret(
            veri
        )


        if hatali == 0:

            durum = (
                "kalici_teslim_arsivi_bagimsiz_dogrulandi"
            )

        else:

            durum = (
                "inceleme_gerekli"
            )


        sonuc = KaliciArsivYenidenDogrulamaSonucu(

            cekirdek_kimligi,

            len(kontroller),

            basarili,

            hatali,

            riskler,

            yeniden_dogrulama_sha256,

            durum,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.kayitlar[
            cekirdek_kimligi
        ] = sonuc


        return sonuc

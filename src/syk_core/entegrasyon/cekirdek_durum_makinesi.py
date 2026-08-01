from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DurumGecisKaydi:

    eski_durum: str

    yeni_durum: str

    aciklama: str

    zaman: str



class CekirdekDurumMakinesi:


    GECERLI_DURUMLAR = [

        "taslak",

        "test_ediliyor",

        "dogrulandi",

        "muhur_adayi",

        "bagimsiz_kontrol",

        "teslim_adayi",

        "arsivlendi",

    ]


    GECISLER = {

        "taslak":
            [
                "test_ediliyor"
            ],

        "test_ediliyor":
            [
                "dogrulandi"
            ],

        "dogrulandi":
            [
                "muhur_adayi"
            ],

        "muhur_adayi":
            [
                "bagimsiz_kontrol"
            ],

        "bagimsiz_kontrol":
            [
                "teslim_adayi"
            ],

        "teslim_adayi":
            [
                "arsivlendi"
            ],

        "arsivlendi":
            [],

    }



    def __init__(self):

        self.durum = "taslak"

        self.gecmis = []



    def gecis_yap(
        self,
        yeni_durum: str,
        aciklama: str,
    ):


        if yeni_durum not in self.GECERLI_DURUMLAR:

            return False



        izinli = self.GECISLER.get(
            self.durum,
            []
        )


        if yeni_durum not in izinli:

            return False



        kayit = DurumGecisKaydi(

            self.durum,

            yeni_durum,

            aciklama,

            datetime.now(
                timezone.utc
            ).isoformat(),

        )


        self.gecmis.append(
            kayit
        )


        self.durum = yeni_durum


        return True



    def mevcut_durum(
        self,
    ):

        return self.durum



    def gecmis_getir(
        self,
    ):

        return self.gecmis

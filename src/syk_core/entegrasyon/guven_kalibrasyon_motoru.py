from dataclasses import dataclass


@dataclass
class GuvenDegerlendirme:

    temel_puan: float

    kanit_etkisi: float

    uzman_uyumu: float

    toplam_guven: float

    karar: str



class GuvenKalibrasyonMotoru:


    def hesapla(
        self,
        temel_puan: float,
        kanit_sayisi: int,
        uzman_sayisi: int,
        uzman_uyumu: float,
    ):

        kanit_etkisi = min(
            kanit_sayisi * 2,
            10
        )


        uzman_etkisi = min(
            uzman_sayisi * 2,
            10
        )


        uyum_bonus = (
            uzman_uyumu / 18
        )


        toplam = (
            temel_puan
            +
            kanit_etkisi
            +
            uzman_etkisi
            +
            uyum_bonus
        )


        toplam = min(
            round(toplam),
            100
        )


        if toplam >= 95:

            karar = (
                "yuksek_dogrulama"
            )

        elif toplam >= 80:

            karar = (
                "guclu_destek"
            )

        elif toplam >= 60:

            karar = (
                "orta_destek"
            )

        elif toplam >= 30:

            karar = (
                "inceleme_gerekli"
            )

        else:

            karar = (
                "dusuk_destek"
            )


        return GuvenDegerlendirme(
            temel_puan,
            kanit_etkisi,
            uzman_uyumu,
            toplam,
            karar,
        )

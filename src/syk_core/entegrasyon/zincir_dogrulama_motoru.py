from dataclasses import dataclass



@dataclass
class ZincirDogrulamaSonucu:

    toplam_kayit: int

    dogrulanan_kayit: int

    hatali_kayit: int

    ilk_hata: str | None

    durum: str



class ZincirDogrulamaMotoru:



    def kontrol_et(
        self,
        kayitlar: list,
        dogrulama_fonksiyonu,
    ):


        toplam = len(
            kayitlar
        )


        dogrulanan = 0

        hatali = 0

        ilk_hata = None



        for index, kayit in enumerate(
            kayitlar
        ):


            sonuc = dogrulama_fonksiyonu(
                kayit
            )


            if sonuc:

                dogrulanan += 1


            else:

                hatali += 1


                if ilk_hata is None:

                    ilk_hata = (
                        f"KAYIT-{index + 1}"
                    )



        if hatali == 0:

            durum = (
                "zincir_dogrulandi"
            )

        else:

            durum = (
                "zincir_hatasi_var"
            )



        return ZincirDogrulamaSonucu(

            toplam,

            dogrulanan,

            hatali,

            ilk_hata,

            durum,

        )

class UcUcaCoreDogrulama:


    def __init__(
        self,
        olay_zinciri,
        core_motoru,
        hash_paketi,
    ):

        self.olay_zinciri = olay_zinciri
        self.core_motoru = core_motoru
        self.hash_paketi = hash_paketi



    def calistir(
        self,
        olay_kimligi: str,
        veri,
    ):

        sonuc = self.core_motoru.degerlendir(
            olay_kimligi,
            veri,
        )


        self.olay_zinciri.kaydet(
            olay_kimligi
        )


        self.olay_zinciri.kanit_ekle(
            olay_kimligi,
            str(sonuc.kanitlar[0]),
        )


        self.olay_zinciri.uzman_sonucu_ekle(
            olay_kimligi,
            "CORE-DEGERLENDIRME",
        )


        paket = self.hash_paketi.paket_olustur(
            olay_kimligi,
            sonuc.kanitlar,
            sonuc.goruntu_sonuclari,
            sonuc.guven_puani,
            sonuc.konsensus_puani,
        )


        return paket

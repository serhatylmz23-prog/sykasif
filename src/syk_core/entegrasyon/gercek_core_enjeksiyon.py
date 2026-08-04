class GercekCoreEnjeksiyon:


    def __init__(
        self,
        cekirdek,
        kanit_modulu,
        goruntu_modulu,
        materyal_modulu,
        konsensus_modulu,
    ):

        self.cekirdek = cekirdek
        self.kanit_modulu = kanit_modulu
        self.goruntu_modulu = goruntu_modulu
        self.materyal_modulu = materyal_modulu
        self.konsensus_modulu = konsensus_modulu



    def degerlendir(
        self,
        olay_kimligi: str,
        veri,
    ):

        self.cekirdek.kanit_aktar(
            olay_kimligi,
            self.kanit_modulu(veri),
        )


        self.cekirdek.goruntu_aktar(
            olay_kimligi,
            self.goruntu_modulu(veri),
        )


        self.cekirdek.materyal_aktar(
            olay_kimligi,
            self.materyal_modulu(veri),
        )


        sonuc = self.konsensus_modulu(
            veri
        )


        self.cekirdek.puanlari_aktar(
            olay_kimligi,
            sonuc["guven"],
            sonuc["konsensus"],
        )


        return self.cekirdek.tamamla(
            olay_kimligi
        )

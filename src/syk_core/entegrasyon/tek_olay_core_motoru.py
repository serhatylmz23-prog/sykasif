class TekOlayCoreMotoru:


    def __init__(
        self,
        cekirdek,
        adaptor,
    ):

        self.cekirdek = cekirdek
        self.adaptor = adaptor



    def degerlendir(
        self,
        olay_kimligi: str,
        veri,
    ):

        self.cekirdek.olay_baslat(
            olay_kimligi
        )


        kanit = (
            self.adaptor.kanit_incele(
                veri
            )
        )


        goruntu = (
            self.adaptor.goruntu_incele(
                veri
            )
        )


        materyal = (
            self.adaptor.materyal_incele(
                veri
            )
        )


        konsensus = (
            self.adaptor.konsensus_hesapla(
                veri
            )
        )


        self.cekirdek.kanit_aktar(
            olay_kimligi,
            kanit,
        )


        self.cekirdek.goruntu_aktar(
            olay_kimligi,
            goruntu,
        )


        self.cekirdek.materyal_aktar(
            olay_kimligi,
            materyal,
        )


        self.cekirdek.puanlari_aktar(
            olay_kimligi,
            konsensus["guven"],
            konsensus["konsensus"],
        )


        return self.cekirdek.tamamla(
            olay_kimligi
        )

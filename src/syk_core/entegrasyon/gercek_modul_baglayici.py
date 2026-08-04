class GercekModulBaglayici:


    def __init__(
        self,
        cekirdek,
    ):
        self.cekirdek = cekirdek


    def kanit_modulu_bagla(
        self,
        olay_kimligi: str,
        kanit,
    ):

        self.cekirdek.kanit_aktar(
            olay_kimligi,
            kanit,
        )


    def goruntu_modulu_bagla(
        self,
        olay_kimligi: str,
        goruntu,
    ):

        self.cekirdek.goruntu_aktar(
            olay_kimligi,
            goruntu,
        )


    def materyal_modulu_bagla(
        self,
        olay_kimligi: str,
        materyal,
    ):

        self.cekirdek.materyal_aktar(
            olay_kimligi,
            materyal,
        )


    def guven_konsensus_bagla(
        self,
        olay_kimligi: str,
        guven: float,
        konsensus: float,
    ):

        self.cekirdek.puanlari_aktar(
            olay_kimligi,
            guven,
            konsensus,
        )


    def sonucu_al(
        self,
        olay_kimligi: str,
    ):

        return self.cekirdek.tamamla(
            olay_kimligi
        )

class GercekSinifAdaptoru:


    def __init__(
        self,
        kanit_uzmani,
        goruntu_uzmani,
        materyal_uzmani,
        konsensus_motoru,
    ):

        self.kanit_uzmani = kanit_uzmani
        self.goruntu_uzmani = goruntu_uzmani
        self.materyal_uzmani = materyal_uzmani
        self.konsensus_motoru = konsensus_motoru



    def kanit_incele(
        self,
        veri,
    ):

        return self.kanit_uzmani.incele(
            veri
        )



    def goruntu_incele(
        self,
        veri,
    ):

        return self.goruntu_uzmani.incele(
            veri
        )



    def materyal_incele(
        self,
        veri,
    ):

        return self.materyal_uzmani.incele(
            veri
        )



    def konsensus_hesapla(
        self,
        veri,
    ):

        return self.konsensus_motoru.hesapla(
            veri
        )

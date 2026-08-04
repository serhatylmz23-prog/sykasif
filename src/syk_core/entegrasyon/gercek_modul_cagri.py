class GercekModulCagri:


    def __init__(
        self,
        kanit=None,
        goruntu=None,
        materyal=None,
        konsensus=None,
    ):

        self.kanit = kanit
        self.goruntu = goruntu
        self.materyal = materyal
        self.konsensus = konsensus


    def kanit_calistir(
        self,
        veri,
    ):

        if self.kanit is None:
            return veri

        return self.kanit(veri)


    def goruntu_calistir(
        self,
        veri,
    ):

        if self.goruntu is None:
            return veri

        return self.goruntu(veri)


    def materyal_calistir(
        self,
        veri,
    ):

        if self.materyal is None:
            return veri

        return self.materyal(veri)


    def konsensus_calistir(
        self,
        veri,
    ):

        if self.konsensus is None:
            return veri

        return self.konsensus(veri)


    def tum_akis(
        self,
        veri,
    ):

        sonuc = {}

        sonuc["kanit"] = (
            self.kanit_calistir(veri)
        )

        sonuc["goruntu"] = (
            self.goruntu_calistir(veri)
        )

        sonuc["materyal"] = (
            self.materyal_calistir(veri)
        )

        sonuc["konsensus"] = (
            self.konsensus_calistir(veri)
        )

        return sonuc

class RuntimeFastApiCoreBaglantisi:


    def __init__(
        self,
        runtime_servisi_baglantisi,
    ):
        self.runtime_servisi_baglantisi = (
            runtime_servisi_baglantisi
        )


    def runtime_olayi_aktar(
        self,
        olay,
    ):

        return (
            self.runtime_servisi_baglantisi.olay_isle(
                olay
            )
        )

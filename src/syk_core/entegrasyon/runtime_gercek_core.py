class GercekRuntimeCoreEntegrasyonu:


    def __init__(
        self,
        runtime_servisi,
        aktarici,
    ):
        self.runtime_servisi = runtime_servisi
        self.aktarici = aktarici


    def olay_uret_ve_aktar(
        self,
        arastirma_kimligi: str,
    ):

        olay = self.runtime_servisi.olay_uret(
            arastirma_kimligi=(
                arastirma_kimligi
            )
        )

        return self.aktarici.olay_aktar(
            olay.arastirma_kimligi,
            str(olay.tur.value),
        )

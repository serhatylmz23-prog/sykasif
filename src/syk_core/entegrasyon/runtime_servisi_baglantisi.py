class RuntimeServisiCoreBaglantisi:


    def __init__(
        self,
        aktarici,
    ):
        self.aktarici = aktarici


    def olay_isle(
        self,
        olay,
    ):

        olay_kimligi = (
            olay.arastirma_kimligi
        )

        durum = (
            olay.tur.value
            if hasattr(
                olay.tur,
                "value",
            )
            else str(
                olay.tur
            )
        )

        return self.aktarici.olay_aktar(
            olay_kimligi,
            durum,
        )

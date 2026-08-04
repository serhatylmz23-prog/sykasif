class GercekModulTekOlayZinciri:


    def __init__(
        self,
        fabrika,
        motor,
    ):

        self.fabrika = fabrika
        self.motor = motor



    def calistir(
        self,
        olay_kimligi: str,
        veri,
    ):

        adaptor = (
            self.fabrika.olustur()
        )


        self.motor.adaptor = adaptor


        return self.motor.degerlendir(
            olay_kimligi,
            veri,
        )

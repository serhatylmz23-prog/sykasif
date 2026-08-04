from .gercek_sinif_adaptoru import (
    GercekSinifAdaptoru,
)


class MevcutModulFabrikasi:


    def __init__(
        self,
        kanit_sinifi,
        goruntu_sinifi,
        materyal_sinifi,
        konsensus_sinifi,
    ):

        self.kanit_sinifi = kanit_sinifi
        self.goruntu_sinifi = goruntu_sinifi
        self.materyal_sinifi = materyal_sinifi
        self.konsensus_sinifi = konsensus_sinifi



    def olustur(
        self,
    ):

        return GercekSinifAdaptoru(
            self.kanit_sinifi(),
            self.goruntu_sinifi(),
            self.materyal_sinifi(),
            self.konsensus_sinifi(),
        )

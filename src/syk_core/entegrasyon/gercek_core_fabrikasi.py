from .gercek_modul_cagri import (
    GercekModulCagri,
)


class GercekCoreFabrikasi:


    def __init__(
        self,
        cekirdek,
    ):

        self.cekirdek = cekirdek



    def olustur(
        self,
        kanit_modulu,
        goruntu_modulu,
        materyal_modulu,
        konsensus_modulu,
    ):

        return GercekModulCagri(
            kanit=kanit_modulu,
            goruntu=goruntu_modulu,
            materyal=materyal_modulu,
            konsensus=konsensus_modulu,
        )

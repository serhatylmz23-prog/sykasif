import importlib


class ImportDogrulamaMotoru:


    def __init__(
        self,
        moduller,
    ):

        self.moduller = moduller



    def kontrol_et(
        self,
    ):

        sonuc = {}

        for modul in self.moduller:

            try:

                importlib.import_module(
                    modul
                )

                sonuc[modul] = True

            except Exception:

                sonuc[modul] = False


        return sonuc

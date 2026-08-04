from dataclasses import dataclass


@dataclass
class RuntimeCoreAktarimSonucu:

    olay_kimligi: str
    runtime_durumu: str
    aktarim_durumu: str = "beklemede"



class RuntimeCoreAktarici:


    def __init__(
        self,
        core_koprusu,
    ):
        self.core_koprusu = core_koprusu


    def olay_aktar(
        self,
        olay_kimligi: str,
        runtime_durumu: str,
    ):

        sonuc = self.core_koprusu.olay_baslat(
            olay_kimligi
        )

        self.core_koprusu.tamamla(
            olay_kimligi
        )

        return RuntimeCoreAktarimSonucu(
            olay_kimligi,
            runtime_durumu,
            "aktarildi",
        )

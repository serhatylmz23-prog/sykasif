from dataclasses import dataclass, field


@dataclass
class KaynakTuru:

    kimlik: str
    ad: str
    aciklama: str

    aktif: bool = True

    alt_kaynaklar: list[str] = field(
        default_factory=list
    )


class KaynakTurYonetici:


    def __init__(self):
        self.turler = {}


    def tur_ekle(
        self,
        kaynak_turu: KaynakTuru,
    ):

        self.turler[
            kaynak_turu.kimlik
        ] = kaynak_turu


    def alt_kaynak_ekle(
        self,
        kimlik: str,
        kaynak: str,
    ):

        self.turler[
            kimlik
        ].alt_kaynaklar.append(
            kaynak
        )


    def aktif_turleri_getir(
        self,
    ):

        return [
            tur
            for tur in self.turler.values()
            if tur.aktif
        ]

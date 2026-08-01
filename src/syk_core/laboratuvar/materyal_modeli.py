from dataclasses import dataclass, field


@dataclass
class MateryalKaydi:

    materyal_kimligi: str
    materyal_adi: str

    kategori: str

    alasim_bilgileri: list[str] = field(
        default_factory=list
    )

    fiziksel_veriler: list[str] = field(
        default_factory=list
    )

    kimyasal_veriler: list[str] = field(
        default_factory=list
    )

    frekans_tepkileri: list[str] = field(
        default_factory=list
    )

    dalga_boyu_verileri: list[str] = field(
        default_factory=list
    )

    derinlik_kayitlari: list[str] = field(
        default_factory=list
    )


class MateryalLaboratuvarYoneticisi:


    def __init__(self):
        self.materyaller = {}


    def materyal_kaydet(
        self,
        materyal: MateryalKaydi,
    ):

        self.materyaller[
            materyal.materyal_kimligi
        ] = materyal

        return materyal


    def veri_ekle(
        self,
        materyal_kimligi: str,
        alan: str,
        veri: str,
    ):

        materyal = self.materyaller[
            materyal_kimligi
        ]

        getattr(
            materyal,
            alan
        ).append(
            veri
        )


    def materyal_getir(
        self,
        materyal_kimligi: str,
    ):

        return self.materyaller.get(
            materyal_kimligi
        )

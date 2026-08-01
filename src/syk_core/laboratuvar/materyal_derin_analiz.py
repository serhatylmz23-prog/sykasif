from dataclasses import dataclass, field


@dataclass
class DerinlikAnalizi:

    derinlik_cm: int

    frekans_tepkisi: list[str] = field(
        default_factory=list
    )

    dalga_boyu_tepkisi: list[str] = field(
        default_factory=list
    )

    sensor_kayitlari: list[str] = field(
        default_factory=list
    )

    kosul_testleri: list[str] = field(
        default_factory=list
    )


@dataclass
class MateryalDerinAnaliz:

    materyal_kimligi: str

    element_verileri: list[str] = field(
        default_factory=list
    )

    fiziksel_ozellikler: list[str] = field(
        default_factory=list
    )

    kimyasal_ozellikler: list[str] = field(
        default_factory=list
    )

    derinlik_analizleri: list[DerinlikAnalizi] = field(
        default_factory=list
    )


class MateryalDerinAnalizYoneticisi:


    def __init__(self):
        self.kayitlar = {}


    def kaydet(
        self,
        analiz: MateryalDerinAnaliz,
    ):
        self.kayitlar[
            analiz.materyal_kimligi
        ] = analiz


    def veri_ekle(
        self,
        materyal_kimligi: str,
        alan: str,
        veri: str,
    ):

        getattr(
            self.kayitlar[materyal_kimligi],
            alan
        ).append(
            veri
        )


    def derinlik_kaydi_ekle(
        self,
        materyal_kimligi: str,
        derinlik: DerinlikAnalizi,
    ):

        self.kayitlar[
            materyal_kimligi
        ].derinlik_analizleri.append(
            derinlik
        )


    def getir(
        self,
        materyal_kimligi: str,
    ):

        return self.kayitlar.get(
            materyal_kimligi
        )

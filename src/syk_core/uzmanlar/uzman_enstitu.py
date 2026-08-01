from dataclasses import dataclass, field


class UzmanErisimYasagi(Exception):
    pass


@dataclass
class UzmanEnstitusu:

    enstitu_kimligi: str
    enstitu_adi: str
    bilim_alani: str

    uzmanlar: list[str] = field(
        default_factory=list
    )

    aktif: bool = True


@dataclass
class UzmanBaglantisi:

    uzman_kimligi: str
    uzman_adi: str
    bagli_enstitu: str

    aktif: bool = True
    emekli: bool = False


class UzmanEnstituAgaci:

    def __init__(self):
        self.enstituler = {}
        self.uzmanlar = {}

    def enstitu_ekle(
        self,
        enstitu: UzmanEnstitusu,
    ):
        self.enstituler[
            enstitu.enstitu_kimligi
        ] = enstitu


    def uzman_ekle(
        self,
        uzman: UzmanBaglantisi,
    ):
        if uzman.bagli_enstitu not in self.enstituler:
            raise ValueError(
                "Bagli enstitu bulunamadi."
            )

        self.uzmanlar[
            uzman.uzman_kimligi
        ] = uzman

        self.enstituler[
            uzman.bagli_enstitu
        ].uzmanlar.append(
            uzman.uzman_kimligi
        )


    def aile_erisimi_kontrol(
        self,
        isteyen_uzman: str,
        hedef_uzman: str,
    ) -> bool:

        kaynak = self.uzmanlar.get(
            isteyen_uzman
        )

        hedef = self.uzmanlar.get(
            hedef_uzman
        )

        if kaynak is None or hedef is None:
            return False

        return (
            kaynak.bagli_enstitu
            ==
            hedef.bagli_enstitu
        )


    def veri_gorme_izni(
        self,
        isteyen_uzman: str,
        hedef_uzman: str,
    ):
        if not self.aile_erisimi_kontrol(
            isteyen_uzman,
            hedef_uzman,
        ):
            raise UzmanErisimYasagi(
                "Uzman farkli bilim ailesine erisemez."
            )

        return True


    def emekliye_ayir(
        self,
        uzman_kimligi: str,
    ):
        uzman = self.uzmanlar.get(
            uzman_kimligi
        )

        if uzman:
            uzman.aktif = False
            uzman.emekli = True

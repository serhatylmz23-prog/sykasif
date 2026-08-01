from dataclasses import dataclass


class UzmanYetkiYasagi(Exception):
    pass


@dataclass
class UzmanYetki:
    uzman_kimligi: str
    analiz_yapabilir: bool = True
    arastirma_yapabilir: bool = True
    oneri_uretebilir: bool = True
    karar_verebilir: bool = False


def karar_kontrolu(
    yetki: UzmanYetki,
):
    if yetki.karar_verebilir:
        return False

    return True

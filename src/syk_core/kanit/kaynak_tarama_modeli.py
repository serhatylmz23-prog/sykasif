from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class KaynakTarama:

    kaynak_kimligi: str
    kaynak_turu: str
    kaynak_adi: str

    analiz_durumu: str = "bekliyor"

    ogrenilen_veriler: list[str] = field(
        default_factory=list
    )

    karsilastirma_notlari: list[str] = field(
        default_factory=list
    )

    zaman: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )


class KaynakTaramaYoneticisi:


    def __init__(self):
        self.kaynak_havuzu = {}


    def kaynak_ekle(
        self,
        kaynak: KaynakTaramasi,
    ):

        self.kaynak_havuzu[
            kaynak.kaynak_kimligi
        ] = kaynak

        return kaynak


    def veri_ekle(
        self,
        kaynak_kimligi: str,
        veri: str,
    ):

        self.kaynak_havuzu[
            kaynak_kimligi
        ].ogrenilen_veriler.append(
            veri
        )


    def karsilastirma_ekle(
        self,
        kaynak_kimligi: str,
        not_: str,
    ):

        self.kaynak_havuzu[
            kaynak_kimligi
        ].karsilastirma_notlari.append(
            not_
        )


    def analiz_tamamla(
        self,
        kaynak_kimligi: str,
    ):

        self.kaynak_havuzu[
            kaynak_kimligi
        ].analiz_durumu = "tamamlandi"


    def kaynak_getir(
        self,
        kaynak_kimligi: str,
    ):

        return self.kaynak_havuzu.get(
            kaynak_kimligi
        )

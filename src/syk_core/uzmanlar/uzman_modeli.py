from dataclasses import dataclass, field
from datetime import datetime, timezone


class UzmanKararYasagi(Exception):
    """
    Uzmanlar?n kendi ba??na nihai karar vermesini engeller.
    """
    pass


@dataclass
class UzmanModeli:
    """
    SYK-CORE-001 temel uzman modeli.

    Uzman:
    - ara?t?r?r,
    - ??renir,
    - analiz eder,
    - ?neri ?retir.

    Uzman:
    - nihai karar vermez.
    """

    uzman_kimligi: str
    uzman_adi: str
    bilim_ailesi: str
    gorev_alani: str

    aktif: bool = True
    deneyim_kaydi: list[str] = field(
        default_factory=list
    )
    ogrenme_kaydi: list[str] = field(
        default_factory=list
    )

    olusturma_zamani: str = field(
        default_factory=lambda:
            datetime.now(
                timezone.utc
            ).isoformat()
    )

    def arastirma_kaydi_ekle(
        self,
        kayit: str,
    ) -> None:
        self.deneyim_kaydi.append(
            kayit
        )

    def ogrenme_kaydi_ekle(
        self,
        bilgi: str,
    ) -> None:
        self.ogrenme_kaydi.append(
            bilgi
        )

    def analiz_onerisi_uret(
        self,
        konu: str,
    ) -> dict:
        return {
            "uzman": self.uzman_adi,
            "konu": konu,
            "durum": "?neri",
            "nihai_karar": False,
        }

    def karar_ver(
        self,
        karar: str,
    ) -> None:
        raise UzmanKararYasagi(
            "Uzman nihai karar veremez. "
            "Karar ak??? Ka?if onay? ile y?r?t?l?r."
        )

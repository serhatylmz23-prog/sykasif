from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class OlayKaydi:

    olay_kimligi: str

    kanitlar: list[str] = field(
        default_factory=list
    )

    uzman_sonuclari: list[str] = field(
        default_factory=list
    )

    guven_puani: float = 0.0

    konsensus_puani: float = 0.0

    durum: str = "kayitli"

    zaman: str = field(
        default_factory=lambda:
            datetime.now(timezone.utc).isoformat()
    )



class OlayKayitZinciri:


    def __init__(self):

        self.kayitlar = {}



    def kaydet(
        self,
        olay_kimligi: str,
    ):

        kayit = OlayKaydi(
            olay_kimligi
        )

        self.kayitlar[
            olay_kimligi
        ] = kayit

        return kayit



    def kanit_ekle(
        self,
        olay_kimligi: str,
        kanit: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].kanitlar.append(
            kanit
        )



    def uzman_sonucu_ekle(
        self,
        olay_kimligi: str,
        sonuc: str,
    ):

        self.kayitlar[
            olay_kimligi
        ].uzman_sonuclari.append(
            sonuc
        )



    def puan_kaydet(
        self,
        olay_kimligi: str,
        guven: float,
        konsensus: float,
    ):

        kayit = self.kayitlar[
            olay_kimligi
        ]

        kayit.guven_puani = guven
        kayit.konsensus_puani = konsensus



    def dogrula(
        self,
        olay_kimligi: str,
    ):

        kayit = self.kayitlar.get(
            olay_kimligi
        )

        if kayit is None:
            return False


        return (
            bool(kayit.kanitlar)
            and
            bool(kayit.uzman_sonuclari)
        )



    def getir(
        self,
        olay_kimligi: str,
    ):

        return self.kayitlar.get(
            olay_kimligi
        )

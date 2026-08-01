from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OnayKaydi:
    konu: str
    uzman_onerisi: str

    bilge_kaan_durumu: str = "bekliyor"
    kasif_durumu: str = "bekliyor"

    sonuc: str = "bekliyor"

    zaman: str = ""

    def __post_init__(self):
        self.zaman = datetime.now(
            timezone.utc
        ).isoformat()


class OnayZinciri:

    def __init__(self):
        self.kayitlar = []


    def uzman_onerisi_al(
        self,
        konu: str,
        oneri: str,
    ):
        kayit = OnayKaydi(
            konu=konu,
            uzman_onerisi=oneri,
        )

        self.kayitlar.append(
            kayit
        )

        return kayit


    def bilge_kaan_degerlendir(
        self,
        kayit: OnayKaydi,
        sonuc: str,
    ):
        kayit.bilge_kaan_durumu = sonuc


    def kasif_degerlendir(
        self,
        kayit: OnayKaydi,
        sonuc: str,
    ):
        kayit.kasif_durumu = sonuc


    def nihai_karar(
        self,
        kayit: OnayKaydi,
    ):

        if (
            kayit.bilge_kaan_durumu
            == "onay"
            and
            kayit.kasif_durumu
            == "onay"
        ):
            kayit.sonuc = "yururluk"

        else:
            kayit.sonuc = "beklemede"

        return kayit.sonuc

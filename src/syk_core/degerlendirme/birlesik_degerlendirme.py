from dataclasses import dataclass, field


@dataclass
class BirlesikDegerlendirmeKaydi:

    degerlendirme_kimligi: str

    goruntu_kaniti: list[str] = field(
        default_factory=list
    )

    materyal_analizi: list[str] = field(
        default_factory=list
    )

    kaynak_guven_puani: float = 0.0

    celiski_kayitlari: list[str] = field(
        default_factory=list
    )

    uzman_yorumlari: list[str] = field(
        default_factory=list
    )

    durum: str = "beklemede"


class BirlesikDegerlendirmeYoneticisi:


    def __init__(self):
        self.kayitlar = {}


    def kaydet(
        self,
        kayit: BirlesikDegerlendirmeKaydi,
    ):
        self.kayitlar[
            kayit.degerlendirme_kimligi
        ] = kayit

        return kayit


    def goruntu_ekle(
        self,
        kimlik: str,
        veri: str,
    ):
        self.kayitlar[
            kimlik
        ].goruntu_kaniti.append(
            veri
        )


    def materyal_ekle(
        self,
        kimlik: str,
        veri: str,
    ):
        self.kayitlar[
            kimlik
        ].materyal_analizi.append(
            veri
        )


    def guven_puani_ver(
        self,
        kimlik: str,
        puan: float,
    ):
        self.kayitlar[
            kimlik
        ].kaynak_guven_puani = puan


    def celiski_ekle(
        self,
        kimlik: str,
        veri: str,
    ):
        self.kayitlar[
            kimlik
        ].celiski_kayitlari.append(
            veri
        )


    def uzman_yorumu_ekle(
        self,
        kimlik: str,
        yorum: str,
    ):
        self.kayitlar[
            kimlik
        ].uzman_yorumlari.append(
            yorum
        )


    def degerlendirme_tamamla(
        self,
        kimlik: str,
    ):
        self.kayitlar[
            kimlik
        ].durum = "incelendi"


    def getir(
        self,
        kimlik: str,
    ):
        return self.kayitlar.get(
            kimlik
        )

from dataclasses import dataclass, field


@dataclass
class GoruntuKaniti:

    goruntu_kimligi: str

    kaynak_bilgisi: str

    gerceklik_sonucu: str = "incelenmedi"

    manipulasyon_suphesi: list[str] = field(
        default_factory=list
    )

    nesne_adaylari: list[str] = field(
        default_factory=list
    )

    materyal_adaylari: list[str] = field(
        default_factory=list
    )

    uzman_yorumlari: list[str] = field(
        default_factory=list
    )

    kanit_baglantilari: list[str] = field(
        default_factory=list
    )


class GoruntuKanitYoneticisi:


    def __init__(self):
        self.kayitlar = {}


    def kaydet(
        self,
        kanit: GoruntuKaniti,
    ):

        self.kayitlar[
            kanit.goruntu_kimligi
        ] = kanit

        return kanit


    def gerceklik_sonucu_ekle(
        self,
        kimlik: str,
        sonuc: str,
    ):

        self.kayitlar[
            kimlik
        ].gerceklik_sonucu = sonuc


    def suphe_ekle(
        self,
        kimlik: str,
        aciklama: str,
    ):

        self.kayitlar[
            kimlik
        ].manipulasyon_suphesi.append(
            aciklama
        )


    def nesne_adayi_ekle(
        self,
        kimlik: str,
        nesne: str,
    ):

        self.kayitlar[
            kimlik
        ].nesne_adaylari.append(
            nesne
        )


    def materyal_adayi_ekle(
        self,
        kimlik: str,
        materyal: str,
    ):

        self.kayitlar[
            kimlik
        ].materyal_adaylari.append(
            materyal
        )


    def kanit_bagla(
        self,
        kimlik: str,
        kanit: str,
    ):

        self.kayitlar[
            kimlik
        ].kanit_baglantilari.append(
            kanit
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


    def getir(
        self,
        kimlik: str,
    ):

        return self.kayitlar.get(
            kimlik
        )

from dataclasses import dataclass, field


@dataclass
class GoruntuKaydi:

    veri_kimligi: str

    veri_turu: str

    kaynak: str

    konum_bilgisi: str | None = None

    gerceklik_durumu: str = "incelenmedi"

    tespitler: list[str] = field(
        default_factory=list
    )

    supheli_bolgeler: list[dict] = field(
        default_factory=list
    )

    uzman_notlari: list[str] = field(
        default_factory=list
    )


class GoruntuUzmani:


    def __init__(self):
        self.kayitlar = {}


    def goruntu_kaydet(
        self,
        kayit: GoruntuKaydi,
    ):
        self.kayitlar[
            kayit.veri_kimligi
        ] = kayit

        return kayit


    def gerceklik_incele(
        self,
        veri_kimligi: str,
        sonuc: str,
    ):

        self.kayitlar[
            veri_kimligi
        ].gerceklik_durumu = sonuc


    def supheli_bolge_isaretle(
        self,
        veri_kimligi: str,
        x: int,
        y: int,
        genislik: int,
        yukseklik: int,
        aciklama: str,
    ):

        self.kayitlar[
            veri_kimligi
        ].supheli_bolgeler.append(
            {
                "x": x,
                "y": y,
                "genislik": genislik,
                "yukseklik": yukseklik,
                "aciklama": aciklama,
            }
        )


    def tespit_ekle(
        self,
        veri_kimligi: str,
        tespit: str,
    ):

        self.kayitlar[
            veri_kimligi
        ].tespitler.append(
            tespit
        )


    def konum_yoksa_uzmana_gonder(
        self,
        veri_kimligi: str,
    ) -> bool:

        return (
            self.kayitlar[
                veri_kimligi
            ].konum_bilgisi
            is None
        )


    def getir(
        self,
        veri_kimligi: str,
    ):

        return self.kayitlar.get(
            veri_kimligi
        )

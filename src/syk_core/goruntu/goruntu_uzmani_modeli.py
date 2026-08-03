from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


GoruntuOlayDinleyicisi = Callable[
    [str, dict[str, Any]],
    None,
]


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

    kare_genisligi: int | None = None
    kare_yuksekligi: int | None = None
    kare_numarasi: int = 0
    zaman_ms: int = 0


class GoruntuUzmani:
    def __init__(self):
        self.kayitlar: dict[
            str,
            GoruntuKaydi,
        ] = {}

        self._dinleyiciler: list[
            GoruntuOlayDinleyicisi
        ] = []

    def dinleyici_ekle(
        self,
        dinleyici: GoruntuOlayDinleyicisi,
    ) -> None:
        if dinleyici not in self._dinleyiciler:
            self._dinleyiciler.append(
                dinleyici
            )

    def dinleyici_kaldir(
        self,
        dinleyici: GoruntuOlayDinleyicisi,
    ) -> None:
        if dinleyici in self._dinleyiciler:
            self._dinleyiciler.remove(
                dinleyici
            )

    def goruntu_kaydet(
        self,
        kayit: GoruntuKaydi,
    ):
        self.kayitlar[
            kayit.veri_kimligi
        ] = kayit

        self._olay_yayinla(
            "goruntu_kaydedildi",
            {
                "veri_kimligi": (
                    kayit.veri_kimligi
                ),
                "kayit": kayit,
            },
        )

        return kayit

    def gerceklik_incele(
        self,
        veri_kimligi: str,
        sonuc: str,
    ):
        kayit = self._zorunlu_getir(
            veri_kimligi
        )

        kayit.gerceklik_durumu = sonuc

        self._olay_yayinla(
            "gerceklik_incelendi",
            {
                "veri_kimligi": veri_kimligi,
                "sonuc": sonuc,
                "kayit": kayit,
            },
        )

    def supheli_bolge_isaretle(
        self,
        veri_kimligi: str,
        x: int,
        y: int,
        genislik: int,
        yukseklik: int,
        aciklama: str,
        guven: float = 75.0,
        sinyal_turu: str | None = None,
    ):
        kayit = self._zorunlu_getir(
            veri_kimligi
        )

        if x < 0 or y < 0:
            raise ValueError(
                "Bölge başlangıç değerleri "
                "negatif olamaz."
            )

        if genislik <= 0 or yukseklik <= 0:
            raise ValueError(
                "Bölge ölçüleri sıfırdan "
                "büyük olmalıdır."
            )

        bolge = {
            "x": x,
            "y": y,
            "genislik": genislik,
            "yukseklik": yukseklik,
            "aciklama": aciklama,
            "guven": max(
                0.0,
                min(99.9, float(guven)),
            ),
            "sinyal_turu": sinyal_turu,
        }

        kayit.supheli_bolgeler.append(
            bolge
        )

        self._olay_yayinla(
            "supheli_bolge_isaretlendi",
            {
                "veri_kimligi": veri_kimligi,
                "kayit": kayit,
                "bolge": bolge,
            },
        )

        return bolge

    def tespit_ekle(
        self,
        veri_kimligi: str,
        tespit: str,
    ):
        kayit = self._zorunlu_getir(
            veri_kimligi
        )

        kayit.tespitler.append(
            tespit
        )

        self._olay_yayinla(
            "tespit_eklendi",
            {
                "veri_kimligi": veri_kimligi,
                "tespit": tespit,
                "kayit": kayit,
            },
        )

    def konum_yoksa_uzmana_gonder(
        self,
        veri_kimligi: str,
    ) -> bool:
        return (
            self._zorunlu_getir(
                veri_kimligi
            ).konum_bilgisi
            is None
        )

    def getir(
        self,
        veri_kimligi: str,
    ):
        return self.kayitlar.get(
            veri_kimligi
        )

    def _zorunlu_getir(
        self,
        veri_kimligi: str,
    ) -> GoruntuKaydi:
        try:
            return self.kayitlar[
                veri_kimligi
            ]
        except KeyError as error:
            raise KeyError(
                f"Görüntü kaydı bulunamadı: "
                f"{veri_kimligi}"
            ) from error

    def _olay_yayinla(
        self,
        olay_turu: str,
        veri: dict[str, Any],
    ) -> None:
        for dinleyici in tuple(
            self._dinleyiciler
        ):
            dinleyici(
                olay_turu,
                veri,
            )
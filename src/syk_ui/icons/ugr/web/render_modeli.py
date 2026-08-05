"""UGR web ikon render modelleri."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any


@dataclass(frozen=True, slots=True)
class IkonWebStili:
    """Tarayıcıya aktarılacak görsel stil."""

    durum: str
    animasyon: str
    renk_rolu: str
    animasyon_suresi_ms: int
    tekrarli: bool
    parlaklik: float
    saydamlik: float
    olcek: float

    def css_degiskenleri(self) -> dict[str, str]:
        """CSS özel değişkenlerini üretir."""

        tekrar_sayisi = (
            "infinite"
            if self.tekrarli
            else "1"
        )

        return {
            "--syk-icon-duration": (
                f"{self.animasyon_suresi_ms}ms"
            ),
            "--syk-icon-iteration": tekrar_sayisi,
            "--syk-icon-brightness": str(
                self.parlaklik
            ),
            "--syk-icon-opacity": str(
                self.saydamlik
            ),
            "--syk-icon-scale": str(
                self.olcek
            ),
        }

    def css_satiri(self) -> str:
        """HTML style niteliği için CSS metni üretir."""

        return ";".join(
            f"{anahtar}:{deger}"
            for anahtar, deger
            in self.css_degiskenleri().items()
        )


@dataclass(frozen=True, slots=True)
class IkonWebRenderKaydi:
    """Tek ikon için tarayıcı render çıktısı."""

    ikon_kimligi: str
    kategori: str
    etiket: str
    dosya_yolu: str
    durum: str
    gorunum_modu: str
    aktif: bool
    stil: IkonWebStili
    bagli_nesne_kimligi: str | None = None

    def css_siniflari(self) -> tuple[str, ...]:
        """İkona uygulanacak güvenli sınıfları üretir."""

        siniflar = [
            "syk-ugr-icon",
            f"syk-ugr-state-{self.durum}",
            f"syk-ugr-animation-{self.stil.animasyon}",
            f"syk-ugr-role-{self.stil.renk_rolu}",
            f"syk-ugr-view-{self.gorunum_modu}",
        ]

        if not self.aktif:
            siniflar.append(
                "syk-ugr-icon-inactive"
            )

        return tuple(siniflar)

    def veri_nitelikleri(self) -> dict[str, str]:
        """Tarayıcı veri niteliklerini üretir."""

        sonuc = {
            "data-syk-icon-id": self.ikon_kimligi,
            "data-syk-category": self.kategori,
            "data-syk-label": self.etiket,
            "data-syk-state": self.durum,
            "data-syk-view": self.gorunum_modu,
            "data-syk-animation": (
                self.stil.animasyon
            ),
            "data-syk-color-role": (
                self.stil.renk_rolu
            ),
            "data-syk-active": (
                "true"
                if self.aktif
                else "false"
            ),
        }

        if self.bagli_nesne_kimligi:
            sonuc[
                "data-syk-object-id"
            ] = self.bagli_nesne_kimligi

        return sonuc

    def html(self) -> str:
        """Bağımsız ikon bileşeni HTML'i üretir."""

        siniflar = " ".join(
            escape(sinif_adi, quote=True)
            for sinif_adi in self.css_siniflari()
        )

        nitelikler = " ".join(
            (
                f'{escape(anahtar, quote=True)}='
                f'"{escape(deger, quote=True)}"'
            )
            for anahtar, deger
            in self.veri_nitelikleri().items()
        )

        stil = escape(
            self.stil.css_satiri(),
            quote=True,
        )

        kaynak = escape(
            self.dosya_yolu,
            quote=True,
        )

        etiket = escape(
            self.etiket,
            quote=True,
        )

        kimlik = escape(
            self.ikon_kimligi,
            quote=True,
        )

        return (
            f'<button class="{siniflar}" '
            f'{nitelikler} '
            f'style="{stil}" '
            f'type="button" '
            f'aria-label="{etiket}" '
            f'title="{etiket}">'
            f'<span class="syk-ugr-icon-frame">'
            f'<img '
            f'class="syk-ugr-icon-image" '
            f'src="{kaynak}" '
            f'alt="" '
            f'draggable="false">'
            f'<span '
            f'class="syk-ugr-icon-energy" '
            f'aria-hidden="true"></span>'
            f'<span '
            f'class="syk-ugr-icon-scan" '
            f'aria-hidden="true"></span>'
            f'<span '
            f'class="syk-ugr-icon-status" '
            f'aria-hidden="true"></span>'
            f'</span>'
            f'<span class="syk-ugr-icon-caption">'
            f'{etiket}'
            f'</span>'
            f'<span class="syk-ugr-icon-runtime-id">'
            f'{kimlik}'
            f'</span>'
            f'</button>'
        )

    def json_verisi(self) -> dict[str, Any]:
        """API ve testler için sözlük üretir."""

        return {
            "ikon_kimligi": self.ikon_kimligi,
            "kategori": self.kategori,
            "etiket": self.etiket,
            "dosya_yolu": self.dosya_yolu,
            "durum": self.durum,
            "gorunum_modu": self.gorunum_modu,
            "aktif": self.aktif,
            "bagli_nesne_kimligi": (
                self.bagli_nesne_kimligi
            ),
            "stil": {
                "animasyon": (
                    self.stil.animasyon
                ),
                "renk_rolu": (
                    self.stil.renk_rolu
                ),
                "animasyon_suresi_ms": (
                    self.stil.animasyon_suresi_ms
                ),
                "tekrarli": (
                    self.stil.tekrarli
                ),
                "parlaklik": (
                    self.stil.parlaklik
                ),
                "saydamlik": (
                    self.stil.saydamlik
                ),
                "olcek": self.stil.olcek,
            },
            "css_siniflari": list(
                self.css_siniflari()
            ),
            "veri_nitelikleri": (
                self.veri_nitelikleri()
            ),
        }

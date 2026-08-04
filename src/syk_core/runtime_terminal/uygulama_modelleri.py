"""SyKaşif terminal uygulaması yapılandırma modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TerminalUygulamasiHatasi(RuntimeError):
    """Terminal uygulaması oluşturma veya çalışma hatası."""


class CalismaKipi(str, Enum):
    GELISTIRME = "geliştirme"
    LABORATUVAR = "laboratuvar"
    SAHA = "saha"
    URETIM = "üretim"


@dataclass(slots=True, frozen=True)
class YetkiliCihazAyari:
    cihaz_kimligi: str
    ad: str
    cihaz_turu: str
    yetki_seviyesi: str
    cihaz_parmak_izi: str
    baslangicta_bagli: bool = False
    aciklama: str | None = None
    veri: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cihaz_kimligi.strip():
            raise ValueError(
                "Cihaz kimliği boş olamaz."
            )

        if not self.ad.strip():
            raise ValueError(
                "Cihaz adı boş olamaz."
            )

        if not self.cihaz_turu.strip():
            raise ValueError(
                "Cihaz türü boş olamaz."
            )

        if not self.yetki_seviyesi.strip():
            raise ValueError(
                "Yetki seviyesi boş olamaz."
            )

        if not self.cihaz_parmak_izi.strip():
            raise ValueError(
                "Cihaz parmak izi boş olamaz."
            )

    def sozluk(self) -> dict[str, Any]:
        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "ad": self.ad,
            "cihaz_türü": self.cihaz_turu,
            "yetki_seviyesi": self.yetki_seviyesi,
            "cihaz_parmak_izi": self.cihaz_parmak_izi,
            "başlangıçta_bağlı": self.baslangicta_bagli,
            "açıklama": self.aciklama,
            "veri": dict(self.veri),
        }


@dataclass(slots=True, frozen=True)
class TerminalUygulamasiAyarlari:
    calisma_kipi: CalismaKipi = CalismaKipi.GELISTIRME
    ana_makine: str = "127.0.0.1"
    baglanti_noktasi: int = 8014
    panel_yolu: str = "/terminal"
    panel_veri_yolu: str = "/terminal/veri"
    dis_ag_erisimine_izin_ver: bool = False
    yeniden_yukleme: bool = False
    gunluk_seviyesi: str = "info"
    ana_makine_cihaz_kimligi: str = "ANA-MASAUSTU"
    sykasif_uygulama_kimligi: str = "SYKASIF"
    sykasif_calistirma_yolu: str = "."
    ayar_dosyasi: str | None = None
    durum_dosyasi: str = (
        "artifacts/syk_core_parca_006/"
        "terminal_uygulamasi_durumu.json"
    )
    yetkili_cihazlar: tuple[YetkiliCihazAyari, ...] = ()
    veri: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ana_makine.strip():
            raise ValueError(
                "Ana makine adresi boş olamaz."
            )

        if not 1 <= self.baglanti_noktasi <= 65535:
            raise ValueError(
                "Bağlantı noktası 1 ile 65535 arasında olmalıdır."
            )

        if not self.panel_yolu.startswith("/"):
            raise ValueError(
                "Panel yolu eğik çizgi ile başlamalıdır."
            )

        if not self.panel_veri_yolu.startswith("/"):
            raise ValueError(
                "Panel veri yolu eğik çizgi ile başlamalıdır."
            )

        if not self.ana_makine_cihaz_kimligi.strip():
            raise ValueError(
                "Ana makine cihaz kimliği boş olamaz."
            )

        if not self.sykasif_uygulama_kimligi.strip():
            raise ValueError(
                "SyKaşif uygulama kimliği boş olamaz."
            )

        if not self.sykasif_calistirma_yolu.strip():
            raise ValueError(
                "SyKaşif çalıştırma yolu boş olamaz."
            )

    @classmethod
    def varsayilan(
        cls,
    ) -> "TerminalUygulamasiAyarlari":
        return cls(
            yetkili_cihazlar=(
                YetkiliCihazAyari(
                    cihaz_kimligi="ANA-MASAUSTU",
                    ad="SyKaşif Ana Makine",
                    cihaz_turu="masaüstü",
                    yetki_seviyesi="Kurucu Kaan",
                    cihaz_parmak_izi=(
                        "ANA-MASAUSTU-YEREL-PARMAK-IZI"
                    ),
                    baslangicta_bagli=True,
                ),
                YetkiliCihazAyari(
                    cihaz_kimligi="SAMSUNG-TABLET",
                    ad="Samsung Ana Saha Terminali",
                    cihaz_turu="tablet",
                    yetki_seviyesi="Bilge Kaan",
                    cihaz_parmak_izi=(
                        "SAMSUNG-TABLET-PARMAK-IZI"
                    ),
                    baslangicta_bagli=False,
                ),
                YetkiliCihazAyari(
                    cihaz_kimligi="IPHONE-8-PLUS",
                    ad="iPhone Yetkili Yardımcı Terminal",
                    cihaz_turu="telefon",
                    yetki_seviyesi="işletmen",
                    cihaz_parmak_izi=(
                        "IPHONE-8-PLUS-PARMAK-IZI"
                    ),
                    baslangicta_bagli=False,
                ),
            )
        )

    def sozluk(self) -> dict[str, Any]:
        return {
            "çalışma_kipi": self.calisma_kipi.value,
            "ana_makine": self.ana_makine,
            "bağlantı_noktası": self.baglanti_noktasi,
            "panel_yolu": self.panel_yolu,
            "panel_veri_yolu": self.panel_veri_yolu,
            "dış_ağ_erişimine_izin_ver": (
                self.dis_ag_erisimine_izin_ver
            ),
            "yeniden_yükleme": self.yeniden_yukleme,
            "günlük_seviyesi": self.gunluk_seviyesi,
            "ana_makine_cihaz_kimliği": (
                self.ana_makine_cihaz_kimligi
            ),
            "sykasif_uygulama_kimliği": (
                self.sykasif_uygulama_kimligi
            ),
            "sykasif_çalıştırma_yolu": (
                self.sykasif_calistirma_yolu
            ),
            "ayar_dosyası": self.ayar_dosyasi,
            "durum_dosyası": self.durum_dosyasi,
            "yetkili_cihazlar": [
                cihaz.sozluk()
                for cihaz in self.yetkili_cihazlar
            ],
            "veri": dict(self.veri),
        }

    def durum_dosyasi_yolu(
        self,
    ) -> Path:
        return Path(self.durum_dosyasi)

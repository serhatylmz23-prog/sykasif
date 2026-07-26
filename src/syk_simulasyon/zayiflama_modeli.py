from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class ZayiflamaSonucu:
    toplam_yol_m: float
    ortam_kaybi_db: float
    geometrik_kayip_db: float
    toplam_kayip_db: float
    genlik_katsayisi: float
    varsayimlar: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ZayiflamaGirdisi:
    tek_yon_mesafe_m: float
    ortam_zayiflama_db_m: float
    gidis_donus: bool = True
    geometrik_yayilim: bool = False
    referans_mesafe_m: float = 1.0
    geometrik_us: float = 1.0

    def dogrula(self) -> None:
        if self.tek_yon_mesafe_m < 0:
            raise ValueError("tek_yon_mesafe_m negatif olamaz")
        if self.ortam_zayiflama_db_m < 0:
            raise ValueError("ortam_zayiflama_db_m negatif olamaz")
        if self.referans_mesafe_m <= 0:
            raise ValueError("referans_mesafe_m pozitif olmalıdır")
        if self.geometrik_us < 0:
            raise ValueError("geometrik_us negatif olamaz")


class ZayiflamaModeli:
    """Sabit dB/m ortam kaybı ve isteğe bağlı geometrik yayılım modeli.

    Bu ilk referans modelidir. Frekansa, sıcaklığa veya malzemeye bağlı gerçek
    katsayı üretmez; bu katsayıların doğrulanmış bir dış kaynaktan sağlanmasını
    bekler. Geometrik yayılım kapalıyken önceki v1.0 davranışı korunur.
    """

    def hesapla(self, girdi: ZayiflamaGirdisi) -> ZayiflamaSonucu:
        girdi.dogrula()
        toplam_yol = girdi.tek_yon_mesafe_m * (2.0 if girdi.gidis_donus else 1.0)
        ortam_kaybi = girdi.ortam_zayiflama_db_m * toplam_yol

        geometrik_kayip = 0.0
        varsayimlar = ["sabit_db_m_ortam_kaybi"]
        if girdi.gidis_donus:
            varsayimlar.append("gidis_donus_yolu")

        if girdi.geometrik_yayilim and toplam_yol > girdi.referans_mesafe_m:
            # Genlik için A ∝ (r0/r)^n; dB karşılığı 20*n*log10(r/r0).
            geometrik_kayip = 20.0 * girdi.geometrik_us * math.log10(
                toplam_yol / girdi.referans_mesafe_m
            )
            varsayimlar.append("geometrik_yayilim")

        toplam_kayip = ortam_kaybi + geometrik_kayip
        genlik_katsayisi = 10.0 ** (-toplam_kayip / 20.0)
        return ZayiflamaSonucu(
            toplam_yol_m=toplam_yol,
            ortam_kaybi_db=ortam_kaybi,
            geometrik_kayip_db=geometrik_kayip,
            toplam_kayip_db=toplam_kayip,
            genlik_katsayisi=genlik_katsayisi,
            varsayimlar=tuple(varsayimlar),
        )

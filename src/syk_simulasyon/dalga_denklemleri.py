from __future__ import annotations

import math


def db_genlik_katsayisi(zayiflama_db_m: float, toplam_yol_m: float) -> float:
    """Desibel cinsinden zayıflamayı doğrusal genlik katsayısına çevirir."""
    if zayiflama_db_m < 0 or toplam_yol_m < 0:
        raise ValueError("zayıflama ve yol negatif olamaz")
    return 10.0 ** (-(zayiflama_db_m * toplam_yol_m) / 20.0)


def gidis_donus_gecikmesi_s(derinlik_m: float, yayilim_hizi_m_s: float) -> float:
    """Düzlemsel hedef varsayımıyla gidiş-dönüş süresi."""
    if derinlik_m < 0:
        raise ValueError("derinlik negatif olamaz")
    if yayilim_hizi_m_s <= 0:
        raise ValueError("yayılım hızı pozitif olmalıdır")
    return 2.0 * derinlik_m / yayilim_hizi_m_s


def sinuz_ornegi(*, genlik: float, frekans_hz: float, zaman_s: float, faz_rad: float = 0.0) -> float:
    return genlik * math.sin(2.0 * math.pi * frekans_hz * zaman_s + faz_rad)

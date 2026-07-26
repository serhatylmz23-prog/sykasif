from __future__ import annotations

from dataclasses import dataclass

from .fizik_sabitleri import MAX_DERINLIK_M, MIN_FREKANS_HZ


@dataclass(frozen=True, slots=True)
class OrtamModeli:
    """Homojen ortam için ilk referans modeli.

    zayiflama_db_m: genlik zayıflaması, desibel/metre.
    yayilim_hizi_m_s: dalganın ortam içindeki yayılma hızı.
    """

    ortam_kimligi: str
    yayilim_hizi_m_s: float
    zayiflama_db_m: float = 0.0

    def dogrula(self) -> None:
        if not self.ortam_kimligi.strip():
            raise ValueError("ortam_kimligi boş olamaz")
        if self.yayilim_hizi_m_s <= 0:
            raise ValueError("yayilim_hizi_m_s pozitif olmalıdır")
        if self.zayiflama_db_m < 0:
            raise ValueError("zayiflama_db_m negatif olamaz")


def ortak_girdileri_dogrula(*, derinlik_m: float, frekans_hz: float, ornekleme_hz: float) -> None:
    if derinlik_m < 0 or derinlik_m > MAX_DERINLIK_M:
        raise ValueError(f"derinlik_m 0 ile {MAX_DERINLIK_M} arasında olmalıdır")
    if frekans_hz <= MIN_FREKANS_HZ:
        raise ValueError("frekans_hz pozitif olmalıdır")
    if ornekleme_hz <= 0:
        raise ValueError("ornekleme_hz pozitif olmalıdır")
    if ornekleme_hz < 2.0 * frekans_hz:
        raise ValueError("ornekleme_hz, frekansın en az iki katı olmalıdır")

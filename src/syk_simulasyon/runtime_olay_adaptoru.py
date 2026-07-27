from __future__ import annotations

from .olay_omurgasi import Olay, OlayTuru
from .ortak_dil import Katman
from .runtime_durumu import RuntimeDurumu, RuntimeDurumTuru


def runtime_durumunu_olaya_cevir(
    durum: RuntimeDurumu,
    *,
    arastirma_kimligi: str,
    deney_numarasi: str | None = None,
    kaynak: Katman = Katman.SIMULASYON,
    hedef: Katman = Katman.BILGE_KAAN,
) -> Olay:
    """Runtime durumunu olay omurgasının anlayacağı bir olaya dönüştürür."""

    if not arastirma_kimligi.strip():
        raise ValueError("Araştırma kimliği boş olamaz")

    if durum.durum == RuntimeDurumTuru.GUVENLI_DURDURULDU:
        olay_turu = OlayTuru.ACIL_DURDUR
        ozet_kodu = "RUNTIME-GUVENLI-DURDURMA"
    elif durum.durum in {
        RuntimeDurumTuru.TAMAMLANDI,
        RuntimeDurumTuru.BEKLEMEDE,
    }:
        olay_turu = OlayTuru.GOREV_SONUCU
        ozet_kodu = "RUNTIME-GOREV-SONUCU"
    else:
        olay_turu = OlayTuru.GOZLEM
        ozet_kodu = "RUNTIME-DURUM-GOZLEMI"

    gorunum = durum.gorunum()

    return Olay.olustur(
        arastirma_kimligi=arastirma_kimligi,
        deney_numarasi=deney_numarasi,
        tur=olay_turu,
        kaynak=kaynak,
        hedef=hedef,
        ozet_kodu=ozet_kodu,
        ortak_veri={
            "durum": gorunum["durum"],
            "aktif_modul": gorunum["aktif_modul"],
            "ilerleme_yuzdesi": gorunum["ilerleme_yuzdesi"],
        },
        ozel_veri={
            "runtime_gorunumu": gorunum,
        },
    )
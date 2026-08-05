"""UGR dinamik ikon durum sabitleri."""

from __future__ import annotations

from enum import StrEnum


class IkonCalismaDurumu(StrEnum):
    """Bir ikonun canlı çalışma durumları."""

    BEKLIYOR = "bekliyor"
    BASLATILIYOR = "baslatiliyor"
    CALISIYOR = "calisiyor"
    TARIYOR = "tariyor"
    VERI_AKTARIYOR = "veri_aktariyor"
    ANALIZ_EDILIYOR = "analiz_ediliyor"
    DOGRULANIYOR = "dogrulaniyor"
    SENKRONIZE_EDILIYOR = "senkronize_ediliyor"
    TAMAMLANDI = "tamamlandi"
    UYARI = "uyari"
    HATA = "hata"
    DURDURULDU = "durduruldu"
    CEVRIMDISI = "cevrimdisi"


class IkonGorunumModu(StrEnum):
    """UGR görünüm biçimleri."""

    MOD_2B = "2b"
    MOD_3B = "3b"
    MOD_AR = "ar"


class IkonOnceligi(StrEnum):
    """İkon olay önceliği."""

    DUSUK = "dusuk"
    NORMAL = "normal"
    YUKSEK = "yuksek"
    KRITIK = "kritik"


class IkonAnimasyonTuru(StrEnum):
    """Ortak dinamik animasyon aileleri."""

    SABIT = "sabit"
    NEFES = "nefes"
    DONUS = "donus"
    TARAMA = "tarama"
    VERI_AKISI = "veri_akisi"
    NABIZ = "nabiz"
    TITRESIM = "titresim"
    PARLAMA = "parlama"
    SONUMLEME = "sonumleme"


class IkonRenkRolu(StrEnum):
    """Tema bağımsız anlam renkleri."""

    NOTR = "notr"
    BILGI = "bilgi"
    ISLEM = "islem"
    BASARI = "basari"
    UYARI = "uyari"
    HATA = "hata"
    CEVRIMDISI = "cevrimdisi"

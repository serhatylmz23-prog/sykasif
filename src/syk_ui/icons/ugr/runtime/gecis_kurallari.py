"""UGR ikon geçiş güvenlik kuralları."""

from __future__ import annotations

from .durumlar import IkonCalismaDurumu


_IZINLI_GECISLER: dict[
    IkonCalismaDurumu,
    frozenset[IkonCalismaDurumu],
] = {
    IkonCalismaDurumu.BEKLIYOR: frozenset(
        {
            IkonCalismaDurumu.BASLATILIYOR,
            IkonCalismaDurumu.CEVRIMDISI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
        }
    ),
    IkonCalismaDurumu.BASLATILIYOR: frozenset(
        {
            IkonCalismaDurumu.CALISIYOR,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
        }
    ),
    IkonCalismaDurumu.CALISIYOR: frozenset(
        {
            IkonCalismaDurumu.TARIYOR,
            IkonCalismaDurumu.VERI_AKTARIYOR,
            IkonCalismaDurumu.ANALIZ_EDILIYOR,
            IkonCalismaDurumu.DOGRULANIYOR,
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
            IkonCalismaDurumu.CEVRIMDISI,
        }
    ),
    IkonCalismaDurumu.TARIYOR: frozenset(
        {
            IkonCalismaDurumu.VERI_AKTARIYOR,
            IkonCalismaDurumu.ANALIZ_EDILIYOR,
            IkonCalismaDurumu.DOGRULANIYOR,
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
        }
    ),
    IkonCalismaDurumu.VERI_AKTARIYOR: frozenset(
        {
            IkonCalismaDurumu.ANALIZ_EDILIYOR,
            IkonCalismaDurumu.DOGRULANIYOR,
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
        }
    ),
    IkonCalismaDurumu.ANALIZ_EDILIYOR: frozenset(
        {
            IkonCalismaDurumu.DOGRULANIYOR,
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
        }
    ),
    IkonCalismaDurumu.DOGRULANIYOR: frozenset(
        {
            IkonCalismaDurumu.SENKRONIZE_EDILIYOR,
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
        }
    ),
    IkonCalismaDurumu.SENKRONIZE_EDILIYOR: frozenset(
        {
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.UYARI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
        }
    ),
    IkonCalismaDurumu.TAMAMLANDI: frozenset(
        {
            IkonCalismaDurumu.BEKLIYOR,
            IkonCalismaDurumu.BASLATILIYOR,
            IkonCalismaDurumu.CEVRIMDISI,
        }
    ),
    IkonCalismaDurumu.UYARI: frozenset(
        {
            IkonCalismaDurumu.CALISIYOR,
            IkonCalismaDurumu.DOGRULANIYOR,
            IkonCalismaDurumu.TAMAMLANDI,
            IkonCalismaDurumu.HATA,
            IkonCalismaDurumu.DURDURULDU,
            IkonCalismaDurumu.CEVRIMDISI,
        }
    ),
    IkonCalismaDurumu.HATA: frozenset(
        {
            IkonCalismaDurumu.BEKLIYOR,
            IkonCalismaDurumu.BASLATILIYOR,
            IkonCalismaDurumu.DURDURULDU,
            IkonCalismaDurumu.CEVRIMDISI,
        }
    ),
    IkonCalismaDurumu.DURDURULDU: frozenset(
        {
            IkonCalismaDurumu.BEKLIYOR,
            IkonCalismaDurumu.BASLATILIYOR,
            IkonCalismaDurumu.CEVRIMDISI,
        }
    ),
    IkonCalismaDurumu.CEVRIMDISI: frozenset(
        {
            IkonCalismaDurumu.BEKLIYOR,
            IkonCalismaDurumu.BASLATILIYOR,
        }
    ),
}


def gecis_izinli_mi(
    onceki: IkonCalismaDurumu,
    yeni: IkonCalismaDurumu,
) -> bool:
    """İki durum arasındaki geçişin izinli olup olmadığını döndürür."""

    if onceki == yeni:
        return True

    return yeni in _IZINLI_GECISLER[onceki]


def izinli_hedefler(
    durum: IkonCalismaDurumu,
) -> frozenset[IkonCalismaDurumu]:
    """Belirtilen durumdan gidilebilecek hedefleri döndürür."""

    return _IZINLI_GECISLER[durum]

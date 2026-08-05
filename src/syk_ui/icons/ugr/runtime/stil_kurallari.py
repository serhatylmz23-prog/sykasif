"""UGR ikon durum stili kuralları."""

from __future__ import annotations

from .durumlar import (
    IkonAnimasyonTuru,
    IkonCalismaDurumu,
    IkonRenkRolu,
)
from .modeller import IkonDurumStili


_DURUMLAR: dict[
    IkonCalismaDurumu,
    IkonDurumStili,
] = {
    IkonCalismaDurumu.BEKLIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.BEKLIYOR,
        animasyon=IkonAnimasyonTuru.NEFES,
        renk_rolu=IkonRenkRolu.NOTR,
        animasyon_suresi_ms=2600,
        tekrarli=True,
        parlaklik=0.82,
        saydamlik=0.88,
        olcek=1.0,
    ),
    IkonCalismaDurumu.BASLATILIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.BASLATILIYOR,
        animasyon=IkonAnimasyonTuru.DONUS,
        renk_rolu=IkonRenkRolu.ISLEM,
        animasyon_suresi_ms=1200,
        tekrarli=True,
        parlaklik=1.0,
        saydamlik=1.0,
        olcek=1.0,
    ),
    IkonCalismaDurumu.CALISIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.CALISIYOR,
        animasyon=IkonAnimasyonTuru.NABIZ,
        renk_rolu=IkonRenkRolu.ISLEM,
        animasyon_suresi_ms=1800,
        tekrarli=True,
        parlaklik=1.05,
        saydamlik=1.0,
        olcek=1.02,
    ),
    IkonCalismaDurumu.TARIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.TARIYOR,
        animasyon=IkonAnimasyonTuru.TARAMA,
        renk_rolu=IkonRenkRolu.ISLEM,
        animasyon_suresi_ms=1500,
        tekrarli=True,
        parlaklik=1.1,
        saydamlik=1.0,
        olcek=1.0,
    ),
    IkonCalismaDurumu.VERI_AKTARIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.VERI_AKTARIYOR,
        animasyon=IkonAnimasyonTuru.VERI_AKISI,
        renk_rolu=IkonRenkRolu.BILGI,
        animasyon_suresi_ms=1300,
        tekrarli=True,
        parlaklik=1.08,
        saydamlik=1.0,
        olcek=1.0,
    ),
    IkonCalismaDurumu.ANALIZ_EDILIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.ANALIZ_EDILIYOR,
        animasyon=IkonAnimasyonTuru.DONUS,
        renk_rolu=IkonRenkRolu.BILGI,
        animasyon_suresi_ms=2100,
        tekrarli=True,
        parlaklik=1.12,
        saydamlik=1.0,
        olcek=1.01,
    ),
    IkonCalismaDurumu.DOGRULANIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.DOGRULANIYOR,
        animasyon=IkonAnimasyonTuru.NABIZ,
        renk_rolu=IkonRenkRolu.BILGI,
        animasyon_suresi_ms=1600,
        tekrarli=True,
        parlaklik=1.15,
        saydamlik=1.0,
        olcek=1.02,
    ),
    IkonCalismaDurumu.SENKRONIZE_EDILIYOR: IkonDurumStili(
        durum=IkonCalismaDurumu.SENKRONIZE_EDILIYOR,
        animasyon=IkonAnimasyonTuru.DONUS,
        renk_rolu=IkonRenkRolu.BILGI,
        animasyon_suresi_ms=1100,
        tekrarli=True,
        parlaklik=1.1,
        saydamlik=1.0,
        olcek=1.0,
    ),
    IkonCalismaDurumu.TAMAMLANDI: IkonDurumStili(
        durum=IkonCalismaDurumu.TAMAMLANDI,
        animasyon=IkonAnimasyonTuru.PARLAMA,
        renk_rolu=IkonRenkRolu.BASARI,
        animasyon_suresi_ms=900,
        tekrarli=False,
        parlaklik=1.2,
        saydamlik=1.0,
        olcek=1.03,
    ),
    IkonCalismaDurumu.UYARI: IkonDurumStili(
        durum=IkonCalismaDurumu.UYARI,
        animasyon=IkonAnimasyonTuru.NABIZ,
        renk_rolu=IkonRenkRolu.UYARI,
        animasyon_suresi_ms=1050,
        tekrarli=True,
        parlaklik=1.22,
        saydamlik=1.0,
        olcek=1.03,
    ),
    IkonCalismaDurumu.HATA: IkonDurumStili(
        durum=IkonCalismaDurumu.HATA,
        animasyon=IkonAnimasyonTuru.TITRESIM,
        renk_rolu=IkonRenkRolu.HATA,
        animasyon_suresi_ms=550,
        tekrarli=True,
        parlaklik=1.3,
        saydamlik=1.0,
        olcek=1.04,
    ),
    IkonCalismaDurumu.DURDURULDU: IkonDurumStili(
        durum=IkonCalismaDurumu.DURDURULDU,
        animasyon=IkonAnimasyonTuru.SONUMLEME,
        renk_rolu=IkonRenkRolu.NOTR,
        animasyon_suresi_ms=700,
        tekrarli=False,
        parlaklik=0.68,
        saydamlik=0.72,
        olcek=0.98,
    ),
    IkonCalismaDurumu.CEVRIMDISI: IkonDurumStili(
        durum=IkonCalismaDurumu.CEVRIMDISI,
        animasyon=IkonAnimasyonTuru.SABIT,
        renk_rolu=IkonRenkRolu.CEVRIMDISI,
        animasyon_suresi_ms=0,
        tekrarli=False,
        parlaklik=0.5,
        saydamlik=0.55,
        olcek=0.96,
    ),
}


def durum_stili(
    durum: IkonCalismaDurumu,
) -> IkonDurumStili:
    """Çalışma durumuna karşılık gelen stili döndürür."""

    return _DURUMLAR[durum]


def tum_durum_stilleri() -> tuple[IkonDurumStili, ...]:
    """Kayıtlı bütün durum stillerini döndürür."""

    return tuple(_DURUMLAR.values())

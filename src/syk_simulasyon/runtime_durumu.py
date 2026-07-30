from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from threading import RLock
from typing import Any

from .olay_omurgasi import Olay, OlayTuru
from .ortak_dil import Katman


class RuntimeDurumTuru(StrEnum):
    BASLATILIYOR = "başlatılıyor"
    HAZIR = "hazır"
    CALISIYOR = "çalışıyor"
    BEKLEMEDE = "beklemede"
    UYKU = "uyku"
    ONAY_BEKLIYOR = "onay_bekliyor"
    TAMAMLANDI = "tamamlandı"
    HATA = "hata"
    GUVENLI_DURDURULDU = "güvenli_durduruldu"


def _utc_zamani() -> str:
    """Saat dilimi bilgisi taşıyan UTC zaman damgası üretir."""

    return datetime.now(timezone.utc).isoformat()


@dataclass
class RuntimeDurumu:
    """SyKaşif çalışma zamanının tek ve eşzamanlı durum kaynağıdır.

    Sınıf mevcut dış sözleşmeyi korur. Terminal, FastAPI ve olay adaptörleri
    durumu değiştirmek yerine ``gorunum`` çıktısını okuyabilir.
    """

    durum: RuntimeDurumTuru = RuntimeDurumTuru.BASLATILIYOR
    aktif_katman: Katman | None = None
    aktif_modul: str | None = None
    ilerleme_yuzdesi: float = 0.0
    son_olay_kimligi: str | None = None
    son_olay_kodu: str | None = None
    son_olay_turu: OlayTuru | None = None
    guncelleme_zamani: str | None = None

    # İlerleme artık yalnızca tahmini yüzdeye bağlı kalmak zorunda değildir.
    tamamlanan_adim: int = 0
    toplam_adim: int = 0
    risk: str | None = None
    son_hata: str | None = None

    _kilit: RLock = field(
        default_factory=RLock,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        self.ilerleme_yuzdesi = self._yuzdeyi_dogrula(
            self.ilerleme_yuzdesi
        )
        self._adimlari_dogrula(
            tamamlanan_adim=self.tamamlanan_adim,
            toplam_adim=self.toplam_adim,
        )
        self.aktif_modul = self._istege_bagli_metni_temizle(
            self.aktif_modul,
            alan_adi="Aktif modül",
        )
        self.risk = self._istege_bagli_metni_temizle(
            self.risk,
            alan_adi="Risk",
        )
        self.son_hata = self._istege_bagli_metni_temizle(
            self.son_hata,
            alan_adi="Son hata",
        )

    def durum_guncelle(
        self,
        *,
        durum: RuntimeDurumTuru,
        aktif_modul: str | None = None,
        ilerleme_yuzdesi: float | None = None,
    ) -> None:
        """Durumu geriye uyumlu sözleşmeyle günceller."""

        if not isinstance(durum, RuntimeDurumTuru):
            raise TypeError("Durum, RuntimeDurumTuru türünde olmalıdır")

        with self._kilit:
            yeni_yuzde = self.ilerleme_yuzdesi
            if ilerleme_yuzdesi is not None:
                yeni_yuzde = self._yuzdeyi_dogrula(ilerleme_yuzdesi)

            if durum == RuntimeDurumTuru.TAMAMLANDI and yeni_yuzde != 100.0:
                raise ValueError(
                    "İlerleme yüzde 100 olmadan durum tamamlandı yapılamaz"
                )

            yeni_modul = self.aktif_modul
            if aktif_modul is not None:
                yeni_modul = self._zorunlu_metni_temizle(
                    aktif_modul,
                    alan_adi="Aktif modül",
                )

            self.durum = durum
            self.ilerleme_yuzdesi = yeni_yuzde
            self.aktif_modul = yeni_modul

            if durum != RuntimeDurumTuru.HATA:
                self.son_hata = None

            self.guncelleme_zamani = _utc_zamani()

    def adimlari_guncelle(
        self,
        *,
        tamamlanan_adim: int,
        toplam_adim: int,
        aktif_modul: str | None = None,
    ) -> None:
        """Ölçülebilir adım sayılarını ve bunlardan türeyen yüzdeyi kaydeder."""

        self._adimlari_dogrula(
            tamamlanan_adim=tamamlanan_adim,
            toplam_adim=toplam_adim,
        )

        with self._kilit:
            self.tamamlanan_adim = tamamlanan_adim
            self.toplam_adim = toplam_adim
            self.ilerleme_yuzdesi = (
                0.0
                if toplam_adim == 0
                else round((tamamlanan_adim / toplam_adim) * 100.0, 2)
            )

            if aktif_modul is not None:
                self.aktif_modul = self._zorunlu_metni_temizle(
                    aktif_modul,
                    alan_adi="Aktif modül",
                )

            self.guncelleme_zamani = _utc_zamani()

    def risk_guncelle(self, risk: str | None) -> None:
        """Etkin riski kaydeder; ``None`` riski temizler."""

        temiz_risk = self._istege_bagli_metni_temizle(
            risk,
            alan_adi="Risk",
        )
        with self._kilit:
            self.risk = temiz_risk
            self.guncelleme_zamani = _utc_zamani()

    def hata_kaydet(self, hata: str, *, aktif_modul: str | None = None) -> None:
        """Hata durumunu ve kullanıcıya gösterilecek Türkçe özeti kaydeder."""

        temiz_hata = self._zorunlu_metni_temizle(
            hata,
            alan_adi="Hata açıklaması",
        )
        with self._kilit:
            if aktif_modul is not None:
                self.aktif_modul = self._zorunlu_metni_temizle(
                    aktif_modul,
                    alan_adi="Aktif modül",
                )
            self.durum = RuntimeDurumTuru.HATA
            self.son_hata = temiz_hata
            self.guncelleme_zamani = _utc_zamani()

    def olaydan_guncelle(self, olay: Olay) -> None:
        """Olay omurgasından gelen olayla ortak runtime durumunu günceller."""

        if not isinstance(olay, Olay):
            raise TypeError("Olay, Olay türünde olmalıdır")

        with self._kilit:
            self.aktif_katman = olay.hedef
            self.son_olay_kimligi = olay.olay_kimligi
            self.son_olay_kodu = olay.ozet_kodu
            self.son_olay_turu = olay.tur

            if olay.tur == OlayTuru.KANIT:
                self.durum = RuntimeDurumTuru.ONAY_BEKLIYOR
            elif olay.tur == OlayTuru.ACIL_DURDUR:
                self.durum = RuntimeDurumTuru.GUVENLI_DURDURULDU
            elif olay.tur == OlayTuru.GOREV_SONUCU:
                self.durum = RuntimeDurumTuru.BEKLEMEDE
            else:
                self.durum = RuntimeDurumTuru.CALISIYOR

            if self.durum != RuntimeDurumTuru.HATA:
                self.son_hata = None
            self.guncelleme_zamani = _utc_zamani()

    def gorunum(self) -> dict[str, Any]:
        """Dış katmanlara değiştirilemeyen bir anlık görünüm sözlüğü verir."""

        with self._kilit:
            kalan_adim = max(self.toplam_adim - self.tamamlanan_adim, 0)
            return {
                "durum": self.durum.value,
                "aktif_katman": (
                    self.aktif_katman.value
                    if self.aktif_katman is not None
                    else None
                ),
                "aktif_modul": self.aktif_modul,
                "ilerleme_yuzdesi": self.ilerleme_yuzdesi,
                "tamamlanan_adim": self.tamamlanan_adim,
                "toplam_adim": self.toplam_adim,
                "kalan_adim": kalan_adim,
                "risk": self.risk,
                "son_hata": self.son_hata,
                "son_olay_kimligi": self.son_olay_kimligi,
                "son_olay_kodu": self.son_olay_kodu,
                "son_olay_turu": (
                    self.son_olay_turu.value
                    if self.son_olay_turu is not None
                    else None
                ),
                "guncelleme_zamani": self.guncelleme_zamani,
            }

    @staticmethod
    def _yuzdeyi_dogrula(yuzde: float) -> float:
        if isinstance(yuzde, bool) or not isinstance(yuzde, (int, float)):
            raise TypeError("İlerleme yüzdesi sayısal olmalıdır")

        sayisal_yuzde = float(yuzde)
        if not 0.0 <= sayisal_yuzde <= 100.0:
            raise ValueError("İlerleme yüzdesi 0 ile 100 arasında olmalıdır")
        return sayisal_yuzde

    @staticmethod
    def _adimlari_dogrula(*, tamamlanan_adim: int, toplam_adim: int) -> None:
        for alan_adi, deger in (
            ("Tamamlanan adım", tamamlanan_adim),
            ("Toplam adım", toplam_adim),
        ):
            if isinstance(deger, bool) or not isinstance(deger, int):
                raise TypeError(f"{alan_adi} tam sayı olmalıdır")
            if deger < 0:
                raise ValueError(f"{alan_adi} negatif olamaz")

        if tamamlanan_adim > toplam_adim:
            raise ValueError("Tamamlanan adım, toplam adımdan büyük olamaz")

    @staticmethod
    def _zorunlu_metni_temizle(metin: str, *, alan_adi: str) -> str:
        if not isinstance(metin, str):
            raise TypeError(f"{alan_adi} metin olmalıdır")
        temiz_metin = metin.strip()
        if not temiz_metin:
            raise ValueError(f"{alan_adi} boş olamaz")
        return temiz_metin

    @classmethod
    def _istege_bagli_metni_temizle(
        cls,
        metin: str | None,
        *,
        alan_adi: str,
    ) -> str | None:
        if metin is None:
            return None
        return cls._zorunlu_metni_temizle(metin, alan_adi=alan_adi)

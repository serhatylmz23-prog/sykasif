"""SyKaşif UGR dinamik ikon servisi."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .durum_makinesi import IkonDurumMakinesi
from .durumlar import (
    IkonCalismaDurumu,
    IkonGorunumModu,
    IkonOnceligi,
)
from .kayit_defteri import IkonRuntimeKayitDefteri
from .manifest_yukleyici import runtime_kayitlari_uret
from .modeller import IkonRuntimeKaydi
from .olay_yolu import (
    IkonRuntimeOlayYolu,
    IkonRuntimeOlayi,
)
from .stil_kurallari import durum_stili


class UgrDinamikIkonServisi:
    """UGR ikon kayıt, geçiş ve görsel durum yönetimi."""

    def __init__(
        self,
        *,
        kayit_defteri: IkonRuntimeKayitDefteri | None = None,
        durum_makinesi: IkonDurumMakinesi | None = None,
        olay_yolu: IkonRuntimeOlayYolu | None = None,
    ) -> None:
        self.kayit_defteri = (
            kayit_defteri
            or IkonRuntimeKayitDefteri()
        )
        self.durum_makinesi = (
            durum_makinesi
            or IkonDurumMakinesi()
        )
        self.olay_yolu = (
            olay_yolu
            or IkonRuntimeOlayYolu()
        )

    def manifest_yukle(
        self,
        manifest_yolu: str | Path,
    ) -> int:
        """Manifestteki ikonları kayıt defterine yükler."""

        kayitlar = runtime_kayitlari_uret(
            manifest_yolu
        )

        self.kayit_defteri.toplu_ekle(
            kayitlar
        )

        self.olay_yolu.yayinla(
            IkonRuntimeOlayi(
                olay_turu="manifest_yuklendi",
                ikon_kimligi="*",
                veri={
                    "ikon_sayisi": len(
                        kayitlar
                    ),
                    "manifest": str(
                        manifest_yolu
                    ),
                },
            )
        )

        return len(kayitlar)

    def ikon_ekle(
        self,
        kayit: IkonRuntimeKaydi,
    ) -> None:
        """Tek bir ikon kaydını ekler."""

        self.kayit_defteri.ekle(
            kayit
        )

        self.olay_yolu.yayinla(
            IkonRuntimeOlayi(
                olay_turu="ikon_eklendi",
                ikon_kimligi=(
                    kayit.ikon_kimligi
                ),
                veri=kayit.ozet(),
            )
        )

    def durum_degistir(
        self,
        ikon_kimligi: str,
        *,
        yeni_durum: IkonCalismaDurumu,
        neden: str,
        oncelik: IkonOnceligi = IkonOnceligi.NORMAL,
        ek_veri: dict[str, Any] | None = None,
        zorla: bool = False,
    ) -> dict[str, Any]:
        """Bir ikonun durumunu değiştirir."""

        kayit = self.kayit_defteri.getir(
            ikon_kimligi
        )

        degisim = self.durum_makinesi.gecis_yap(
            kayit,
            yeni_durum=yeni_durum,
            neden=neden,
            oncelik=oncelik,
            ek_veri=ek_veri,
            zorla=zorla,
        )

        stil = durum_stili(
            yeni_durum
        )

        sonuc = {
            "ikon": kayit.ozet(),
            "degisim": {
                "onceki_durum": (
                    degisim.onceki_durum.value
                ),
                "yeni_durum": (
                    degisim.yeni_durum.value
                ),
                "neden": degisim.neden,
                "oncelik": (
                    degisim.oncelik.value
                ),
                "zaman": (
                    degisim.zaman.isoformat()
                ),
                "ek_veri": dict(
                    degisim.ek_veri
                ),
            },
            "stil": {
                "animasyon": (
                    stil.animasyon.value
                ),
                "renk_rolu": (
                    stil.renk_rolu.value
                ),
                "animasyon_suresi_ms": (
                    stil.animasyon_suresi_ms
                ),
                "tekrarli": stil.tekrarli,
                "parlaklik": (
                    stil.parlaklik
                ),
                "saydamlik": (
                    stil.saydamlik
                ),
                "olcek": stil.olcek,
            },
        }

        self.olay_yolu.yayinla(
            IkonRuntimeOlayi(
                olay_turu="ikon_durumu_degisti",
                ikon_kimligi=ikon_kimligi,
                veri=sonuc,
            )
        )

        return sonuc

    def gorunum_modu_degistir(
        self,
        ikon_kimligi: str,
        gorunum_modu: IkonGorunumModu,
    ) -> dict[str, Any]:
        """İkon görünümünü 2B, 3B veya AR yapar."""

        kayit = self.kayit_defteri.getir(
            ikon_kimligi
        )

        kayit.gorunum_modu_degistir(
            gorunum_modu
        )

        sonuc = kayit.ozet()

        self.olay_yolu.yayinla(
            IkonRuntimeOlayi(
                olay_turu=(
                    "ikon_gorunum_modu_degisti"
                ),
                ikon_kimligi=ikon_kimligi,
                veri=sonuc,
            )
        )

        return sonuc

    def ikon_ozeti(
        self,
        ikon_kimligi: str,
    ) -> dict[str, Any]:
        """Tek ikonun çalışma özetini döndürür."""

        kayit = self.kayit_defteri.getir(
            ikon_kimligi
        )

        stil = durum_stili(
            kayit.durum
        )

        return {
            **kayit.ozet(),
            "stil": {
                "animasyon": (
                    stil.animasyon.value
                ),
                "renk_rolu": (
                    stil.renk_rolu.value
                ),
                "animasyon_suresi_ms": (
                    stil.animasyon_suresi_ms
                ),
                "tekrarli": stil.tekrarli,
                "parlaklik": stil.parlaklik,
                "saydamlik": stil.saydamlik,
                "olcek": stil.olcek,
            },
        }

    def durum_ozeti(self) -> dict[str, Any]:
        """Bütün dinamik ikon sisteminin özetini döndürür."""

        kayitlar = self.kayit_defteri.tumu()

        durum_sayilari = {
            durum.value: len(
                self.kayit_defteri.duruma_gore(
                    durum
                )
            )
            for durum in IkonCalismaDurumu
        }

        kategori_sayilari: dict[str, int] = {}

        for kayit in kayitlar:
            kategori_sayilari[kayit.kategori] = (
                kategori_sayilari.get(
                    kayit.kategori,
                    0,
                )
                + 1
            )

        return {
            "toplam_ikon": len(kayitlar),
            "aktif_ikon": sum(
                kayit.aktif
                for kayit in kayitlar
            ),
            "durum_sayilari": durum_sayilari,
            "kategori_sayilari": (
                kategori_sayilari
            ),
            "desteklenen_gorunumler": [
                gorunum.value
                for gorunum in IkonGorunumModu
            ],
            "kalici_kimlik_durumu": (
                "prototip_sonrasina_ertelendi"
            ),
        }

"""UGR canlı ikon Runtime 8013 köprüsü."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Any

from syk_ui.icons.ugr.runtime import (
    IkonCalismaDurumu,
    IkonGorunumModu,
    IkonOnceligi,
    UgrDinamikIkonServisi,
)
from syk_ui.icons.ugr.web import (
    UgrIkonWebRenderServisi,
)

from .runtime_8013_events import (
    UgrCanliIkonOlayi,
    UgrCanliOlayTuru,
)
from .runtime_8013_store import (
    UgrRuntime8013EventStore,
)


class UgrRuntime8013Bridge:
    """UGR ikon motorunu canlı UI Runtime 8013'e bağlar."""

    def __init__(
        self,
        *,
        ikon_servisi: UgrDinamikIkonServisi
        | None = None,
        olay_deposu: UgrRuntime8013EventStore
        | None = None,
    ) -> None:
        self.ikon_servisi = (
            ikon_servisi
            or UgrDinamikIkonServisi()
        )

        self.olay_deposu = (
            olay_deposu
            or UgrRuntime8013EventStore()
        )

        self.web_render_servisi = (
            UgrIkonWebRenderServisi(
                self.ikon_servisi
            )
        )

        self._kilit = RLock()
        self._baslatildi = False

    @property
    def baslatildi(self) -> bool:
        """Köprünün başlatılıp başlatılmadığını döndürür."""

        with self._kilit:
            return self._baslatildi

    def baslat(
        self,
        manifest_yolu: str | Path,
    ) -> dict[str, Any]:
        """215 ikonluk manifesti yükleyerek köprüyü başlatır."""

        with self._kilit:
            if self._baslatildi:
                return self.durum_ozeti()

            yuklenen = (
                self.ikon_servisi
                .manifest_yukle(
                    manifest_yolu
                )
            )

            self._baslatildi = True

            olay = UgrCanliIkonOlayi(
                olay_turu=(
                    UgrCanliOlayTuru
                    .MANIFEST_YUKLENDI
                ),
                veri={
                    "manifest_yolu": str(
                        manifest_yolu
                    ),
                    "yuklenen_ikon_sayisi": (
                        yuklenen
                    ),
                    "runtime_portu": 8013,
                },
            )

            self.olay_deposu.ekle(
                olay
            )

            return self.durum_ozeti()

    def ikon_durumu_degistir(
        self,
        ikon_kimligi: str,
        *,
        yeni_durum: IkonCalismaDurumu,
        neden: str,
        oncelik: IkonOnceligi = (
            IkonOnceligi.NORMAL
        ),
        ek_veri: dict[str, Any] | None = None,
        zorla: bool = False,
    ) -> dict[str, Any]:
        """İkon durumunu değiştirir ve canlı olay yayınlar."""

        self._baslatilmis_olmali()

        sonuc = (
            self.ikon_servisi
            .durum_degistir(
                ikon_kimligi,
                yeni_durum=yeni_durum,
                neden=neden,
                oncelik=oncelik,
                ek_veri=ek_veri,
                zorla=zorla,
            )
        )

        stil = sonuc["stil"]

        olay = UgrCanliIkonOlayi(
            olay_turu=(
                UgrCanliOlayTuru
                .IKON_DURUMU
            ),
            ikon_kimligi=ikon_kimligi,
            veri={
                "ikon_kimligi": (
                    ikon_kimligi
                ),
                "durum": (
                    sonuc["ikon"]["durum"]
                ),
                "animasyon": (
                    stil["animasyon"]
                ),
                "renk_rolu": (
                    stil["renk_rolu"]
                ),
                "animasyon_suresi_ms": (
                    stil[
                        "animasyon_suresi_ms"
                    ]
                ),
                "parlaklik": (
                    stil["parlaklik"]
                ),
                "saydamlik": (
                    stil["saydamlik"]
                ),
                "olcek": stil["olcek"],
                "neden": neden,
                "oncelik": oncelik.value,
            },
        )

        self.olay_deposu.ekle(
            olay
        )

        return {
            **sonuc,
            "canli_olay": (
                olay.json_verisi()
            ),
        }

    def ikon_gorunumu_degistir(
        self,
        ikon_kimligi: str,
        gorunum_modu: IkonGorunumModu,
    ) -> dict[str, Any]:
        """İkonun 2B, 3B veya AR görünümünü değiştirir."""

        self._baslatilmis_olmali()

        sonuc = (
            self.ikon_servisi
            .gorunum_modu_degistir(
                ikon_kimligi,
                gorunum_modu,
            )
        )

        olay = UgrCanliIkonOlayi(
            olay_turu=(
                UgrCanliOlayTuru
                .IKON_GORUNUMU
            ),
            ikon_kimligi=ikon_kimligi,
            veri={
                "ikon_kimligi": (
                    ikon_kimligi
                ),
                "gorunum_modu": (
                    gorunum_modu.value
                ),
            },
        )

        self.olay_deposu.ekle(
            olay
        )

        return {
            **sonuc,
            "canli_olay": (
                olay.json_verisi()
            ),
        }

    def ikon_aktifligi_degistir(
        self,
        ikon_kimligi: str,
        *,
        aktif: bool,
    ) -> dict[str, Any]:
        """İkonun aktif veya pasif durumunu değiştirir."""

        self._baslatilmis_olmali()

        kayit = (
            self.ikon_servisi
            .kayit_defteri
            .getir(ikon_kimligi)
        )

        kayit.aktif = bool(aktif)

        olay = UgrCanliIkonOlayi(
            olay_turu=(
                UgrCanliOlayTuru
                .IKON_AKTIFLIGI
            ),
            ikon_kimligi=ikon_kimligi,
            veri={
                "ikon_kimligi": (
                    ikon_kimligi
                ),
                "aktif": kayit.aktif,
            },
        )

        self.olay_deposu.ekle(
            olay
        )

        return {
            **kayit.ozet(),
            "canli_olay": (
                olay.json_verisi()
            ),
        }

    def toplu_durum_degistir(
        self,
        ikon_kimlikleri: list[str],
        *,
        yeni_durum: IkonCalismaDurumu,
        neden: str,
        zorla: bool = False,
    ) -> dict[str, Any]:
        """Birden fazla ikonun durumunu değiştirir."""

        self._baslatilmis_olmali()

        basarili: list[
            dict[str, Any]
        ] = []

        hatalar: list[
            dict[str, str]
        ] = []

        for ikon_kimligi in ikon_kimlikleri:
            try:
                sonuc = (
                    self.ikon_durumu_degistir(
                        ikon_kimligi,
                        yeni_durum=(
                            yeni_durum
                        ),
                        neden=neden,
                        zorla=zorla,
                    )
                )

                basarili.append(
                    {
                        "ikon_kimligi": (
                            ikon_kimligi
                        ),
                        "durum": (
                            sonuc["ikon"]["durum"]
                        ),
                    }
                )

            except Exception as hata:
                hatalar.append(
                    {
                        "ikon_kimligi": (
                            ikon_kimligi
                        ),
                        "hata": str(hata),
                    }
                )

        olay = UgrCanliIkonOlayi(
            olay_turu=(
                UgrCanliOlayTuru
                .TOPLU_GUNCELLEME
            ),
            veri={
                "istenen_ikon_sayisi": len(
                    ikon_kimlikleri
                ),
                "basarili_ikon_sayisi": len(
                    basarili
                ),
                "basarisiz_ikon_sayisi": len(
                    hatalar
                ),
                "yeni_durum": (
                    yeni_durum.value
                ),
                "basarili": basarili,
                "hatalar": hatalar,
            },
        )

        self.olay_deposu.ekle(
            olay
        )

        return olay.json_verisi()

    def ikon_render_verisi(
        self,
        ikon_kimligi: str,
    ) -> dict[str, Any]:
        """Tarayıcıya aktarılacak tek ikon verisini döndürür."""

        self._baslatilmis_olmali()

        return (
            self.web_render_servisi
            .json_uret(
                ikon_kimligi
            )
        )

    def ikon_html(
        self,
        ikon_kimligi: str,
    ) -> str:
        """Tek ikon için canlı HTML üretir."""

        self._baslatilmis_olmali()

        return (
            self.web_render_servisi
            .html_uret(
                ikon_kimligi
            )
        )

    def kategori_html(
        self,
        kategori: str,
    ) -> str:
        """Kategori ikonlarını canlı grid olarak üretir."""

        self._baslatilmis_olmali()

        return (
            self.web_render_servisi
            .kategori_html_uret(
                kategori
            )
        )

    def snapshot(self) -> dict[str, Any]:
        """Bütün ikonların tarayıcı snapshot'ını üretir."""

        self._baslatilmis_olmali()

        ikonlar = [
            self.web_render_servisi
            .json_uret(
                kayit.ikon_kimligi
            )
            for kayit in (
                self.ikon_servisi
                .kayit_defteri
                .tumu()
            )
        ]

        olay = UgrCanliIkonOlayi(
            olay_turu=(
                UgrCanliOlayTuru
                .SNAPSHOT
            ),
            veri={
                "toplam_ikon": len(
                    ikonlar
                ),
                "ikonlar": ikonlar,
            },
        )

        self.olay_deposu.ekle(
            olay
        )

        return olay.json_verisi()

    def durum_ozeti(self) -> dict[str, Any]:
        """Runtime 8013 köprü durumunu döndürür."""

        ikon_ozeti = (
            self.ikon_servisi
            .durum_ozeti()
        )

        return {
            "servis": (
                "SyKaşif UGR Runtime 8013 Bridge"
            ),
            "runtime_portu": 8013,
            "baslatildi": self.baslatildi,
            "ikon_runtime": ikon_ozeti,
            "olay_deposu": (
                self.olay_deposu
                .durum_ozeti()
            ),
            "canli_kanallar": [
                "sse",
                "snapshot",
                "http_json",
            ],
            "websocket_durumu": (
                "sonraki_adapter_asamasi"
            ),
            "kalici_ikon_kimlikleri": (
                "prototip_sonrasina_ertelendi"
            ),
        }

    def _baslatilmis_olmali(self) -> None:
        if not self.baslatildi:
            raise RuntimeError(
                "UGR Runtime 8013 köprüsü başlatılmadı."
            )

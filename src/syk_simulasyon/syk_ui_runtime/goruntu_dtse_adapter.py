from __future__ import annotations

from typing import Any

from syk_core.goruntu.goruntu_uzmani_modeli import (
    GoruntuKaydi,
    GoruntuUzmani,
)

from .dtse_attention_engine import (
    AttentionSignal,
    DTSEAttentionEngine,
    NormalizedBox,
)


class GoruntuDTSEAdapter:
    def __init__(
        self,
        *,
        uzman: GoruntuUzmani,
        dtse: DTSEAttentionEngine,
    ) -> None:
        self._uzman = uzman
        self._dtse = dtse
        self._son_sonuc: dict[str, Any] | None = None
        self._son_hata: dict[str, Any] | None = None

        self._uzman.dinleyici_ekle(
            self._olay_al
        )

    @property
    def son_sonuc(
        self,
    ) -> dict[str, Any] | None:
        return self._son_sonuc

    @property
    def son_hata(
        self,
    ) -> dict[str, Any] | None:
        return self._son_hata

    def durum(self) -> dict[str, Any]:
        return {
            "connected": True,
            "last_result": self._son_sonuc,
            "last_error": self._son_hata,
            "dtse_sequence": (
                self._dtse.sequence
            ),
        }

    def _olay_al(
        self,
        olay_turu: str,
        veri: dict[str, Any],
    ) -> None:
        if (
            olay_turu
            != "supheli_bolge_isaretlendi"
        ):
            return

        kayit = veri["kayit"]
        bolge = veri["bolge"]

        try:
            self._son_sonuc = (
                self._dtseye_aktar(
                    kayit=kayit,
                    bolge=bolge,
                )
            )

            self._son_hata = None

        except (
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            self._son_hata = {
                "veri_kimligi": (
                    kayit.veri_kimligi
                ),
                "reason": str(error),
            }

    def _dtseye_aktar(
        self,
        *,
        kayit: GoruntuKaydi,
        bolge: dict[str, Any],
    ) -> dict[str, Any]:
        kare_genisligi = (
            kayit.kare_genisligi
        )

        kare_yuksekligi = (
            kayit.kare_yuksekligi
        )

        if (
            kare_genisligi is None
            or kare_yuksekligi is None
        ):
            raise ValueError(
                "DTSE aktarımı için kare "
                "genişliği ve yüksekliği "
                "gereklidir."
            )

        if (
            kare_genisligi <= 0
            or kare_yuksekligi <= 0
        ):
            raise ValueError(
                "Kare ölçüleri geçersiz."
            )

        x = float(bolge["x"])
        y = float(bolge["y"])
        genislik = float(
            bolge["genislik"]
        )
        yukseklik = float(
            bolge["yukseklik"]
        )

        if (
            x + genislik
            > kare_genisligi
            or y + yukseklik
            > kare_yuksekligi
        ):
            raise ValueError(
                "Şüpheli bölge görüntü "
                "sınırlarının dışına taşıyor."
            )

        signal_kind = (
            bolge.get("sinyal_turu")
            or self._sinyal_turu(
                bolge.get(
                    "aciklama",
                    "",
                )
            )
        )

        signal = AttentionSignal(
            label=(
                bolge.get("aciklama")
                or "Dikkat çeken görsel alan"
            ),
            kind=signal_kind,
            confidence=float(
                bolge.get(
                    "guven",
                    75.0,
                )
            ),
            box=NormalizedBox(
                x=x / kare_genisligi,
                y=y / kare_yuksekligi,
                width=(
                    genislik
                    / kare_genisligi
                ),
                height=(
                    yukseklik
                    / kare_yuksekligi
                ),
            ),
            description=(
                "Görüntü Uzmanı tarafından "
                "işaretlenen bölge."
            ),
            metrics={
                "pixel_x": int(x),
                "pixel_y": int(y),
                "pixel_width": int(
                    genislik
                ),
                "pixel_height": int(
                    yukseklik
                ),
                "reality_status": (
                    kayit.gerceklik_durumu
                ),
            },
            evidence_refs=[
                kayit.veri_kimligi,
            ],
        )

        return self._dtse.ingest(
            media_id=kayit.veri_kimligi,
            source_kind=(
                self._kaynak_turu(
                    kayit.veri_turu
                )
            ),
            frame_index=max(
                0,
                int(kayit.kare_numarasi),
            ),
            timestamp_ms=max(
                0,
                int(kayit.zaman_ms),
            ),
            frame_width=kare_genisligi,
            frame_height=kare_yuksekligi,
            signals=[signal],
        )

    def _kaynak_turu(
        self,
        veri_turu: str,
    ) -> str:
        normalized = (
            veri_turu
            .strip()
            .casefold()
            .replace("ğ", "g")
            .replace("ı", "i")
            .replace("ş", "s")
            .replace("ö", "o")
            .replace("ü", "u")
            .replace("ç", "c")
        )

        if "video" in normalized:
            return "video"

        if (
            "canli" in normalized
            or "kamera" in normalized
            or "akis" in normalized
        ):
            return "live"

        return "image"

    def _sinyal_turu(
        self,
        aciklama: str,
    ) -> str:
        text = (
            aciklama
            .strip()
            .casefold()
            .replace("ğ", "g")
            .replace("ı", "i")
            .replace("ş", "s")
            .replace("ö", "o")
            .replace("ü", "u")
            .replace("ç", "c")
        )

        rules = (
            (
                "thermal",
                (
                    "isi",
                    "sicak",
                    "termal",
                ),
            ),
            (
                "spectral",
                (
                    "spektral",
                    "renk degisimi",
                    "yansima",
                ),
            ),
            (
                "geometry",
                (
                    "oyuk",
                    "kanal",
                    "catlak",
                    "cizgi",
                    "geometri",
                ),
            ),
            (
                "symbol",
                (
                    "sembol",
                    "isaret",
                    "yazi",
                    "motif",
                ),
            ),
            (
                "texture",
                (
                    "doku",
                    "yuzey",
                    "puruz",
                    "asinma",
                ),
            ),
            (
                "motion",
                (
                    "hareket",
                    "iz",
                    "takip",
                ),
            ),
            (
                "object",
                (
                    "nesne",
                    "heykel",
                    "metal",
                ),
            ),
        )

        for kind, words in rules:
            if any(
                word in text
                for word in words
            ):
                return kind

        return "anomaly"
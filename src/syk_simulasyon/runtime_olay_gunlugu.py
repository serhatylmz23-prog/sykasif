from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

from .olay_omurgasi import Olay, OlayTuru
from .ortak_dil import Katman


class RuntimeOlayGunluguButunlukHatasi(ValueError):
    """Runtime olay gunlugu butunluk hatasi."""


class RuntimeOlayGunlugu:
    """SHA-256 zincirli kalici runtime olay gunlugu."""

    ILK_HASH = "0" * 64
    SURUM = 1

    def __init__(self, yol: str | Path) -> None:
        self._yol = Path(yol)

    @property
    def yol(self) -> Path:
        return self._yol

    def ekle(self, olay: Olay) -> str:
        onceki_hash = self._son_hash()

        govde = {
            "surum": self.SURUM,
            "onceki_hash": onceki_hash,
            "olay": self._olayi_sozluge_cevir(olay),
        }

        kayit_hash = self._hash_uret(govde)

        kayit = {
            **govde,
            "kayit_hash": kayit_hash,
        }

        self._yol.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        satir = json.dumps(
            kayit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        with self._yol.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as dosya:
            dosya.write(satir + "\n")
            dosya.flush()
            os.fsync(dosya.fileno())

        return kayit_hash

    def olaylari_oku(self) -> tuple[Olay, ...]:
        return tuple(
            olay
            for _, olay in self._kayitlari_oku()
        )

    def butunlugu_dogrula(self) -> bool:
        self._kayitlari_oku()
        return True

    def _son_hash(self) -> str:
        kayitlar = self._kayitlari_oku()

        if not kayitlar:
            return self.ILK_HASH

        return kayitlar[-1][0]

    def _kayitlari_oku(
        self,
    ) -> list[tuple[str, Olay]]:
        if not self._yol.exists():
            return []

        onceki_hash = self.ILK_HASH
        sonuc: list[tuple[str, Olay]] = []

        with self._yol.open(
            "r",
            encoding="utf-8",
        ) as dosya:
            for sira, ham_satir in enumerate(
                dosya,
                start=1,
            ):
                satir = ham_satir.strip()

                if not satir:
                    raise RuntimeOlayGunluguButunlukHatasi(
                        f"Bos gunluk satiri: {sira}"
                    )

                try:
                    kayit = json.loads(satir)
                except json.JSONDecodeError as hata:
                    raise RuntimeOlayGunluguButunlukHatasi(
                        f"Gecersiz JSON satiri: {sira}"
                    ) from hata

                if not isinstance(kayit, dict):
                    raise RuntimeOlayGunluguButunlukHatasi(
                        f"Kayit sozluk degil: {sira}"
                    )

                govde = {
                    "surum": kayit.get("surum"),
                    "onceki_hash": kayit.get(
                        "onceki_hash"
                    ),
                    "olay": kayit.get("olay"),
                }

                kayit_hash = kayit.get("kayit_hash")

                if govde["surum"] != self.SURUM:
                    raise RuntimeOlayGunluguButunlukHatasi(
                        f"Desteklenmeyen surum: {sira}"
                    )

                if govde["onceki_hash"] != onceki_hash:
                    raise RuntimeOlayGunluguButunlukHatasi(
                        f"Hash zinciri kopuk: {sira}"
                    )

                hesaplanan = self._hash_uret(govde)

                if kayit_hash != hesaplanan:
                    raise RuntimeOlayGunluguButunlukHatasi(
                        f"Kayit hash uyusmazligi: {sira}"
                    )

                olay = self._sozlukten_olay(
                    govde["olay"],
                    sira=sira,
                )

                sonuc.append((kayit_hash, olay))
                onceki_hash = kayit_hash

        return sonuc

    @staticmethod
    def _hash_uret(govde: dict[str, Any]) -> str:
        ham = json.dumps(
            govde,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return sha256(ham).hexdigest()

    @staticmethod
    def _olayi_sozluge_cevir(
        olay: Olay,
    ) -> dict[str, Any]:
        return {
            "olay_kimligi": olay.olay_kimligi,
            "arastirma_kimligi": (
                olay.arastirma_kimligi
            ),
            "deney_numarasi": olay.deney_numarasi,
            "tur": olay.tur.value,
            "kaynak": olay.kaynak.value,
            "hedef": olay.hedef.value,
            "zaman": olay.zaman,
            "ozet_kodu": olay.ozet_kodu,
            "ortak_veri": dict(olay.ortak_veri),
            "ozel_veri": dict(olay._ozel_veri),
            "ozel_veri_sha256": olay._ozel_sha256,
        }

    @staticmethod
    def _sozlukten_olay(
        veri: object,
        *,
        sira: int,
    ) -> Olay:
        if not isinstance(veri, dict):
            raise RuntimeOlayGunluguButunlukHatasi(
                f"Olay verisi gecersiz: {sira}"
            )

        try:
            ozel_veri = veri["ozel_veri"]
            beklenen_ozel_hash = veri[
                "ozel_veri_sha256"
            ]

            if not isinstance(ozel_veri, dict):
                raise TypeError

            ozel_ham = json.dumps(
                ozel_veri,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            hesaplanan_ozel_hash = sha256(
                ozel_ham
            ).hexdigest()

            if hesaplanan_ozel_hash != (
                beklenen_ozel_hash
            ):
                raise RuntimeOlayGunluguButunlukHatasi(
                    f"Ozel veri hash uyusmazligi: {sira}"
                )

            ortak_veri = veri["ortak_veri"]

            if not isinstance(ortak_veri, dict):
                raise TypeError

            return Olay(
                olay_kimligi=str(
                    veri["olay_kimligi"]
                ),
                arastirma_kimligi=str(
                    veri["arastirma_kimligi"]
                ),
                deney_numarasi=(
                    None
                    if veri["deney_numarasi"] is None
                    else str(veri["deney_numarasi"])
                ),
                tur=OlayTuru(veri["tur"]),
                kaynak=Katman(veri["kaynak"]),
                hedef=Katman(veri["hedef"]),
                zaman=str(veri["zaman"]),
                ozet_kodu=str(veri["ozet_kodu"]),
                ortak_veri=dict(ortak_veri),
                _ozel_veri=dict(ozel_veri),
                _ozel_sha256=str(
                    beklenen_ozel_hash
                ),
            )
        except RuntimeOlayGunluguButunlukHatasi:
            raise
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as hata:
            raise RuntimeOlayGunluguButunlukHatasi(
                f"Olay alani gecersiz: {sira}"
            ) from hata

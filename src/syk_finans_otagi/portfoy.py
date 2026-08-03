from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from threading import RLock
from typing import Any

from .modeller import VarlikTuru


def _para(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.01")
    )


@dataclass(frozen=True, slots=True)
class PortfoyKaydi:
    kayit_id: str
    sembol: str
    varlik_turu: VarlikTuru
    islem_tarihi: str
    miktar: Decimal
    birim_fiyat: Decimal
    komisyon: Decimal
    kaynak: str
    kayit_sha256: str

    @property
    def toplam_tutar(self) -> Decimal:
        return _para(
            self.miktar
            * self.birim_fiyat
            + self.komisyon
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kayit_id": self.kayit_id,
            "sembol": self.sembol,
            "varlik_turu": (
                self.varlik_turu.value
            ),
            "islem_tarihi": (
                self.islem_tarihi
            ),
            "miktar": float(
                self.miktar
            ),
            "birim_fiyat": float(
                self.birim_fiyat
            ),
            "komisyon": float(
                self.komisyon
            ),
            "toplam_tutar": float(
                self.toplam_tutar
            ),
            "kaynak": self.kaynak,
            "kayit_sha256": (
                self.kayit_sha256
            ),
        }


class Portfoy:
    def __init__(self) -> None:
        self._kayitlar: list[
            PortfoyKaydi
        ] = []

        self._lock = RLock()

    def ekle(
        self,
        *,
        kayit_id: str,
        sembol: str,
        varlik_turu: VarlikTuru,
        miktar: Decimal | int | float | str,
        birim_fiyat: Decimal | int | float | str,
        islem_tarihi: str | None = None,
        komisyon: Decimal | int | float | str = 0,
        kaynak: str = "elle_giris",
    ) -> PortfoyKaydi:
        miktar_degeri = Decimal(
            str(miktar)
        )

        fiyat = _para(
            birim_fiyat
        )

        komisyon_degeri = _para(
            komisyon
        )

        if miktar_degeri <= 0:
            raise ValueError(
                "Miktar pozitif olmalıdır."
            )

        if fiyat <= 0:
            raise ValueError(
                "Birim fiyat pozitif olmalıdır."
            )

        tarih = (
            islem_tarihi
            or datetime.now(UTC).isoformat()
        )

        kanit = {
            "kayit_id": kayit_id,
            "sembol": sembol.upper(),
            "varlik_turu": (
                varlik_turu.value
            ),
            "islem_tarihi": tarih,
            "miktar": str(
                miktar_degeri
            ),
            "birim_fiyat": str(
                fiyat
            ),
            "komisyon": str(
                komisyon_degeri
            ),
            "kaynak": kaynak,
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        kayit = PortfoyKaydi(
            kayit_id=kayit_id,
            sembol=sembol.upper(),
            varlik_turu=varlik_turu,
            islem_tarihi=tarih,
            miktar=miktar_degeri,
            birim_fiyat=fiyat,
            komisyon=komisyon_degeri,
            kaynak=kaynak,
            kayit_sha256=sha256(
                kodlu
            ).hexdigest(),
        )

        with self._lock:
            self._kayitlar.append(
                kayit
            )

        return kayit

    def listele(
        self,
        *,
        sembol: str | None = None,
    ) -> list[PortfoyKaydi]:
        with self._lock:
            kayitlar = list(
                self._kayitlar
            )

        if sembol is None:
            return kayitlar

        aranan = sembol.strip().upper()

        return [
            kayit
            for kayit in kayitlar
            if kayit.sembol == aranan
        ]

    def ozet(
        self,
        sembol: str,
    ) -> dict[str, Any]:
        kayitlar = self.listele(
            sembol=sembol
        )

        toplam_miktar = sum(
            (
                kayit.miktar
                for kayit in kayitlar
            ),
            Decimal("0"),
        )

        toplam_maliyet = sum(
            (
                kayit.toplam_tutar
                for kayit in kayitlar
            ),
            Decimal("0.00"),
        )

        ortalama = (
            _para(
                toplam_maliyet
                / toplam_miktar
            )
            if toplam_miktar > 0
            else None
        )

        return {
            "sembol": sembol.upper(),
            "kayit_sayisi": len(
                kayitlar
            ),
            "toplam_miktar": float(
                toplam_miktar
            ),
            "toplam_maliyet": float(
                _para(toplam_maliyet)
            ),
            "ortalama_maliyet": (
                float(ortalama)
                if ortalama is not None
                else None
            ),
            "ilk_islem_tarihi": (
                min(
                    kayit.islem_tarihi
                    for kayit in kayitlar
                )
                if kayitlar
                else None
            ),
            "son_islem_tarihi": (
                max(
                    kayit.islem_tarihi
                    for kayit in kayitlar
                )
                if kayitlar
                else None
            ),
        }
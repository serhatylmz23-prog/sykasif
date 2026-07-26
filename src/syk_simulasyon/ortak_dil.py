from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import secrets
from typing import Any, Mapping


class Katman(str, Enum):
    SIMULASYON = "K01"
    GORSEL = "K02"
    KONUM = "K03"
    SENSOR = "K04"
    ANALIZ = "K05"
    BILGE_KAAN = "K90"
    KURUCU_KAAN = "K99"


class IletiTuru(str, Enum):
    GOZLEM = "I01"
    ONERI = "I02"
    KANIT = "I03"
    KARAR_TALEBI = "I04"
    KARAR = "I05"


@dataclass(frozen=True)
class KatmanYetkisi:
    katman: Katman
    alabilecegi_turler: frozenset[IletiTuru]
    gorebilecegi_alanlar: frozenset[str] = frozenset({"ileti_kimligi", "arastirma_kimligi", "tur", "kaynak_katman", "zaman", "ozet_kodu", "guven"})


@dataclass(frozen=True)
class OrtakIleti:
    ileti_kimligi: str
    arastirma_kimligi: str
    tur: IletiTuru
    kaynak_katman: Katman
    hedef_katman: Katman
    zaman: str
    ozet_kodu: str
    guven: float
    icerik_ozeti: str
    _ozel_icerik: Mapping[str, Any] = field(repr=False)
    _icerik_sha256: str = field(repr=False)

    @staticmethod
    def olustur(*, arastirma_kimligi: str, tur: IletiTuru, kaynak_katman: Katman,
                hedef_katman: Katman, ozet_kodu: str, guven: float,
                icerik_ozeti: str, ozel_icerik: Mapping[str, Any]) -> "OrtakIleti":
        if not 0 <= guven <= 1:
            raise ValueError("guven 0 ile 1 arasında olmalıdır")
        ham = json.dumps(ozel_icerik, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return OrtakIleti(
            ileti_kimligi="IL-" + secrets.token_hex(8).upper(),
            arastirma_kimligi=arastirma_kimligi,
            tur=tur,
            kaynak_katman=kaynak_katman,
            hedef_katman=hedef_katman,
            zaman=datetime.now(timezone.utc).isoformat(),
            ozet_kodu=ozet_kodu,
            guven=guven,
            icerik_ozeti=icerik_ozeti,
            _ozel_icerik=dict(ozel_icerik),
            _icerik_sha256=hashlib.sha256(ham).hexdigest(),
        )

    def ortak_gorunum(self, yetki: KatmanYetkisi) -> dict[str, Any]:
        if self.hedef_katman != yetki.katman:
            raise PermissionError("ileti bu katmana yöneltilmemiştir")
        if self.tur not in yetki.alabilecegi_turler:
            raise PermissionError("ileti türü bu katmana kapalıdır")
        tum = {
            "ileti_kimligi": self.ileti_kimligi,
            "arastirma_kimligi": self.arastirma_kimligi,
            "tur": self.tur.value,
            "kaynak_katman": self.kaynak_katman.value,
            "hedef_katman": self.hedef_katman.value,
            "zaman": self.zaman,
            "ozet_kodu": self.ozet_kodu,
            "guven": self.guven,
            "icerik_ozeti": self.icerik_ozeti,
            "icerik_sha256": self._icerik_sha256,
        }
        return {k: v for k, v in tum.items() if k in yetki.gorebilecegi_alanlar}

    def ozel_icerigi_ac(self, yetki: KatmanYetkisi) -> Mapping[str, Any]:
        if yetki.katman not in {self.kaynak_katman, self.hedef_katman, Katman.BILGE_KAAN}:
            raise PermissionError("katman özel içeriği göremez")
        return dict(self._ozel_icerik)

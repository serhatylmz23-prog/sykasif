from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
import secrets
from typing import Any, Mapping

from .ortak_dil import Katman


class OlayTuru(StrEnum):
    GOZLEM = "O01"
    OLCUM = "O02"
    ONERI = "O03"
    KANIT = "O04"
    GOREV_ISTEGI = "O05"
    GOREV_SONUCU = "O06"
    ACIL_DURDUR = "O90"


class GorevDurumu(StrEnum):
    TASLAK = "taslak"
    BILGE_KAAN_INCELEMESI = "bilge_kaan_incelemesi"
    ONAYLANDI = "onaylandi"
    REDDEDILDI = "reddedildi"
    CALISIYOR = "calisiyor"
    TAMAMLANDI = "tamamlandi"
    DURDURULDU = "durduruldu"


@dataclass(frozen=True)
class KatmanKapisi:
    katman: Katman
    alabilecegi_olaylar: frozenset[OlayTuru]
    yayimlayabilecegi_olaylar: frozenset[OlayTuru]


@dataclass(frozen=True)
class Olay:
    olay_kimligi: str
    arastirma_kimligi: str
    deney_numarasi: str | None
    tur: OlayTuru
    kaynak: Katman
    hedef: Katman
    zaman: str
    ozet_kodu: str
    ortak_veri: Mapping[str, Any]
    _ozel_veri: Mapping[str, Any] = field(repr=False)
    _ozel_sha256: str = field(repr=False)

    @staticmethod
    def olustur(*, arastirma_kimligi: str, deney_numarasi: str | None,
                tur: OlayTuru, kaynak: Katman, hedef: Katman,
                ozet_kodu: str, ortak_veri: Mapping[str, Any],
                ozel_veri: Mapping[str, Any]) -> "Olay":
        ham = json.dumps(ozel_veri, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
        return Olay(
            olay_kimligi="OK-" + secrets.token_hex(8).upper(),
            arastirma_kimligi=arastirma_kimligi,
            deney_numarasi=deney_numarasi,
            tur=tur,
            kaynak=kaynak,
            hedef=hedef,
            zaman=datetime.now(timezone.utc).isoformat(),
            ozet_kodu=ozet_kodu,
            ortak_veri=dict(ortak_veri),
            _ozel_veri=dict(ozel_veri),
            _ozel_sha256=hashlib.sha256(ham).hexdigest(),
        )

    def ortak_gorunum(self) -> dict[str, Any]:
        return {
            "olay_kimligi": self.olay_kimligi,
            "arastirma_kimligi": self.arastirma_kimligi,
            "deney_numarasi": self.deney_numarasi,
            "tur": self.tur.value,
            "kaynak": self.kaynak.value,
            "hedef": self.hedef.value,
            "zaman": self.zaman,
            "ozet_kodu": self.ozet_kodu,
            "ortak_veri": dict(self.ortak_veri),
            "ozel_veri_sha256": self._ozel_sha256,
        }


@dataclass
class BilgeKaanDenetimliOlayOmurgasi:
    kapilar: dict[Katman, KatmanKapisi]
    olaylar: list[Olay] = field(default_factory=list)
    denetim_kaydi: list[dict[str, Any]] = field(default_factory=list)

    def yayinla(self, olay: Olay, *, bilge_kaan_onayi: bool) -> str:
        kaynak_kapisi = self.kapilar.get(olay.kaynak)
        hedef_kapisi = self.kapilar.get(olay.hedef)
        if kaynak_kapisi is None or hedef_kapisi is None:
            raise PermissionError("kaynak veya hedef katman kapısı tanımsızdır")
        if olay.tur not in kaynak_kapisi.yayimlayabilecegi_olaylar:
            raise PermissionError("kaynak katman bu olay türünü yayımlayamaz")
        if olay.tur not in hedef_kapisi.alabilecegi_olaylar:
            raise PermissionError("hedef katman bu olay türünü alamaz")
        if not bilge_kaan_onayi:
            raise PermissionError("Bilge Kaan denetimi olmadan olay yayımlanamaz")
        self.olaylar.append(olay)
        self.denetim_kaydi.append({
            "olay_kimligi": olay.olay_kimligi,
            "karar": "yayinlandi",
            "denetleyen": "Bilge Kaan",
            "zaman": datetime.now(timezone.utc).isoformat(),
        })
        return olay.olay_kimligi

    def oku(self, olay_kimligi: str, isteyen: Katman) -> dict[str, Any]:
        olay = next((x for x in self.olaylar if x.olay_kimligi == olay_kimligi), None)
        if olay is None:
            raise KeyError("olay bulunamadı")
        if isteyen not in {olay.hedef, Katman.BILGE_KAAN}:
            raise PermissionError("katman kendisine yöneltilmeyen olayı göremez")
        return olay.ortak_gorunum()

    def ozel_veriyi_ac(self, olay_kimligi: str, isteyen: Katman) -> Mapping[str, Any]:
        olay = next((x for x in self.olaylar if x.olay_kimligi == olay_kimligi), None)
        if olay is None:
            raise KeyError("olay bulunamadı")
        if isteyen != Katman.BILGE_KAAN:
            raise PermissionError("özel analiz verisini yalnız Bilge Kaan görebilir")
        return dict(olay._ozel_veri)


@dataclass
class Gorev:
    gorev_kimligi: str
    arastirma_kimligi: str
    deney_numarasi: str | None
    amac_kodu: str
    hedef_katman: Katman
    durum: GorevDurumu = GorevDurumu.TASLAK
    geri_alma_plani: str | None = None
    gecmis: list[dict[str, str]] = field(default_factory=list)

    def bilge_kaan_incele(self, onay: bool, gerekce: str) -> None:
        self.durum = GorevDurumu.ONAYLANDI if onay else GorevDurumu.REDDEDILDI
        self.gecmis.append({"aktor": "Bilge Kaan", "karar": self.durum.value, "gerekce": gerekce})

    def baslat(self) -> None:
        if self.durum != GorevDurumu.ONAYLANDI:
            raise PermissionError("Bilge Kaan onayı olmadan görev başlatılamaz")
        self.durum = GorevDurumu.CALISIYOR

    def geri_al(self, *, bilge_kaan_onayi: bool, kurucu_kaan_onayi: bool) -> None:
        if not self.geri_alma_plani:
            raise ValueError("geri alma planı yok")
        if not (bilge_kaan_onayi and kurucu_kaan_onayi):
            raise PermissionError("geri alma için Bilge Kaan ve Kurucu Kaan onayı gerekir")
        self.durum = GorevDurumu.DURDURULDU
        self.gecmis.append({"aktor": "Bilge Kaan + Kurucu Kaan", "karar": "geri_alindi", "gerekce": self.geri_alma_plani})


def yeni_gorev(*, arastirma_kimligi: str, deney_numarasi: str | None,
               amac_kodu: str, hedef_katman: Katman,
               geri_alma_plani: str | None = None) -> Gorev:
    return Gorev(
        gorev_kimligi="GR-" + secrets.token_hex(8).upper(),
        arastirma_kimligi=arastirma_kimligi,
        deney_numarasi=deney_numarasi,
        amac_kodu=amac_kodu,
        hedef_katman=hedef_katman,
        geri_alma_plani=geri_alma_plani,
    )

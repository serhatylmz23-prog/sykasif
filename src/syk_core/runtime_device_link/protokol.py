"""SyKaşif cihazlar arası iletişim protokolü."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class ProtokolHatasi(RuntimeError):
    """Cihaz iletişim protokolü hatası."""


class MesajTuru(str, Enum):
    CANLILIK = "canlılık"
    CANLILIK_YANITI = "canlılık_yanıtı"
    DURUM_ISTEGI = "durum_isteği"
    DURUM_YANITI = "durum_yanıtı"
    KOMUT = "komut"
    KOMUT_SONUCU = "komut_sonucu"
    VERI = "veri"
    BILDIRIM = "bildirim"
    BAGLANTI_KAPATMA = "bağlantı_kapatma"
    HATA = "hata"


class MesajDurumu(str, Enum):
    OLUSTURULDU = "oluşturuldu"
    IMZALANDI = "imzalandı"
    GONDERILDI = "gönderildi"
    ALINDI = "alındı"
    DOGRULANDI = "doğrulandı"
    ISLENDI = "işlendi"
    REDDEDILDI = "reddedildi"
    HATA = "hata"


@dataclass(slots=True)
class CihazMesaji:
    mesaj_kimligi: str
    kaynak_cihaz_kimligi: str
    hedef_cihaz_kimligi: str
    mesaj_turu: MesajTuru
    sira_numarasi: int
    olusturulma_zamani: datetime
    gecerlilik_suresi_saniye: int = 60
    icerik: dict[str, Any] = field(default_factory=dict)
    oturum_kimligi: str | None = None
    benzersiz_deger: str | None = None
    imza: str | None = None
    durum: MesajDurumu = MesajDurumu.OLUSTURULDU
    hata: str | None = None

    def __post_init__(self) -> None:
        if not self.mesaj_kimligi.strip():
            raise ValueError(
                "Mesaj kimliği boş olamaz."
            )

        if not self.kaynak_cihaz_kimligi.strip():
            raise ValueError(
                "Kaynak cihaz kimliği boş olamaz."
            )

        if not self.hedef_cihaz_kimligi.strip():
            raise ValueError(
                "Hedef cihaz kimliği boş olamaz."
            )

        if self.sira_numarasi <= 0:
            raise ValueError(
                "Sıra numarası sıfırdan büyük olmalıdır."
            )

        if self.gecerlilik_suresi_saniye <= 0:
            raise ValueError(
                "Geçerlilik süresi sıfırdan büyük olmalıdır."
            )

        if self.olusturulma_zamani.tzinfo is None:
            raise ValueError(
                "Mesaj zamanı saat dilimi içermelidir."
            )

    @classmethod
    def olustur(
        cls,
        *,
        kaynak_cihaz_kimligi: str,
        hedef_cihaz_kimligi: str,
        mesaj_turu: MesajTuru,
        sira_numarasi: int,
        icerik: dict[str, Any] | None = None,
        oturum_kimligi: str | None = None,
        olusturulma_zamani: datetime | None = None,
        gecerlilik_suresi_saniye: int = 60,
    ) -> "CihazMesaji":
        return cls(
            mesaj_kimligi=(
                "SYK-CIHAZ-MESAJ-"
                + uuid4().hex.upper()
            ),
            kaynak_cihaz_kimligi=(
                kaynak_cihaz_kimligi
            ),
            hedef_cihaz_kimligi=(
                hedef_cihaz_kimligi
            ),
            mesaj_turu=mesaj_turu,
            sira_numarasi=sira_numarasi,
            olusturulma_zamani=(
                olusturulma_zamani
                or datetime.now(UTC)
            ),
            gecerlilik_suresi_saniye=(
                gecerlilik_suresi_saniye
            ),
            icerik=dict(icerik or {}),
            oturum_kimligi=oturum_kimligi,
            benzersiz_deger=uuid4().hex,
        )

    def imza_icerigi(self) -> bytes:
        veri = {
            "mesaj_kimliği": self.mesaj_kimligi,
            "kaynak_cihaz_kimliği": (
                self.kaynak_cihaz_kimligi
            ),
            "hedef_cihaz_kimliği": (
                self.hedef_cihaz_kimligi
            ),
            "mesaj_türü": self.mesaj_turu.value,
            "sıra_numarası": self.sira_numarasi,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "geçerlilik_süresi_saniye": (
                self.gecerlilik_suresi_saniye
            ),
            "içerik": self.icerik,
            "oturum_kimliği": self.oturum_kimligi,
            "benzersiz_değer": self.benzersiz_deger,
        }

        return json.dumps(
            veri,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

    def imzala(
        self,
        gizli_anahtar: str,
    ) -> str:
        if not gizli_anahtar:
            raise ProtokolHatasi(
                "Mesaj imzalama anahtarı boş olamaz."
            )

        self.imza = hmac.new(
            gizli_anahtar.encode("utf-8"),
            self.imza_icerigi(),
            hashlib.sha256,
        ).hexdigest()

        self.durum = MesajDurumu.IMZALANDI

        return self.imza

    def imzayi_dogrula(
        self,
        gizli_anahtar: str,
    ) -> bool:
        if not self.imza:
            return False

        beklenen = hmac.new(
            gizli_anahtar.encode("utf-8"),
            self.imza_icerigi(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            self.imza,
            beklenen,
        )

    def sozluk(self) -> dict[str, Any]:
        return {
            "mesaj_kimliği": self.mesaj_kimligi,
            "kaynak_cihaz_kimliği": (
                self.kaynak_cihaz_kimligi
            ),
            "hedef_cihaz_kimliği": (
                self.hedef_cihaz_kimligi
            ),
            "mesaj_türü": self.mesaj_turu.value,
            "sıra_numarası": self.sira_numarasi,
            "oluşturulma_zamanı": (
                self.olusturulma_zamani.isoformat()
            ),
            "geçerlilik_süresi_saniye": (
                self.gecerlilik_suresi_saniye
            ),
            "içerik": dict(self.icerik),
            "oturum_kimliği": self.oturum_kimligi,
            "benzersiz_değer": self.benzersiz_deger,
            "imza": self.imza,
            "durum": self.durum.value,
            "hata": self.hata,
        }

    def json_olustur(self) -> str:
        return json.dumps(
            self.sozluk(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def sozlukten_olustur(
        cls,
        veri: dict[str, Any],
    ) -> "CihazMesaji":
        try:
            return cls(
                mesaj_kimligi=str(
                    veri["mesaj_kimliği"]
                ),
                kaynak_cihaz_kimligi=str(
                    veri["kaynak_cihaz_kimliği"]
                ),
                hedef_cihaz_kimligi=str(
                    veri["hedef_cihaz_kimliği"]
                ),
                mesaj_turu=MesajTuru(
                    veri["mesaj_türü"]
                ),
                sira_numarasi=int(
                    veri["sıra_numarası"]
                ),
                olusturulma_zamani=(
                    datetime.fromisoformat(
                        str(
                            veri[
                                "oluşturulma_zamanı"
                            ]
                        )
                    )
                ),
                gecerlilik_suresi_saniye=int(
                    veri[
                        "geçerlilik_süresi_saniye"
                    ]
                ),
                icerik=dict(
                    veri.get("içerik", {})
                ),
                oturum_kimligi=veri.get(
                    "oturum_kimliği"
                ),
                benzersiz_deger=veri.get(
                    "benzersiz_değer"
                ),
                imza=veri.get("imza"),
                durum=MesajDurumu(
                    veri.get(
                        "durum",
                        MesajDurumu.OLUSTURULDU.value,
                    )
                ),
                hata=veri.get("hata"),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as hata:
            raise ProtokolHatasi(
                "Cihaz mesajı çözümlenemedi."
            ) from hata

    @classmethod
    def json_coz(
        cls,
        ham_veri: str,
    ) -> "CihazMesaji":
        try:
            veri = json.loads(
                ham_veri
            )
        except json.JSONDecodeError as hata:
            raise ProtokolHatasi(
                "Cihaz mesajı geçerli JSON değil."
            ) from hata

        if not isinstance(veri, dict):
            raise ProtokolHatasi(
                "Cihaz mesajı nesne yapısında olmalıdır."
            )

        return cls.sozlukten_olustur(
            veri
        )

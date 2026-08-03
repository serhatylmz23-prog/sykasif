from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable

from .modeller import (
    VeriGuncelligi,
)
from .portfoy_analizi import (
    Kanit,
    VarlikAdayi,
)


def _sinirla(
    deger: float,
    alt: float = 0.0,
    ust: float = 100.0,
) -> float:
    return round(
        min(
            ust,
            max(
                alt,
                float(deger),
            ),
        ),
        3,
    )


@dataclass(frozen=True, slots=True)
class IncelemeBolumu:
    bolum_id: str
    baslik: str
    kisa_ozet: str
    ayrintili_aciklama: str
    kanitlar: tuple[Kanit, ...]
    goruntuleme_turu: str = "metin"
    varsayilan_acik: bool = False

    @property
    def kanit_sayisi(self) -> int:
        return len(
            self.kanitlar
        )

    @property
    def bolum_kanit_gucu(self) -> float:
        if not self.kanitlar:
            return 0.0

        toplam_agirlik = sum(
            abs(
                kanit.agirlik
            )
            for kanit in self.kanitlar
        )

        if toplam_agirlik <= 0:
            return 0.0

        puan = sum(
            kanit.deger
            * abs(
                kanit.agirlik
            )
            for kanit in self.kanitlar
        ) / toplam_agirlik

        kaynak_sayisi = len(
            {
                kanit.kaynak
                for kanit in self.kanitlar
                if kanit.kaynak.strip()
            }
        )

        kaynak_destegi = min(
            20.0,
            kaynak_sayisi * 4.0,
        )

        return _sinirla(
            puan * 0.80
            + kaynak_destegi
        )

    def as_dict(
        self,
        *,
        ayrintili: bool,
    ) -> dict[str, Any]:
        veri = {
            "bolum_id": self.bolum_id,
            "baslik": self.baslik,
            "kisa_ozet": self.kisa_ozet,
            "goruntuleme_turu": (
                self.goruntuleme_turu
            ),
            "varsayilan_acik": (
                self.varsayilan_acik
            ),
            "kanit_sayisi": (
                self.kanit_sayisi
            ),
            "kanit_gucu": (
                self.bolum_kanit_gucu
            ),
        }

        if ayrintili:
            veri[
                "ayrintili_aciklama"
            ] = self.ayrintili_aciklama

            veri["kanitlar"] = [
                kanit.as_dict()
                for kanit in self.kanitlar
            ]

        return veri


@dataclass(frozen=True, slots=True)
class PiyasaDavranisi:
    hacim_puani: float
    emir_yogunlugu_puani: float
    toplama_olasiligi: float
    dagitma_olasiligi: float
    baskilama_olasiligi: float
    sahte_kirilim_riski: float
    likidite_puani: float
    oynaklik_puani: float
    aciklama: str

    @property
    def davranis_guveni(self) -> float:
        tutarlilik = (
            _sinirla(
                self.hacim_puani
            )
            + _sinirla(
                self.emir_yogunlugu_puani
            )
            + _sinirla(
                self.likidite_puani
            )
        ) / 3.0

        belirsizlik = (
            _sinirla(
                self.sahte_kirilim_riski
            )
            + _sinirla(
                self.oynaklik_puani
            )
        ) / 2.0

        return _sinirla(
            tutarlilik * 0.70
            + (
                100.0
                - belirsizlik
            )
            * 0.30
        )

    @property
    def baskin_davranis(self) -> str:
        olasiliklar = {
            "toplama": (
                self.toplama_olasiligi
            ),
            "dagitma": (
                self.dagitma_olasiligi
            ),
            "baskilama": (
                self.baskilama_olasiligi
            ),
        }

        davranis, puan = max(
            olasiliklar.items(),
            key=lambda oge: oge[1],
        )

        if puan < 55:
            return "belirsiz"

        return davranis

    def as_dict(self) -> dict[str, Any]:
        return {
            "hacim_puani": _sinirla(
                self.hacim_puani
            ),
            "emir_yogunlugu_puani": (
                _sinirla(
                    self.emir_yogunlugu_puani
                )
            ),
            "toplama_olasiligi": (
                _sinirla(
                    self.toplama_olasiligi
                )
            ),
            "dagitma_olasiligi": (
                _sinirla(
                    self.dagitma_olasiligi
                )
            ),
            "baskilama_olasiligi": (
                _sinirla(
                    self.baskilama_olasiligi
                )
            ),
            "sahte_kirilim_riski": (
                _sinirla(
                    self.sahte_kirilim_riski
                )
            ),
            "likidite_puani": _sinirla(
                self.likidite_puani
            ),
            "oynaklik_puani": _sinirla(
                self.oynaklik_puani
            ),
            "davranis_guveni": (
                self.davranis_guveni
            ),
            "baskin_davranis": (
                self.baskin_davranis
            ),
            "aciklama": self.aciklama,
            "uyari": (
                "Bu bölüm piyasa davranışı "
                "olasılığıdır; kesin kişi veya "
                "kurum tespiti değildir."
            ),
        }


@dataclass(frozen=True, slots=True)
class KasifFinansYorumu:
    kisa_yorum: str
    ayrintili_yorum: str
    olumlu_kanitlar: tuple[str, ...]
    riskler: tuple[str, ...]
    izlenecek_kosullar: tuple[str, ...]
    guven_endeksi: float
    kanit_gucu: float
    karar_durumu: str

    def as_dict(
        self,
        *,
        ayrintili: bool,
    ) -> dict[str, Any]:
        veri = {
            "kisa_yorum": (
                self.kisa_yorum
            ),
            "guven_endeksi": (
                _sinirla(
                    self.guven_endeksi
                )
            ),
            "kanit_gucu": (
                _sinirla(
                    self.kanit_gucu
                )
            ),
            "karar_durumu": (
                self.karar_durumu
            ),
            "karar_yetkisi": (
                "Nihai karar kullanıcıya aittir."
            ),
        }

        if ayrintili:
            veri.update(
                {
                    "ayrintili_yorum": (
                        self.ayrintili_yorum
                    ),
                    "olumlu_kanitlar": list(
                        self.olumlu_kanitlar
                    ),
                    "riskler": list(
                        self.riskler
                    ),
                    "izlenecek_kosullar": list(
                        self.izlenecek_kosullar
                    ),
                }
            )

        return veri


@dataclass(frozen=True, slots=True)
class VarlikIncelemeRaporu:
    sembol: str
    aday: VarlikAdayi
    bolumler: tuple[
        IncelemeBolumu,
        ...
    ]
    piyasa_davranisi: PiyasaDavranisi
    kasif_yorumu: KasifFinansYorumu
    veri_guncelligi: VeriGuncelligi
    rapor_sha256: str

    def kisa_gorunum(
        self,
    ) -> dict[str, Any]:
        return {
            "sembol": self.sembol,
            "mevcut_fiyat": (
                self.aday.mevcut_fiyat
            ),
            "risk_puani": (
                self.aday.risk_puani
            ),
            "guven_endeksi": (
                self.aday.guven_endeksi
            ),
            "kanit_gucu": (
                self.aday.kanit_gucu
            ),
            "karar": self.aday.karar,
            "kisa_yorum": (
                self.kasif_yorumu
                .kisa_yorum
            ),
            "piyasa_davranisi": {
                "baskin_davranis": (
                    self.piyasa_davranisi
                    .baskin_davranis
                ),
                "davranis_guveni": (
                    self.piyasa_davranisi
                    .davranis_guveni
                ),
            },
            "bolumler": [
                bolum.as_dict(
                    ayrintili=False
                )
                for bolum in self.bolumler
            ],
            "veri_guncelligi": (
                self.veri_guncelligi
                .as_dict()
            ),
            "ayrinti_mevcut": True,
            "rapor_sha256": (
                self.rapor_sha256
            ),
        }

    def ayrintili_gorunum(
        self,
        *,
        secilen_bolumler: (
            Iterable[str] | None
        ) = None,
    ) -> dict[str, Any]:
        secimler = (
            {
                str(bolum).strip()
                for bolum
                in secilen_bolumler
            }
            if secilen_bolumler
            is not None
            else None
        )

        bolumler = [
            bolum
            for bolum in self.bolumler
            if (
                secimler is None
                or bolum.bolum_id
                in secimler
            )
        ]

        return {
            "sembol": self.sembol,
            "aday": self.aday.as_dict(),
            "bolumler": [
                bolum.as_dict(
                    ayrintili=True
                )
                for bolum in bolumler
            ],
            "piyasa_davranisi": (
                self.piyasa_davranisi
                .as_dict()
            ),
            "kasif_yorumu": (
                self.kasif_yorumu
                .as_dict(
                    ayrintili=True
                )
            ),
            "veri_guncelligi": (
                self.veri_guncelligi
                .as_dict()
            ),
            "rapor_sha256": (
                self.rapor_sha256
            ),
        }


class VarlikIncelemeMotoru:
    GECERLI_BOLUMLER = {
        "grafik",
        "kap",
        "mali_tablolar",
        "fon_yabanci",
        "piyasa_davranisi",
        "uzmanlar",
        "makaleler",
        "videolar",
        "sektor",
        "makro",
    }

    @classmethod
    def olustur(
        cls,
        *,
        aday: VarlikAdayi,
        bolumler: Iterable[
            IncelemeBolumu
        ],
        piyasa_davranisi: (
            PiyasaDavranisi
        ),
        veri_guncelligi: (
            VeriGuncelligi
        ),
    ) -> VarlikIncelemeRaporu:
        bolum_listesi = tuple(
            bolumler
        )

        if not bolum_listesi:
            raise ValueError(
                "En az bir inceleme bölümü "
                "bulunmalıdır."
            )

        bolum_kimlikleri = [
            bolum.bolum_id
            for bolum in bolum_listesi
        ]

        if len(
            set(
                bolum_kimlikleri
            )
        ) != len(
            bolum_kimlikleri
        ):
            raise ValueError(
                "Aynı inceleme bölümü "
                "birden fazla eklenemez."
            )

        gecersiz = sorted(
            set(
                bolum_kimlikleri
            )
            - cls.GECERLI_BOLUMLER
        )

        if gecersiz:
            raise ValueError(
                "Geçersiz inceleme bölümleri: "
                + ", ".join(
                    gecersiz
                )
            )

        olumlu = tuple(
            kanit.baslik
            for kanit in aday.kanitlar
            if kanit.olumlu
        )

        riskler = tuple(
            kanit.baslik
            for kanit in aday.kanitlar
            if not kanit.olumlu
        )

        if (
            piyasa_davranisi
            .sahte_kirilim_riski
            >= 60
        ):
            riskler = (
                *riskler,
                "Sahte kırılım riski yüksek",
            )

        if aday.risk_puani >= 65:
            riskler = (
                *riskler,
                "Genel risk puanı yüksek",
            )

        if aday.karar == "olumlu_aday":
            kisa_yorum = (
                "Kanıtlar olumlu yönde "
                "ağırlık kazanıyor; kademeli "
                "plan değerlendirilebilir."
            )
        elif aday.karar == "izle":
            kisa_yorum = (
                "Görünüm izlemeye değer; "
                "yeni kanıtlarla doğrulanmalı."
            )
        elif aday.karar == "yuksek_risk":
            kisa_yorum = (
                "Getiri ihtimaline karşın "
                "risk seviyesi belirgin."
            )
        else:
            kisa_yorum = (
                "Mevcut veriler ortak ve güçlü "
                "bir yön oluşturmuyor."
            )

        ayrintili_yorum = (
            f"{aday.sembol} için Güven Endeksi "
            f"{aday.guven_endeksi:.1f}, "
            f"Kanıt Gücü {aday.kanit_gucu:.1f} "
            f"ve risk puanı "
            f"{aday.risk_puani:.1f} olarak "
            "hesaplandı. Değerlendirme kesin "
            "hüküm değil, mevcut kanıtların "
            "ağırlıklı sonucudur."
        )

        yorum = KasifFinansYorumu(
            kisa_yorum=kisa_yorum,
            ayrintili_yorum=(
                ayrintili_yorum
            ),
            olumlu_kanitlar=olumlu,
            riskler=riskler,
            izlenecek_kosullar=(
                "Yeni KAP açıklamaları",
                "Hacim ve kademe değişimi",
                "Fon ve yabancı akışı",
                "Sektör ve endeks etkisi",
            ),
            guven_endeksi=(
                aday.guven_endeksi
            ),
            kanit_gucu=(
                aday.kanit_gucu
            ),
            karar_durumu=aday.karar,
        )

        kanit = {
            "sembol": aday.sembol,
            "guven_endeksi": (
                aday.guven_endeksi
            ),
            "kanit_gucu": (
                aday.kanit_gucu
            ),
            "risk_puani": (
                aday.risk_puani
            ),
            "bolumler": [
                {
                    "bolum_id": (
                        bolum.bolum_id
                    ),
                    "kanit_gucu": (
                        bolum.bolum_kanit_gucu
                    ),
                }
                for bolum
                in bolum_listesi
            ],
            "piyasa_davranisi": (
                piyasa_davranisi
                .as_dict()
            ),
            "veri_guncelligi": (
                veri_guncelligi
                .as_dict()
            ),
        }

        kodlu = json.dumps(
            kanit,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return VarlikIncelemeRaporu(
            sembol=(
                aday.sembol
                .strip()
                .upper()
            ),
            aday=aday,
            bolumler=bolum_listesi,
            piyasa_davranisi=(
                piyasa_davranisi
            ),
            kasif_yorumu=yorum,
            veri_guncelligi=(
                veri_guncelligi
            ),
            rapor_sha256=sha256(
                kodlu
            ).hexdigest(),
        )
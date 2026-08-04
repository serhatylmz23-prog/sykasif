from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from threading import RLock
from typing import Any, Mapping

from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel, Field


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _muhur(
    veri: Mapping[str, Any],
) -> str:
    kodlu = json.dumps(
        dict(veri),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return sha256(
        kodlu
    ).hexdigest()


finans_router = APIRouter(
    prefix="/syfinans",
    tags=["SyFinansOtağı"],
)


SEKMELER = (
    "piyasa",
    "kasam",
    "analiz",
    "planlar",
)


@dataclass(frozen=True, slots=True)
class KaynakRuntimeDurumu:
    kaynak_id: str
    baslik: str
    durum: str
    veri_akis_durumu: str
    aciklama: str
    üretim_baglantisi: bool

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "kaynak_id": self.kaynak_id,
            "baslik": self.baslik,
            "durum": self.durum,
            "veri_akis_durumu": (
                self.veri_akis_durumu
            ),
            "aciklama": self.aciklama,
            "uretim_baglantisi": (
                self.üretim_baglantisi
            ),
        }


class AlarmKuyrukIstegi(BaseModel):
    alarm_id: str = Field(
        min_length=1,
        max_length=120,
    )

    alarm_turu: str = Field(
        min_length=1,
        max_length=80,
    )

    sembol: str = Field(
        min_length=1,
        max_length=40,
    )

    baslik: str = Field(
        min_length=1,
        max_length=200,
    )

    mesaj: str = Field(
        min_length=1,
        max_length=2000,
    )

    onem: str = Field(
        default="bilgi",
        max_length=30,
    )


class SyFinansRuntimeServisi:
    def __init__(
        self,
        *,
        alarm_kapasitesi: int = 250,
    ) -> None:
        if alarm_kapasitesi <= 0:
            raise ValueError(
                "Alarm kapasitesi pozitif olmalıdır."
            )

        self._alarmlar: deque[
            dict[str, Any]
        ] = deque(
            maxlen=alarm_kapasitesi
        )

        self._alarm_kimlikleri: set[
            str
        ] = set()

        self._lock = RLock()

    @staticmethod
    def kaynak_durumlari(
    ) -> tuple[
        KaynakRuntimeDurumu,
        ...
    ]:
        return (
            KaynakRuntimeDurumu(
                kaynak_id="tcmb",
                baslik="TCMB Döviz",
                durum="hazir",
                veri_akis_durumu=(
                    "canli_baglanti_dogrulandi"
                ),
                aciklama=(
                    "TCMB gösterge kuru bağlantısı "
                    "doğrulandı. Gösterge kuru doğrudan "
                    "işlem fiyatı değildir."
                ),
                üretim_baglantisi=True,
            ),
            KaynakRuntimeDurumu(
                kaynak_id="kap",
                baslik="KAP Bildirimleri",
                durum="hazir",
                veri_akis_durumu=(
                    "bagdastirici_hazir"
                ),
                aciklama=(
                    "KAP bildirim çözümleme ve önem "
                    "sınıflandırma katmanı hazır."
                ),
                üretim_baglantisi=False,
            ),
            KaynakRuntimeDurumu(
                kaynak_id="bist",
                baslik="BIST Piyasa",
                durum="beklemede",
                veri_akis_durumu=(
                    "lisansli_saglayici_bekleniyor"
                ),
                aciklama=(
                    "Ortak fiyat, alış, satış, hacim ve "
                    "gecikme sözleşmesi hazır. Lisanslı "
                    "üretim sağlayıcısı bekleniyor."
                ),
                üretim_baglantisi=False,
            ),
            KaynakRuntimeDurumu(
                kaynak_id="tefas",
                baslik="TEFAS Fonlar",
                durum="beklemede",
                veri_akis_durumu=(
                    "izinli_veri_adresi_bekleniyor"
                ),
                aciklama=(
                    "Fon veri modeli ve güvenli çalışma "
                    "katmanı hazır. Belgelenmiş ve izinli "
                    "üretim veri adresi bekleniyor."
                ),
                üretim_baglantisi=False,
            ),
        )

    @staticmethod
    def cihaz_profilleri(
    ) -> tuple[
        dict[str, Any],
        ...
    ]:
        return (
            {
                "profil_id": "iphone",
                "cihaz_turu": "telefon",
                "hedef_genislik": 390,
                "yerlesim": "tek_sutun",
                "menu": "alt_sekme",
                "grafik_yuksekligi": 260,
                "kart_sutunu": 1,
                "dokunmatik": True,
            },
            {
                "profil_id": (
                    "samsung_tab_a_2019_8"
                ),
                "cihaz_turu": "tablet",
                "hedef_genislik": 800,
                "yerlesim": "uyarlanabilir_iki_sutun",
                "menu": "yan_veya_alt_sekme",
                "grafik_yuksekligi": 320,
                "kart_sutunu": 2,
                "dokunmatik": True,
            },
            {
                "profil_id": "masaustu",
                "cihaz_turu": "masaustu",
                "hedef_genislik": 1440,
                "yerlesim": "coklu_panel",
                "menu": "yan_menu",
                "grafik_yuksekligi": 420,
                "kart_sutunu": 4,
                "dokunmatik": False,
            },
        )

    @staticmethod
    def sekme_sozlesmesi(
        sekme: str,
    ) -> dict[str, Any]:
        sekme_degeri = (
            str(sekme)
            .strip()
            .casefold()
        )

        if sekme_degeri not in SEKMELER:
            raise KeyError(
                f"Finans sekmesi bulunamadı: {sekme}"
            )

        ortak = {
            "anlik_veri_satiri": True,
            "kaynak_durumu": True,
            "gecikme_aciklamasi": True,
            "kanit_sha256": True,
            "kesinlik_uyarisi": (
                "Veriler karar desteğidir; "
                "nihai karar kullanıcıya aittir."
            ),
        }

        icerikler = {
            "piyasa": {
                "baslik": "Piyasa",
                "bolumler": (
                    "BIST",
                    "Fonlar",
                    "Döviz",
                    "Altın",
                    "Gümüş",
                ),
                "bilesenler": (
                    "fiyat_karti",
                    "alis_satis",
                    "hacim",
                    "degisim",
                    "grafik",
                    "kaynak_sagligi",
                ),
            },
            "kasam": {
                "baslik": "Kasam",
                "bolumler": (
                    "Hisselerim",
                    "Fonlarım",
                    "Dövizlerim",
                    "Kıymetli madenlerim",
                ),
                "bilesenler": (
                    "miktar",
                    "ortalama_maliyet",
                    "guncel_deger",
                    "kar_zarar",
                    "dunu_bugunu",
                    "maliyet_cizgisi",
                ),
            },
            "analiz": {
                "baslik": "Analiz",
                "bolumler": (
                    "Kanıt Gücü",
                    "Güven Endeksi",
                    "Risk",
                    "Adaylar",
                    "Piyasa davranışı",
                ),
                "bilesenler": (
                    "kisa_ozet",
                    "detayli_inceleme",
                    "kap_etkisi",
                    "trend",
                    "kaynak_karsilastirma",
                    "kasif_yorumu",
                ),
            },
            "planlar": {
                "baslik": "Planlar",
                "bolumler": (
                    "Bütçe dağılımı",
                    "Kademeli alım",
                    "Kademeli satım",
                    "Gerçekleşme ve maliyet",
                ),
                "bilesenler": (
                    "serbest_secim",
                    "kullanici_secimi",
                    "kademe_tablosu",
                    "gerceklesti_secimi",
                    "ortalama_maliyet",
                    "basari_orani",
                ),
            },
        }

        veri = {
            "sekme": sekme_degeri,
            **icerikler[
                sekme_degeri
            ],
            **ortak,
        }

        return {
            **veri,
            "sozlesme_sha256": _muhur(
                veri
            ),
        }

    def alarm_ekle(
        self,
        istek: AlarmKuyrukIstegi,
    ) -> dict[str, Any]:
        alarm_id = (
            istek.alarm_id
            .strip()
        )

        with self._lock:
            if alarm_id in (
                self._alarm_kimlikleri
            ):
                return {
                    "durum": "tekrar_engellendi",
                    "alarm_id": alarm_id,
                    "kuyruk_boyutu": len(
                        self._alarmlar
                    ),
                }

            zaman = _simdi()

            kayit_temeli = {
                "alarm_id": alarm_id,
                "alarm_turu": (
                    istek.alarm_turu
                ),
                "sembol": (
                    istek.sembol
                    .strip()
                    .upper()
                ),
                "baslik": istek.baslik,
                "mesaj": istek.mesaj,
                "onem": istek.onem,
                "olusma_zamani": zaman,
                "durum": "bekliyor",
            }

            kayit = {
                **kayit_temeli,
                "alarm_sha256": _muhur(
                    kayit_temeli
                ),
            }

            self._alarmlar.append(
                kayit
            )

            self._alarm_kimlikleri.add(
                alarm_id
            )

            return {
                "durum": "kuyruga_alindi",
                "alarm": kayit,
                "kuyruk_boyutu": len(
                    self._alarmlar
                ),
            }

    def alarm_listesi(
        self,
    ) -> tuple[
        dict[str, Any],
        ...
    ]:
        with self._lock:
            return tuple(
                reversed(
                    tuple(
                        self._alarmlar
                    )
                )
            )

    def runtime_snapshot(
        self,
    ) -> dict[str, Any]:
        kaynaklar = tuple(
            kaynak.as_dict()
            for kaynak
            in self.kaynak_durumlari()
        )

        hazir = sum(
            kaynak["durum"] == "hazir"
            for kaynak in kaynaklar
        )

        beklemede = sum(
            kaynak["durum"] == "beklemede"
            for kaynak in kaynaklar
        )

        snapshot_temeli = {
            "schema": (
                "syfinans-runtime/v1"
            ),
            "modul": "SyFinansOtağı",
            "durum": "prototip_hazir",
            "karar_yetkisi": "kullanici",
            "otomatik_al_sat": False,
            "sekmeler": list(
                SEKMELER
            ),
            "kaynaklar": list(
                kaynaklar
            ),
            "hazir_kaynak_sayisi": hazir,
            "bekleyen_kaynak_sayisi": (
                beklemede
            ),
            "alarm_kuyrugu_boyutu": len(
                self.alarm_listesi()
            ),
            "cihaz_profilleri": list(
                self.cihaz_profilleri()
            ),
            "uretilme_zamani": _simdi(),
        }

        return {
            **snapshot_temeli,
            "snapshot_sha256": _muhur(
                snapshot_temeli
            ),
        }


_servis = SyFinansRuntimeServisi()


@finans_router.get(
    "/runtime",
)
def get_syfinans_runtime(
) -> dict[str, Any]:
    return _servis.runtime_snapshot()


@finans_router.get(
    "/kaynaklar",
)
def get_syfinans_kaynaklari(
) -> dict[str, Any]:
    kaynaklar = [
        kaynak.as_dict()
        for kaynak
        in _servis.kaynak_durumlari()
    ]

    veri = {
        "schema": (
            "syfinans-kaynak-durumlari/v1"
        ),
        "kaynaklar": kaynaklar,
    }

    return {
        **veri,
        "kaynaklar_sha256": _muhur(
            veri
        ),
    }


@finans_router.get(
    "/sekmeler/{sekme}",
)
def get_syfinans_sekmesi(
    sekme: str,
) -> dict[str, Any]:
    try:
        return (
            _servis
            .sekme_sozlesmesi(
                sekme
            )
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@finans_router.get(
    "/cihaz-profilleri",
)
def get_syfinans_cihaz_profilleri(
) -> dict[str, Any]:
    profiller = list(
        _servis.cihaz_profilleri()
    )

    veri = {
        "schema": (
            "syfinans-cihaz-profilleri/v1"
        ),
        "profiller": profiller,
    }

    return {
        **veri,
        "profiller_sha256": _muhur(
            veri
        ),
    }


@finans_router.get(
    "/alarmlar",
)
def get_syfinans_alarmlari(
) -> dict[str, Any]:
    alarmlar = list(
        _servis.alarm_listesi()
    )

    veri = {
        "schema": (
            "syfinans-alarm-kuyrugu/v1"
        ),
        "alarmlar": alarmlar,
        "alarm_sayisi": len(
            alarmlar
        ),
    }

    return {
        **veri,
        "kuyruk_sha256": _muhur(
            veri
        ),
    }


@finans_router.post(
    "/alarmlar",
)
def post_syfinans_alarmi(
    istek: AlarmKuyrukIstegi,
) -> dict[str, Any]:
    return _servis.alarm_ekle(
        istek
    )
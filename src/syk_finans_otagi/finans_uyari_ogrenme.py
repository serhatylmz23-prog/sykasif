from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from typing import Any, Iterable, Mapping


def _simdi() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def _ondalik(
    deger: Decimal | int | float | str,
) -> Decimal:
    return Decimal(
        str(deger)
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


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


class AlarmTuru(StrEnum):
    FIYAT = "fiyat"
    KADEME = "kademe"
    KAP = "kap"
    KAYNAK_KESINTISI = "kaynak_kesintisi"
    RISK = "risk"


class AlarmOnemi(StrEnum):
    BILGI = "bilgi"
    DIKKAT = "dikkat"
    ONEMLI = "onemli"
    KRITIK = "kritik"


class AlarmYonelimi(StrEnum):
    YUKARI = "yukari"
    ASAGI = "asagi"
    ESIT = "esit"


class OneriSonucu(StrEnum):
    BEKLIYOR = "bekliyor"
    BASARILI = "basarili"
    BASARISIZ = "basarisiz"
    KISMEN_BASARILI = "kismen_basarili"
    IPTAL = "iptal"


class ArastirmaOnceligi(StrEnum):
    DUSUK = "dusuk"
    ORTA = "orta"
    YUKSEK = "yuksek"
    KRITIK = "kritik"


@dataclass(frozen=True, slots=True)
class AlarmKurali:
    alarm_id: str
    alarm_turu: AlarmTuru
    sembol: str
    hedef_deger: Decimal | None = None
    yonelim: AlarmYonelimi | None = None
    tekrar_bekleme_saniyesi: int = 300
    etkin: bool = True
    aciklama: str = ""

    def __post_init__(self) -> None:
        if not self.alarm_id.strip():
            raise ValueError(
                "Alarm kimliği boş olamaz."
            )

        if not self.sembol.strip():
            raise ValueError(
                "Alarm sembolü boş olamaz."
            )

        if self.tekrar_bekleme_saniyesi < 0:
            raise ValueError(
                "Tekrar bekleme süresi negatif olamaz."
            )

        if (
            self.alarm_turu
            in {
                AlarmTuru.FIYAT,
                AlarmTuru.KADEME,
                AlarmTuru.RISK,
            }
            and self.hedef_deger is None
        ):
            raise ValueError(
                "Bu alarm türü için hedef değer gereklidir."
            )


@dataclass(frozen=True, slots=True)
class AlarmOlayi:
    olay_id: str
    alarm_id: str
    alarm_turu: AlarmTuru
    sembol: str
    onem: AlarmOnemi
    baslik: str
    mesaj: str
    olusma_zamani: str
    guncel_deger: Decimal | None
    hedef_deger: Decimal | None
    kanit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "olay_id": self.olay_id,
            "alarm_id": self.alarm_id,
            "alarm_turu": (
                self.alarm_turu.value
            ),
            "sembol": self.sembol,
            "onem": self.onem.value,
            "baslik": self.baslik,
            "mesaj": self.mesaj,
            "olusma_zamani": (
                self.olusma_zamani
            ),
            "guncel_deger": (
                float(self.guncel_deger)
                if self.guncel_deger
                is not None
                else None
            ),
            "hedef_deger": (
                float(self.hedef_deger)
                if self.hedef_deger
                is not None
                else None
            ),
            "kanit_sha256": (
                self.kanit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class KararBasariKaydi:
    karar_id: str
    sembol: str
    karar_turu: str
    baslangic_fiyati: Decimal
    hedef_fiyat: Decimal | None
    baslangic_zamani: str
    bitis_zamani: str | None
    sonuc_fiyati: Decimal | None
    sonuc: OneriSonucu
    getiri_orani: float | None
    kanit_puani: float
    guven_puani: float
    kayit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "karar_id": self.karar_id,
            "sembol": self.sembol,
            "karar_turu": self.karar_turu,
            "baslangic_fiyati": float(
                self.baslangic_fiyati
            ),
            "hedef_fiyat": (
                float(self.hedef_fiyat)
                if self.hedef_fiyat
                is not None
                else None
            ),
            "baslangic_zamani": (
                self.baslangic_zamani
            ),
            "bitis_zamani": (
                self.bitis_zamani
            ),
            "sonuc_fiyati": (
                float(self.sonuc_fiyati)
                if self.sonuc_fiyati
                is not None
                else None
            ),
            "sonuc": self.sonuc.value,
            "getiri_orani": (
                self.getiri_orani
            ),
            "kanit_puani": (
                self.kanit_puani
            ),
            "guven_puani": (
                self.guven_puani
            ),
            "kayit_sha256": (
                self.kayit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class KaynakOgrenmeKaydi:
    saglayici_id: str
    toplam_istek: int
    basarili_istek: int
    hatali_istek: int
    tutarli_veri: int
    tutarsiz_veri: int
    onceki_guven_puani: float
    yeni_guven_puani: float
    aciklama: str
    kayit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "saglayici_id": (
                self.saglayici_id
            ),
            "toplam_istek": (
                self.toplam_istek
            ),
            "basarili_istek": (
                self.basarili_istek
            ),
            "hatali_istek": (
                self.hatali_istek
            ),
            "tutarli_veri": (
                self.tutarli_veri
            ),
            "tutarsiz_veri": (
                self.tutarsiz_veri
            ),
            "onceki_guven_puani": (
                self.onceki_guven_puani
            ),
            "yeni_guven_puani": (
                self.yeni_guven_puani
            ),
            "aciklama": self.aciklama,
            "kayit_sha256": (
                self.kayit_sha256
            ),
        }


@dataclass(frozen=True, slots=True)
class ArastirmaOnerisi:
    oneri_id: str
    baslik: str
    kategori: str
    oncelik: ArastirmaOnceligi
    gerekce: str
    beklenen_fayda: str
    kanitlar: tuple[str, ...]
    otomatik_uygulanabilir: bool
    kullanici_onayi_gerekli: bool
    oneri_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "oneri_id": self.oneri_id,
            "baslik": self.baslik,
            "kategori": self.kategori,
            "oncelik": self.oncelik.value,
            "gerekce": self.gerekce,
            "beklenen_fayda": (
                self.beklenen_fayda
            ),
            "kanitlar": list(
                self.kanitlar
            ),
            "otomatik_uygulanabilir": (
                self.otomatik_uygulanabilir
            ),
            "kullanici_onayi_gerekli": (
                self.kullanici_onayi_gerekli
            ),
            "oneri_sha256": (
                self.oneri_sha256
            ),
        }


class AlarmTekrarEngelleyici:
    def __init__(
        self,
        *,
        dosya_yolu: str | Path | None = None,
    ) -> None:
        self.dosya_yolu = (
            Path(dosya_yolu)
            if dosya_yolu is not None
            else None
        )

        self._son_gonderimler: dict[
            str,
            str,
        ] = {}

        self._lock = RLock()

        if (
            self.dosya_yolu is not None
            and self.dosya_yolu.is_file()
        ):
            yuklenen = json.loads(
                self.dosya_yolu.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(
                yuklenen,
                Mapping,
            ):
                self._son_gonderimler = {
                    str(anahtar): str(deger)
                    for anahtar, deger
                    in yuklenen.items()
                }

    def gonderilebilir_mi(
        self,
        *,
        alarm_id: str,
        tekrar_bekleme_saniyesi: int,
        simdi: str | None = None,
    ) -> bool:
        zaman = datetime.fromisoformat(
            simdi or _simdi()
        )

        with self._lock:
            onceki = self._son_gonderimler.get(
                alarm_id
            )

        if onceki is None:
            return True

        onceki_zaman = datetime.fromisoformat(
            onceki
        )

        return (
            zaman - onceki_zaman
        ) >= timedelta(
            seconds=tekrar_bekleme_saniyesi
        )

    def gonderildi_kaydet(
        self,
        *,
        alarm_id: str,
        zaman: str | None = None,
    ) -> None:
        kayit_zamani = zaman or _simdi()

        with self._lock:
            self._son_gonderimler[
                alarm_id
            ] = kayit_zamani

            if self.dosya_yolu is not None:
                self.dosya_yolu.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                self.dosya_yolu.write_text(
                    json.dumps(
                        self._son_gonderimler,
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )


class SyFinansAlarmMotoru:
    def __init__(
        self,
        *,
        tekrar_engelleyici: (
            AlarmTekrarEngelleyici | None
        ) = None,
    ) -> None:
        self.tekrar_engelleyici = (
            tekrar_engelleyici
            or AlarmTekrarEngelleyici()
        )

    @staticmethod
    def _esik_asildi(
        *,
        guncel: Decimal,
        hedef: Decimal,
        yonelim: AlarmYonelimi,
    ) -> bool:
        if yonelim == AlarmYonelimi.YUKARI:
            return guncel >= hedef

        if yonelim == AlarmYonelimi.ASAGI:
            return guncel <= hedef

        return guncel == hedef

    def fiyat_alarm_degerlendir(
        self,
        *,
        kural: AlarmKurali,
        guncel_fiyat: (
            Decimal | int | float | str
        ),
        zaman: str | None = None,
    ) -> AlarmOlayi | None:
        if not kural.etkin:
            return None

        if kural.alarm_turu not in {
            AlarmTuru.FIYAT,
            AlarmTuru.KADEME,
        }:
            raise ValueError(
                "Kural fiyat alarmı değildir."
            )

        if (
            kural.hedef_deger is None
            or kural.yonelim is None
        ):
            raise ValueError(
                "Fiyat alarmında hedef ve yönelim gereklidir."
            )

        guncel = _ondalik(
            guncel_fiyat
        )

        hedef = _ondalik(
            kural.hedef_deger
        )

        if not self._esik_asildi(
            guncel=guncel,
            hedef=hedef,
            yonelim=kural.yonelim,
        ):
            return None

        olay_zamani = zaman or _simdi()

        if not (
            self.tekrar_engelleyici
            .gonderilebilir_mi(
                alarm_id=kural.alarm_id,
                tekrar_bekleme_saniyesi=(
                    kural
                    .tekrar_bekleme_saniyesi
                ),
                simdi=olay_zamani,
            )
        ):
            return None

        onem = (
            AlarmOnemi.ONEMLI
            if kural.alarm_turu
            == AlarmTuru.KADEME
            else AlarmOnemi.DIKKAT
        )

        baslik = (
            "Kademe fiyatına ulaşıldı"
            if kural.alarm_turu
            == AlarmTuru.KADEME
            else "Fiyat alarmı gerçekleşti"
        )

        mesaj = (
            f"{kural.sembol.upper()} "
            f"{guncel} fiyatına ulaştı. "
            f"İzlenen hedef: {hedef}."
        )

        kanit = {
            "alarm_id": kural.alarm_id,
            "sembol": kural.sembol.upper(),
            "alarm_turu": (
                kural.alarm_turu.value
            ),
            "guncel": str(guncel),
            "hedef": str(hedef),
            "yonelim": (
                kural.yonelim.value
            ),
            "zaman": olay_zamani,
        }

        olay = AlarmOlayi(
            olay_id=(
                f"{kural.alarm_id}:"
                f"{olay_zamani}"
            ),
            alarm_id=kural.alarm_id,
            alarm_turu=(
                kural.alarm_turu
            ),
            sembol=(
                kural.sembol.upper()
            ),
            onem=onem,
            baslik=baslik,
            mesaj=mesaj,
            olusma_zamani=(
                olay_zamani
            ),
            guncel_deger=guncel,
            hedef_deger=hedef,
            kanit_sha256=_muhur(
                kanit
            ),
        )

        self.tekrar_engelleyici.gonderildi_kaydet(
            alarm_id=kural.alarm_id,
            zaman=olay_zamani,
        )

        return olay

    def kap_alarm_degerlendir(
        self,
        *,
        bildirim_id: str,
        sembol: str,
        baslik: str,
        onem: str,
        bildirim_sha256: str,
        zaman: str | None = None,
    ) -> AlarmOlayi | None:
        onem_degeri = str(
            onem
        ).strip().casefold()

        if onem_degeri not in {
            "kritik",
            "onemli",
            "önemli",
        }:
            return None

        alarm_id = (
            f"KAP:{bildirim_id}"
        )

        olay_zamani = zaman or _simdi()

        if not (
            self.tekrar_engelleyici
            .gonderilebilir_mi(
                alarm_id=alarm_id,
                tekrar_bekleme_saniyesi=(
                    86400
                ),
                simdi=olay_zamani,
            )
        ):
            return None

        kanit = {
            "bildirim_id": bildirim_id,
            "sembol": sembol.upper(),
            "baslik": baslik,
            "onem": onem_degeri,
            "bildirim_sha256": (
                bildirim_sha256
            ),
        }

        olay = AlarmOlayi(
            olay_id=(
                f"{alarm_id}:"
                f"{olay_zamani}"
            ),
            alarm_id=alarm_id,
            alarm_turu=AlarmTuru.KAP,
            sembol=sembol.upper(),
            onem=(
                AlarmOnemi.KRITIK
                if onem_degeri == "kritik"
                else AlarmOnemi.ONEMLI
            ),
            baslik=(
                "Önemli KAP bildirimi"
            ),
            mesaj=baslik,
            olusma_zamani=(
                olay_zamani
            ),
            guncel_deger=None,
            hedef_deger=None,
            kanit_sha256=_muhur(
                kanit
            ),
        )

        self.tekrar_engelleyici.gonderildi_kaydet(
            alarm_id=alarm_id,
            zaman=olay_zamani,
        )

        return olay

    def kaynak_kesinti_alarm_degerlendir(
        self,
        *,
        saglayici_id: str,
        durum: str,
        son_hata: str | None,
        zaman: str | None = None,
    ) -> AlarmOlayi | None:
        if durum not in {
            "erisilemiyor",
            "cevrimdisi",
        }:
            return None

        alarm_id = (
            f"KAYNAK:{saglayici_id}"
        )

        olay_zamani = zaman or _simdi()

        if not (
            self.tekrar_engelleyici
            .gonderilebilir_mi(
                alarm_id=alarm_id,
                tekrar_bekleme_saniyesi=600,
                simdi=olay_zamani,
            )
        ):
            return None

        kanit = {
            "saglayici_id": (
                saglayici_id
            ),
            "durum": durum,
            "son_hata": son_hata,
            "zaman": olay_zamani,
        }

        olay = AlarmOlayi(
            olay_id=(
                f"{alarm_id}:"
                f"{olay_zamani}"
            ),
            alarm_id=alarm_id,
            alarm_turu=(
                AlarmTuru.KAYNAK_KESINTISI
            ),
            sembol=saglayici_id,
            onem=AlarmOnemi.ONEMLI,
            baslik=(
                "Finans veri kaynağı kesintisi"
            ),
            mesaj=(
                f"{saglayici_id} kaynağına "
                "erişilemiyor. Son güvenilir "
                "veri kullanılabilir."
            ),
            olusma_zamani=(
                olay_zamani
            ),
            guncel_deger=None,
            hedef_deger=None,
            kanit_sha256=_muhur(
                kanit
            ),
        )

        self.tekrar_engelleyici.gonderildi_kaydet(
            alarm_id=alarm_id,
            zaman=olay_zamani,
        )

        return olay


class KararBasariMotoru:
    def karar_ac(
        self,
        *,
        karar_id: str,
        sembol: str,
        karar_turu: str,
        baslangic_fiyati: (
            Decimal | int | float | str
        ),
        hedef_fiyat: (
            Decimal | int | float | str | None
        ),
        kanit_puani: float,
        guven_puani: float,
        zaman: str | None = None,
    ) -> KararBasariKaydi:
        if not karar_id.strip():
            raise ValueError(
                "Karar kimliği boş olamaz."
            )

        baslangic = _ondalik(
            baslangic_fiyati
        )

        hedef = (
            _ondalik(hedef_fiyat)
            if hedef_fiyat is not None
            else None
        )

        kanit = {
            "karar_id": karar_id,
            "sembol": sembol.upper(),
            "karar_turu": karar_turu,
            "baslangic_fiyati": (
                str(baslangic)
            ),
            "hedef_fiyat": (
                str(hedef)
                if hedef is not None
                else None
            ),
            "kanit_puani": kanit_puani,
            "guven_puani": guven_puani,
        }

        return KararBasariKaydi(
            karar_id=karar_id,
            sembol=sembol.upper(),
            karar_turu=karar_turu,
            baslangic_fiyati=(
                baslangic
            ),
            hedef_fiyat=hedef,
            baslangic_zamani=(
                zaman or _simdi()
            ),
            bitis_zamani=None,
            sonuc_fiyati=None,
            sonuc=OneriSonucu.BEKLIYOR,
            getiri_orani=None,
            kanit_puani=float(
                kanit_puani
            ),
            guven_puani=float(
                guven_puani
            ),
            kayit_sha256=_muhur(
                kanit
            ),
        )

    def karar_kapat(
        self,
        *,
        kayit: KararBasariKaydi,
        sonuc_fiyati: (
            Decimal | int | float | str
        ),
        basari_esigi_yuzde: float = 0.0,
        zaman: str | None = None,
    ) -> KararBasariKaydi:
        sonuc_fiyat = _ondalik(
            sonuc_fiyati
        )

        getiri = round(
            float(
                (
                    sonuc_fiyat
                    - kayit.baslangic_fiyati
                )
                / kayit.baslangic_fiyati
                * Decimal("100")
            ),
            3,
        )

        if kayit.karar_turu in {
            "alim",
            "guclu_aday",
            "izle",
        }:
            basarili = (
                getiri
                >= float(
                    basari_esigi_yuzde
                )
            )
        else:
            basarili = (
                getiri
                <= -float(
                    basari_esigi_yuzde
                )
            )

        if basarili:
            sonuc = OneriSonucu.BASARILI
        elif abs(getiri) < 0.5:
            sonuc = (
                OneriSonucu
                .KISMEN_BASARILI
            )
        else:
            sonuc = (
                OneriSonucu.BASARISIZ
            )

        kanit = {
            **kayit.as_dict(),
            "sonuc_fiyati": str(
                sonuc_fiyat
            ),
            "getiri_orani": getiri,
            "sonuc": sonuc.value,
        }

        return replace(
            kayit,
            bitis_zamani=(
                zaman or _simdi()
            ),
            sonuc_fiyati=(
                sonuc_fiyat
            ),
            sonuc=sonuc,
            getiri_orani=getiri,
            kayit_sha256=_muhur(
                kanit
            ),
        )

    @staticmethod
    def basari_ozeti(
        kayitlar: Iterable[
            KararBasariKaydi
        ],
    ) -> dict[str, Any]:
        liste = tuple(
            kayitlar
        )

        kapananlar = tuple(
            kayit
            for kayit in liste
            if kayit.sonuc
            != OneriSonucu.BEKLIYOR
        )

        basarili = sum(
            kayit.sonuc
            == OneriSonucu.BASARILI
            for kayit in kapananlar
        )

        kismen = sum(
            kayit.sonuc
            == OneriSonucu
            .KISMEN_BASARILI
            for kayit in kapananlar
        )

        oran = (
            round(
                (
                    basarili
                    + kismen * 0.5
                )
                / len(kapananlar)
                * 100.0,
                3,
            )
            if kapananlar
            else 0.0
        )

        ozet = {
            "toplam_karar": len(
                liste
            ),
            "kapanan_karar": len(
                kapananlar
            ),
            "basarili": basarili,
            "kismen_basarili": (
                kismen
            ),
            "basari_orani": oran,
        }

        return {
            **ozet,
            "ozet_sha256": _muhur(
                ozet
            ),
        }


class KaynakGuvenOgrenmeMotoru:
    def guncelle(
        self,
        *,
        saglayici_id: str,
        toplam_istek: int,
        basarili_istek: int,
        hatali_istek: int,
        tutarli_veri: int,
        tutarsiz_veri: int,
        onceki_guven_puani: float,
    ) -> KaynakOgrenmeKaydi:
        if toplam_istek <= 0:
            raise ValueError(
                "Toplam istek pozitif olmalıdır."
            )

        erisim_orani = (
            basarili_istek
            / toplam_istek
            * 100.0
        )

        tutarlilik_toplami = (
            tutarli_veri
            + tutarsiz_veri
        )

        tutarlilik_orani = (
            tutarli_veri
            / tutarlilik_toplami
            * 100.0
            if tutarlilik_toplami > 0
            else 50.0
        )

        hata_cezasi = min(
            25.0,
            (
                hatali_istek
                / toplam_istek
                * 25.0
            ),
        )

        hesaplanan = (
            float(onceki_guven_puani)
            * 0.45
            + erisim_orani * 0.30
            + tutarlilik_orani * 0.25
            - hata_cezasi
        )

        yeni = round(
            max(
                0.0,
                min(
                    100.0,
                    hesaplanan,
                ),
            ),
            3,
        )

        if yeni > onceki_guven_puani:
            aciklama = (
                "Kaynak erişim ve tutarlılık "
                "sonuçlarına göre güçlendi."
            )
        elif yeni < onceki_guven_puani:
            aciklama = (
                "Kaynak hata veya tutarsızlık "
                "sonuçları nedeniyle zayıfladı."
            )
        else:
            aciklama = (
                "Kaynak güven puanı değişmedi."
            )

        kanit = {
            "saglayici_id": (
                saglayici_id
            ),
            "toplam_istek": toplam_istek,
            "basarili_istek": (
                basarili_istek
            ),
            "hatali_istek": (
                hatali_istek
            ),
            "tutarli_veri": (
                tutarli_veri
            ),
            "tutarsiz_veri": (
                tutarsiz_veri
            ),
            "onceki_guven_puani": (
                onceki_guven_puani
            ),
            "yeni_guven_puani": yeni,
        }

        return KaynakOgrenmeKaydi(
            saglayici_id=saglayici_id,
            toplam_istek=toplam_istek,
            basarili_istek=(
                basarili_istek
            ),
            hatali_istek=hatali_istek,
            tutarli_veri=tutarli_veri,
            tutarsiz_veri=(
                tutarsiz_veri
            ),
            onceki_guven_puani=float(
                onceki_guven_puani
            ),
            yeni_guven_puani=yeni,
            aciklama=aciklama,
            kayit_sha256=_muhur(
                kanit
            ),
        )


class FinansArastirmaArgeMotoru:
    def oneriler_uret(
        self,
        *,
        kaynak_durumlari: Iterable[
            Mapping[str, Any]
        ] = (),
        karar_basari_ozeti: (
            Mapping[str, Any] | None
        ) = None,
        portfoy_ozeti: (
            Mapping[str, Any] | None
        ) = None,
    ) -> tuple[
        ArastirmaOnerisi,
        ...
    ]:
        oneriler: list[
            ArastirmaOnerisi
        ] = []

        for kaynak in kaynak_durumlari:
            durum = str(
                kaynak.get(
                    "durum",
                    "",
                )
            )

            basari_orani = float(
                kaynak.get(
                    "basari_orani",
                    0.0,
                )
            )

            if (
                durum == "erisilemiyor"
                or basari_orani < 80.0
            ):
                saglayici = str(
                    kaynak.get(
                        "saglayici_id",
                        "bilinmeyen",
                    )
                )

                kanitlar = (
                    f"Durum: {durum}",
                    (
                        "Başarı oranı: "
                        f"{basari_orani:.1f}"
                    ),
                )

                veri = {
                    "saglayici": saglayici,
                    "kategori": (
                        "veri_kaynagi"
                    ),
                    "kanitlar": list(
                        kanitlar
                    ),
                }

                oneriler.append(
                    ArastirmaOnerisi(
                        oneri_id=(
                            "KAYNAK-"
                            + saglayici
                        ),
                        baslik=(
                            f"{saglayici} için "
                            "yedek kaynak araştır"
                        ),
                        kategori=(
                            "veri_kaynagi"
                        ),
                        oncelik=(
                            ArastirmaOnceligi
                            .YUKSEK
                        ),
                        gerekce=(
                            "Kaynak erişimi veya "
                            "başarı oranı yeterli değil."
                        ),
                        beklenen_fayda=(
                            "Kesinti dayanımını ve "
                            "çapraz doğrulamayı artırmak."
                        ),
                        kanitlar=kanitlar,
                        otomatik_uygulanabilir=False,
                        kullanici_onayi_gerekli=True,
                        oneri_sha256=_muhur(
                            veri
                        ),
                    )
                )

        if karar_basari_ozeti is not None:
            oran = float(
                karar_basari_ozeti.get(
                    "basari_orani",
                    0.0,
                )
            )

            kapanan = int(
                karar_basari_ozeti.get(
                    "kapanan_karar",
                    0,
                )
            )

            if kapanan >= 5 and oran < 60.0:
                kanitlar = (
                    (
                        "Kapanan karar: "
                        f"{kapanan}"
                    ),
                    (
                        "Başarı oranı: "
                        f"{oran:.1f}"
                    ),
                )

                veri = {
                    "kategori": (
                        "karar_modeli"
                    ),
                    "kanitlar": list(
                        kanitlar
                    ),
                }

                oneriler.append(
                    ArastirmaOnerisi(
                        oneri_id=(
                            "KARAR-MODELI-001"
                        ),
                        baslik=(
                            "Karar puanı ağırlıklarını "
                            "yeniden incele"
                        ),
                        kategori=(
                            "karar_modeli"
                        ),
                        oncelik=(
                            ArastirmaOnceligi
                            .YUKSEK
                        ),
                        gerekce=(
                            "Geçmiş karar başarısı "
                            "hedef seviyenin altında."
                        ),
                        beklenen_fayda=(
                            "Risk, güven, trend ve "
                            "kanıt ağırlıklarını "
                            "iyileştirmek."
                        ),
                        kanitlar=kanitlar,
                        otomatik_uygulanabilir=False,
                        kullanici_onayi_gerekli=True,
                        oneri_sha256=_muhur(
                            veri
                        ),
                    )
                )

        if portfoy_ozeti is not None:
            en_yuksek_oran = float(
                portfoy_ozeti.get(
                    "en_yuksek_varlik_orani",
                    0.0,
                )
            )

            if en_yuksek_oran > 40.0:
                kanitlar = (
                    (
                        "En yüksek varlık oranı: "
                        f"{en_yuksek_oran:.1f}%"
                    ),
                )

                veri = {
                    "kategori": (
                        "portfoy_riski"
                    ),
                    "kanitlar": list(
                        kanitlar
                    ),
                }

                oneriler.append(
                    ArastirmaOnerisi(
                        oneri_id=(
                            "PORTFOY-DENGE-001"
                        ),
                        baslik=(
                            "Portföy yoğunlaşma "
                            "riskini incele"
                        ),
                        kategori=(
                            "portfoy_riski"
                        ),
                        oncelik=(
                            ArastirmaOnceligi
                            .ORTA
                        ),
                        gerekce=(
                            "Tek varlık ağırlığı "
                            "yüksek seviyeye ulaştı."
                        ),
                        beklenen_fayda=(
                            "Portföy riskini daha "
                            "dengeli dağıtmak."
                        ),
                        kanitlar=kanitlar,
                        otomatik_uygulanabilir=False,
                        kullanici_onayi_gerekli=True,
                        oneri_sha256=_muhur(
                            veri
                        ),
                    )
                )

        return tuple(
            sorted(
                oneriler,
                key=lambda oneri: (
                    {
                        ArastirmaOnceligi.KRITIK: 4,
                        ArastirmaOnceligi.YUKSEK: 3,
                        ArastirmaOnceligi.ORTA: 2,
                        ArastirmaOnceligi.DUSUK: 1,
                    }[
                        oneri.oncelik
                    ],
                    oneri.oneri_id,
                ),
                reverse=True,
            )
        )
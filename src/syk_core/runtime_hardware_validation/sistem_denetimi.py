"""Gerçek sistem USB, ağ ve seri bağlantı denetimi."""

from __future__ import annotations

import json
import platform
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Sequence


class SistemDenetimHatasi(RuntimeError):
    """Gerçek sistem bağlantı denetimi hatası."""


class DenetimTuru(str, Enum):
    USB = "usb"
    AG = "ağ"
    SERI = "seri"
    SISTEM = "sistem"


class DenetimDurumu(str, Enum):
    BASARILI = "başarılı"
    BASARISIZ = "başarısız"
    KISMI = "kısmi"
    DESTEKLENMIYOR = "desteklenmiyor"


@dataclass(slots=True, frozen=True)
class KomutSonucu:
    komut: tuple[str, ...]
    cikis_kodu: int
    standart_cikti: str
    hata_ciktisi: str
    sure_milisaniye: float

    @property
    def basarili_mi(self) -> bool:
        return self.cikis_kodu == 0

    def sozluk(self) -> dict[str, Any]:
        return {
            "komut": list(self.komut),
            "çıkış_kodu": self.cikis_kodu,
            "başarılı": self.basarili_mi,
            "standart_çıktı": self.standart_cikti,
            "hata_çıktısı": self.hata_ciktisi,
            "süre_milisaniye": self.sure_milisaniye,
        }


@dataclass(slots=True, frozen=True)
class UsbCihazBilgisi:
    cihaz_kimligi: str
    cihaz_adi: str
    uretici: str | None = None
    durum: str | None = None
    pnp_kimligi: str | None = None

    def sozluk(self) -> dict[str, Any]:
        return {
            "cihaz_kimliği": self.cihaz_kimligi,
            "cihaz_adı": self.cihaz_adi,
            "üretici": self.uretici,
            "durum": self.durum,
            "pnp_kimliği": self.pnp_kimligi,
        }


@dataclass(slots=True, frozen=True)
class SeriBaglantiBilgisi:
    baglanti_noktasi: str
    aciklama: str
    uretici: str | None = None
    cihaz_kimligi: str | None = None

    def sozluk(self) -> dict[str, Any]:
        return {
            "bağlantı_noktası": self.baglanti_noktasi,
            "açıklama": self.aciklama,
            "üretici": self.uretici,
            "cihaz_kimliği": self.cihaz_kimligi,
        }


@dataclass(slots=True, frozen=True)
class AgArayuzuBilgisi:
    arayuz_adi: str
    durum: str
    mac_adresi: str | None = None
    ip_adresleri: tuple[str, ...] = ()
    ag_gecidi: str | None = None
    dns_adresleri: tuple[str, ...] = ()

    @property
    def etkin_mi(self) -> bool:
        return self.durum.casefold() in {
            "up",
            "etkin",
            "connected",
            "bağlı",
        }

    def sozluk(self) -> dict[str, Any]:
        return {
            "arayüz_adı": self.arayuz_adi,
            "durum": self.durum,
            "etkin": self.etkin_mi,
            "mac_adresi": self.mac_adresi,
            "ip_adresleri": list(self.ip_adresleri),
            "ağ_geçidi": self.ag_gecidi,
            "dns_adresleri": list(self.dns_adresleri),
        }


@dataclass(slots=True, frozen=True)
class AgNoktasiSonucu:
    ana_makine: str
    baglanti_noktasi: int
    erisilebilir: bool
    gecikme_milisaniye: float | None = None
    hata: str | None = None

    def sozluk(self) -> dict[str, Any]:
        return {
            "ana_makine": self.ana_makine,
            "bağlantı_noktası": self.baglanti_noktasi,
            "erişilebilir": self.erisilebilir,
            "gecikme_milisaniye": self.gecikme_milisaniye,
            "hata": self.hata,
        }


@dataclass(slots=True)
class SistemDenetimSonucu:
    denetim_turu: DenetimTuru
    durum: DenetimDurumu
    baslama_zamani: datetime
    bitis_zamani: datetime
    kayitlar: list[dict[str, Any]] = field(
        default_factory=list
    )
    hata: str | None = None

    def __post_init__(self) -> None:
        if self.baslama_zamani.tzinfo is None:
            raise ValueError(
                "Denetim başlangıç zamanı saat dilimi içermelidir."
            )

        if self.bitis_zamani.tzinfo is None:
            raise ValueError(
                "Denetim bitiş zamanı saat dilimi içermelidir."
            )

        if self.bitis_zamani < self.baslama_zamani:
            raise ValueError(
                "Denetim bitiş zamanı başlangıçtan önce olamaz."
            )

    @property
    def basarili_mi(self) -> bool:
        return self.durum is DenetimDurumu.BASARILI

    def sozluk(self) -> dict[str, Any]:
        return {
            "denetim_türü": self.denetim_turu.value,
            "durum": self.durum.value,
            "başarılı": self.basarili_mi,
            "başlama_zamanı": (
                self.baslama_zamani.isoformat()
            ),
            "bitiş_zamanı": (
                self.bitis_zamani.isoformat()
            ),
            "kayıt_sayısı": len(self.kayitlar),
            "kayıtlar": list(self.kayitlar),
            "hata": self.hata,
        }


KomutCalistirici = Callable[
    [Sequence[str]],
    KomutSonucu,
]

YuvaDenetleyici = Callable[
    [str, int, float],
    AgNoktasiSonucu,
]


def komut_calistir(
    komut: Sequence[str],
    *,
    zaman_asimi_saniye: float = 10.0,
) -> KomutSonucu:
    if not komut:
        raise SistemDenetimHatasi(
            "Çalıştırılacak komut boş olamaz."
        )

    baslangic = time.perf_counter()

    try:
        sonuc = subprocess.run(
            list(komut),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=zaman_asimi_saniye,
            check=False,
        )

        sure = (
            time.perf_counter() - baslangic
        ) * 1000

        return KomutSonucu(
            komut=tuple(komut),
            cikis_kodu=sonuc.returncode,
            standart_cikti=sonuc.stdout.strip(),
            hata_ciktisi=sonuc.stderr.strip(),
            sure_milisaniye=round(sure, 3),
        )

    except subprocess.TimeoutExpired as hata:
        sure = (
            time.perf_counter() - baslangic
        ) * 1000

        return KomutSonucu(
            komut=tuple(komut),
            cikis_kodu=124,
            standart_cikti="",
            hata_ciktisi=(
                f"Komut zaman aşımına uğradı: {hata}"
            ),
            sure_milisaniye=round(sure, 3),
        )

    except OSError as hata:
        sure = (
            time.perf_counter() - baslangic
        ) * 1000

        return KomutSonucu(
            komut=tuple(komut),
            cikis_kodu=127,
            standart_cikti="",
            hata_ciktisi=str(hata),
            sure_milisaniye=round(sure, 3),
        )


def ag_noktasi_denetle(
    ana_makine: str,
    baglanti_noktasi: int,
    zaman_asimi_saniye: float = 2.0,
) -> AgNoktasiSonucu:
    if not ana_makine.strip():
        raise ValueError(
            "Ana makine boş olamaz."
        )

    if not 1 <= baglanti_noktasi <= 65535:
        raise ValueError(
            "Bağlantı noktası 1–65535 aralığında olmalıdır."
        )

    baslangic = time.perf_counter()

    try:
        with socket.create_connection(
            (
                ana_makine,
                baglanti_noktasi,
            ),
            timeout=zaman_asimi_saniye,
        ):
            sure = (
                time.perf_counter() - baslangic
            ) * 1000

            return AgNoktasiSonucu(
                ana_makine=ana_makine,
                baglanti_noktasi=baglanti_noktasi,
                erisilebilir=True,
                gecikme_milisaniye=round(
                    sure,
                    3,
                ),
            )

    except OSError as hata:
        sure = (
            time.perf_counter() - baslangic
        ) * 1000

        return AgNoktasiSonucu(
            ana_makine=ana_makine,
            baglanti_noktasi=baglanti_noktasi,
            erisilebilir=False,
            gecikme_milisaniye=round(
                sure,
                3,
            ),
            hata=str(hata),
        )


class GercekSistemDenetleyicisi:
    """Windows üzerindeki gerçek bağlantı noktalarını denetler."""

    def __init__(
        self,
        *,
        saat: Callable[[], datetime] | None = None,
        komut_calistirici: KomutCalistirici | None = None,
        yuva_denetleyici: YuvaDenetleyici | None = None,
        sistem_adi: str | None = None,
    ) -> None:
        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self._komut_calistirici = (
            komut_calistirici
            or (
                lambda komut: komut_calistir(
                    komut
                )
            )
        )

        self._yuva_denetleyici = (
            yuva_denetleyici
            or ag_noktasi_denetle
        )

        self.sistem_adi = (
            sistem_adi
            or platform.system()
        )

        self._sonuclar: list[
            SistemDenetimSonucu
        ] = []

    @property
    def windows_mu(self) -> bool:
        return (
            self.sistem_adi.casefold()
            == "windows"
        )

    def usb_cihazlarini_denetle(
        self,
    ) -> SistemDenetimSonucu:
        baslangic = self._saat()

        if not self.windows_mu:
            return self._sonuc_ekle(
                SistemDenetimSonucu(
                    denetim_turu=DenetimTuru.USB,
                    durum=(
                        DenetimDurumu.DESTEKLENMIYOR
                    ),
                    baslama_zamani=baslangic,
                    bitis_zamani=self._saat(),
                    hata=(
                        "USB denetimi bu aşamada "
                        "Windows için hazırlanmıştır."
                    ),
                )
            )

        komut = (
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-PnpDevice -PresentOnly | "
                "Where-Object { "
                "$_.InstanceId -like 'USB*' "
                "} | "
                "Select-Object "
                "InstanceId,FriendlyName,"
                "Manufacturer,Status | "
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        )

        komut_sonucu = (
            self._komut_calistirici(
                komut
            )
        )

        if not komut_sonucu.basarili_mi:
            return self._sonuc_ekle(
                SistemDenetimSonucu(
                    denetim_turu=DenetimTuru.USB,
                    durum=(
                        DenetimDurumu.BASARISIZ
                    ),
                    baslama_zamani=baslangic,
                    bitis_zamani=self._saat(),
                    kayitlar=[
                        komut_sonucu.sozluk()
                    ],
                    hata=(
                        komut_sonucu.hata_ciktisi
                        or "USB aygıtları okunamadı."
                    ),
                )
            )

        cihazlar = self._usb_json_ayristir(
            komut_sonucu.standart_cikti
        )

        durum = (
            DenetimDurumu.BASARILI
            if cihazlar
            else DenetimDurumu.KISMI
        )

        return self._sonuc_ekle(
            SistemDenetimSonucu(
                denetim_turu=DenetimTuru.USB,
                durum=durum,
                baslama_zamani=baslangic,
                bitis_zamani=self._saat(),
                kayitlar=[
                    cihaz.sozluk()
                    for cihaz in cihazlar
                ],
                hata=(
                    None
                    if cihazlar
                    else "Bağlı USB aygıtı bulunamadı."
                ),
            )
        )

    def seri_baglanti_noktalarini_denetle(
        self,
    ) -> SistemDenetimSonucu:
        baslangic = self._saat()

        if not self.windows_mu:
            return self._sonuc_ekle(
                SistemDenetimSonucu(
                    denetim_turu=DenetimTuru.SERI,
                    durum=(
                        DenetimDurumu.DESTEKLENMIYOR
                    ),
                    baslama_zamani=baslangic,
                    bitis_zamani=self._saat(),
                    hata=(
                        "Seri bağlantı denetimi bu aşamada "
                        "Windows için hazırlanmıştır."
                    ),
                )
            )

        komut = (
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-CimInstance Win32_SerialPort | "
                "Select-Object "
                "DeviceID,Name,Manufacturer,PNPDeviceID | "
                "ConvertTo-Json -Depth 4 -Compress"
            ),
        )

        komut_sonucu = (
            self._komut_calistirici(
                komut
            )
        )

        if not komut_sonucu.basarili_mi:
            return self._sonuc_ekle(
                SistemDenetimSonucu(
                    denetim_turu=DenetimTuru.SERI,
                    durum=(
                        DenetimDurumu.BASARISIZ
                    ),
                    baslama_zamani=baslangic,
                    bitis_zamani=self._saat(),
                    kayitlar=[
                        komut_sonucu.sozluk()
                    ],
                    hata=(
                        komut_sonucu.hata_ciktisi
                        or "Seri bağlantı noktaları okunamadı."
                    ),
                )
            )

        noktalar = self._seri_json_ayristir(
            komut_sonucu.standart_cikti
        )

        durum = (
            DenetimDurumu.BASARILI
            if noktalar
            else DenetimDurumu.KISMI
        )

        return self._sonuc_ekle(
            SistemDenetimSonucu(
                denetim_turu=DenetimTuru.SERI,
                durum=durum,
                baslama_zamani=baslangic,
                bitis_zamani=self._saat(),
                kayitlar=[
                    nokta.sozluk()
                    for nokta in noktalar
                ],
                hata=(
                    None
                    if noktalar
                    else (
                        "Etkin seri bağlantı "
                        "noktası bulunamadı."
                    )
                ),
            )
        )

    def ag_arayuzlerini_denetle(
        self,
    ) -> SistemDenetimSonucu:
        baslangic = self._saat()

        if not self.windows_mu:
            return self._sonuc_ekle(
                SistemDenetimSonucu(
                    denetim_turu=DenetimTuru.AG,
                    durum=(
                        DenetimDurumu.DESTEKLENMIYOR
                    ),
                    baslama_zamani=baslangic,
                    bitis_zamani=self._saat(),
                    hata=(
                        "Ağ arayüzü denetimi bu aşamada "
                        "Windows için hazırlanmıştır."
                    ),
                )
            )

        komut = (
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$adapters = Get-NetAdapter | "
                "Select-Object Name,Status,MacAddress;"
                "$configs = Get-NetIPConfiguration;"
                "$result = foreach ($adapter in $adapters) {"
                "$config = $configs | "
                "Where-Object { "
                "$_.InterfaceAlias -eq $adapter.Name "
                "} | Select-Object -First 1;"
                "[PSCustomObject]@{"
                "Name=$adapter.Name;"
                "Status=$adapter.Status;"
                "MacAddress=$adapter.MacAddress;"
                "IPAddresses=@("
                "$config.IPv4Address.IPAddress"
                ");"
                "Gateway=("
                "$config.IPv4DefaultGateway.NextHop | "
                "Select-Object -First 1"
                ");"
                "DnsServers=@("
                "$config.DNSServer.ServerAddresses"
                ")"
                "}"
                "};"
                "$result | ConvertTo-Json "
                "-Depth 5 -Compress"
            ),
        )

        komut_sonucu = (
            self._komut_calistirici(
                komut
            )
        )

        if not komut_sonucu.basarili_mi:
            return self._sonuc_ekle(
                SistemDenetimSonucu(
                    denetim_turu=DenetimTuru.AG,
                    durum=(
                        DenetimDurumu.BASARISIZ
                    ),
                    baslama_zamani=baslangic,
                    bitis_zamani=self._saat(),
                    kayitlar=[
                        komut_sonucu.sozluk()
                    ],
                    hata=(
                        komut_sonucu.hata_ciktisi
                        or "Ağ arayüzleri okunamadı."
                    ),
                )
            )

        arayuzler = self._ag_json_ayristir(
            komut_sonucu.standart_cikti
        )

        etkin_sayisi = sum(
            arayuz.etkin_mi
            for arayuz in arayuzler
        )

        if etkin_sayisi > 0:
            durum = DenetimDurumu.BASARILI
            hata = None
        elif arayuzler:
            durum = DenetimDurumu.KISMI
            hata = "Etkin ağ arayüzü bulunamadı."
        else:
            durum = DenetimDurumu.BASARISIZ
            hata = "Ağ arayüzü bulunamadı."

        return self._sonuc_ekle(
            SistemDenetimSonucu(
                denetim_turu=DenetimTuru.AG,
                durum=durum,
                baslama_zamani=baslangic,
                bitis_zamani=self._saat(),
                kayitlar=[
                    arayuz.sozluk()
                    for arayuz in arayuzler
                ],
                hata=hata,
            )
        )

    def ag_noktasini_denetle(
        self,
        *,
        ana_makine: str,
        baglanti_noktasi: int,
        zaman_asimi_saniye: float = 2.0,
    ) -> SistemDenetimSonucu:
        baslangic = self._saat()

        sonuc = self._yuva_denetleyici(
            ana_makine,
            baglanti_noktasi,
            zaman_asimi_saniye,
        )

        return self._sonuc_ekle(
            SistemDenetimSonucu(
                denetim_turu=DenetimTuru.AG,
                durum=(
                    DenetimDurumu.BASARILI
                    if sonuc.erisilebilir
                    else DenetimDurumu.BASARISIZ
                ),
                baslama_zamani=baslangic,
                bitis_zamani=self._saat(),
                kayitlar=[
                    sonuc.sozluk()
                ],
                hata=sonuc.hata,
            )
        )

    def tum_baglantilari_denetle(
        self,
        *,
        ag_noktalari: Sequence[
            tuple[str, int]
        ] = (),
    ) -> dict[str, Any]:
        usb = self.usb_cihazlarini_denetle()
        seri = (
            self.seri_baglanti_noktalarini_denetle()
        )
        ag = self.ag_arayuzlerini_denetle()

        noktalar = [
            self.ag_noktasini_denetle(
                ana_makine=ana_makine,
                baglanti_noktasi=port,
            )
            for ana_makine, port
            in ag_noktalari
        ]

        sonuclar = [
            usb,
            seri,
            ag,
            *noktalar,
        ]

        basarisiz_sayisi = sum(
            sonuc.durum
            is DenetimDurumu.BASARISIZ
            for sonuc in sonuclar
        )

        basarili_sayisi = sum(
            sonuc.durum
            is DenetimDurumu.BASARILI
            for sonuc in sonuclar
        )

        return {
            "sistem": self.sistem_adi,
            "toplam_denetim_sayısı": len(
                sonuclar
            ),
            "başarılı_denetim_sayısı": (
                basarili_sayisi
            ),
            "başarısız_denetim_sayısı": (
                basarisiz_sayisi
            ),
            "gerçek_sistem_denetimi": True,
            "sonuçlar": [
                sonuc.sozluk()
                for sonuc in sonuclar
            ],
        }

    def sonuc_kaydi_yaz(
        self,
        dosya: str | Path,
    ) -> Path:
        hedef = Path(dosya)

        hedef.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        veri = {
            "sistem": self.sistem_adi,
            "kayıt_zamanı": (
                self._saat().isoformat()
            ),
            "denetimler": [
                sonuc.sozluk()
                for sonuc in self._sonuclar
            ],
        }

        hedef.write_text(
            json.dumps(
                veri,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return hedef

    def sonuclari_listele(
        self,
    ) -> tuple[SistemDenetimSonucu, ...]:
        return tuple(self._sonuclar)

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "sistem": self.sistem_adi,
            "windows": self.windows_mu,
            "toplam_denetim_sayısı": len(
                self._sonuclar
            ),
            "başarılı_denetim_sayısı": sum(
                sonuc.basarili_mi
                for sonuc in self._sonuclar
            ),
            "gerçek_bağlantı_denetimi": (
                "çalıştırıldı"
                if self._sonuclar
                else "bekliyor"
            ),
        }

    def _sonuc_ekle(
        self,
        sonuc: SistemDenetimSonucu,
    ) -> SistemDenetimSonucu:
        self._sonuclar.append(
            sonuc
        )

        return sonuc

    @staticmethod
    def _json_listeye_cevir(
        ham: str,
    ) -> list[dict[str, Any]]:
        if not ham.strip():
            return []

        try:
            veri = json.loads(ham)
        except json.JSONDecodeError as hata:
            raise SistemDenetimHatasi(
                "Sistem komutu geçerli JSON üretmedi."
            ) from hata

        if isinstance(veri, dict):
            return [veri]

        if isinstance(veri, list):
            return [
                kayit
                for kayit in veri
                if isinstance(kayit, dict)
            ]

        raise SistemDenetimHatasi(
            "Sistem komutu beklenmeyen veri üretti."
        )

    @classmethod
    def _usb_json_ayristir(
        cls,
        ham: str,
    ) -> tuple[UsbCihazBilgisi, ...]:
        kayitlar = cls._json_listeye_cevir(
            ham
        )

        sonuc: list[UsbCihazBilgisi] = []

        for kayit in kayitlar:
            kimlik = str(
                kayit.get("InstanceId")
                or kayit.get("PNPDeviceID")
                or ""
            ).strip()

            ad = str(
                kayit.get("FriendlyName")
                or kayit.get("Name")
                or kimlik
                or "Bilinmeyen USB aygıtı"
            ).strip()

            if not kimlik:
                continue

            sonuc.append(
                UsbCihazBilgisi(
                    cihaz_kimligi=kimlik,
                    cihaz_adi=ad,
                    uretici=(
                        str(
                            kayit.get(
                                "Manufacturer"
                            )
                        )
                        if kayit.get(
                            "Manufacturer"
                        )
                        else None
                    ),
                    durum=(
                        str(kayit.get("Status"))
                        if kayit.get("Status")
                        else None
                    ),
                    pnp_kimligi=kimlik,
                )
            )

        return tuple(sonuc)

    @classmethod
    def _seri_json_ayristir(
        cls,
        ham: str,
    ) -> tuple[SeriBaglantiBilgisi, ...]:
        kayitlar = cls._json_listeye_cevir(
            ham
        )

        sonuc: list[
            SeriBaglantiBilgisi
        ] = []

        for kayit in kayitlar:
            nokta = str(
                kayit.get("DeviceID")
                or ""
            ).strip()

            if not nokta:
                continue

            sonuc.append(
                SeriBaglantiBilgisi(
                    baglanti_noktasi=nokta,
                    aciklama=str(
                        kayit.get("Name")
                        or nokta
                    ),
                    uretici=(
                        str(
                            kayit.get(
                                "Manufacturer"
                            )
                        )
                        if kayit.get(
                            "Manufacturer"
                        )
                        else None
                    ),
                    cihaz_kimligi=(
                        str(
                            kayit.get(
                                "PNPDeviceID"
                            )
                        )
                        if kayit.get(
                            "PNPDeviceID"
                        )
                        else None
                    ),
                )
            )

        return tuple(sonuc)

    @classmethod
    def _ag_json_ayristir(
        cls,
        ham: str,
    ) -> tuple[AgArayuzuBilgisi, ...]:
        kayitlar = cls._json_listeye_cevir(
            ham
        )

        sonuc: list[
            AgArayuzuBilgisi
        ] = []

        for kayit in kayitlar:
            ad = str(
                kayit.get("Name")
                or ""
            ).strip()

            if not ad:
                continue

            ipler = kayit.get(
                "IPAddresses"
            ) or []

            dnsler = kayit.get(
                "DnsServers"
            ) or []

            if isinstance(ipler, str):
                ipler = [ipler]

            if isinstance(dnsler, str):
                dnsler = [dnsler]

            sonuc.append(
                AgArayuzuBilgisi(
                    arayuz_adi=ad,
                    durum=str(
                        kayit.get("Status")
                        or "bilinmiyor"
                    ),
                    mac_adresi=(
                        str(
                            kayit.get(
                                "MacAddress"
                            )
                        )
                        if kayit.get(
                            "MacAddress"
                        )
                        else None
                    ),
                    ip_adresleri=tuple(
                        str(ip)
                        for ip in ipler
                        if ip
                    ),
                    ag_gecidi=(
                        str(
                            kayit.get(
                                "Gateway"
                            )
                        )
                        if kayit.get(
                            "Gateway"
                        )
                        else None
                    ),
                    dns_adresleri=tuple(
                        str(dns)
                        for dns in dnsler
                        if dns
                    ),
                )
            )

        return tuple(sonuc)

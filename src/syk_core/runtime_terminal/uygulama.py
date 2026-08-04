"""SyKaşif terminal uygulaması birleştiricisi."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Callable

from fastapi import FastAPI

from .ag_gecidi import TerminalAgGecidi
from .ag_modelleri import AgGecidiAyarlari
from .arac_modelleri import (
    IslemTuru,
    UygulamaDurumu,
    UygulamaTanimi,
)
from .cihaz_araci import YetkiliCihazAraci
from .modeller import (
    CihazTuru,
    YetkiliCihazTanimi,
    YetkiSeviyesi,
)
from .oturum_yoneticisi import (
    TerminalOturumYoneticisi,
)
from .panel import TerminalPaneli
from .panel_modelleri import PanelAyarlari
from .terminal import CalismaTerminali
from .uygulama_modelleri import (
    CalismaKipi,
    TerminalUygulamasiAyarlari,
    TerminalUygulamasiHatasi,
)


class YerelUygulamaIsletmeni:
    """Yerel uygulamaları güvenli süreç kimliğiyle çalıştırır."""

    def __init__(
        self,
        *,
        gercek_isleme_izin_ver: bool = False,
    ) -> None:
        self.gercek_isleme_izin_ver = (
            gercek_isleme_izin_ver
        )

        self._surecler: dict[
            str,
            subprocess.Popen[Any],
        ] = {}

        self._sahte_islem_kimligi = 50000
        self._kilit = RLock()

    def baslat(
        self,
        tanim: UygulamaTanimi,
    ) -> int:
        with self._kilit:
            mevcut = self._surecler.get(
                tanim.uygulama_kimligi
            )

            if (
                mevcut is not None
                and mevcut.poll() is None
            ):
                return int(mevcut.pid)

            if not self.gercek_isleme_izin_ver:
                self._sahte_islem_kimligi += 1
                return self._sahte_islem_kimligi

            yol = Path(
                tanim.calistirma_yolu
            ).expanduser()

            if not yol.exists():
                raise TerminalUygulamasiHatasi(
                    "Uygulama çalıştırma yolu bulunamadı: "
                    f"{yol}"
                )

            komut = self._komut_olustur(
                tanim,
                yol,
            )

            surec = subprocess.Popen(
                komut,
                cwd=(
                    str(yol)
                    if yol.is_dir()
                    else str(yol.parent)
                ),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    if sys.platform == "win32"
                    else 0
                ),
            )

            self._surecler[
                tanim.uygulama_kimligi
            ] = surec

            return int(surec.pid)

    def kapat(
        self,
        tanim: UygulamaTanimi,
        durum: UygulamaDurumu,
    ) -> bool:
        with self._kilit:
            if not self.gercek_isleme_izin_ver:
                return True

            surec = self._surecler.get(
                tanim.uygulama_kimligi
            )

            if surec is None:
                return True

            if surec.poll() is not None:
                self._surecler.pop(
                    tanim.uygulama_kimligi,
                    None,
                )
                return True

            surec.terminate()

            try:
                surec.wait(timeout=10)
            except subprocess.TimeoutExpired:
                surec.kill()
                surec.wait(timeout=5)

            self._surecler.pop(
                tanim.uygulama_kimligi,
                None,
            )

            return True

    @staticmethod
    def _komut_olustur(
        tanim: UygulamaTanimi,
        yol: Path,
    ) -> list[str]:
        degiskenler = list(
            tanim.calistirma_degiskenleri
        )

        if yol.is_file():
            return [
                str(yol),
                *degiskenler,
            ]

        baslatici = yol / "run.py"

        if baslatici.exists():
            return [
                sys.executable,
                str(baslatici),
                *degiskenler,
            ]

        return [
            sys.executable,
            "-m",
            "syk_ui.runtime_server",
            *degiskenler,
        ]


class GuvenliSistemIsletmeni:
    """Sistem işlemlerini varsayılan olarak yalnız kaydeder."""

    def __init__(
        self,
        *,
        gercek_isleme_izin_ver: bool = False,
    ) -> None:
        self.gercek_isleme_izin_ver = (
            gercek_isleme_izin_ver
        )

        self.islem_gecmisi: list[
            dict[str, Any]
        ] = []

    def calistir(
        self,
        islem_turu: IslemTuru,
        icerik: dict[str, Any],
    ) -> dict[str, Any]:
        kayit = {
            "işlem_türü": islem_turu.value,
            "içerik": dict(icerik),
            "gerçek_işlem": (
                self.gercek_isleme_izin_ver
            ),
            "durum": "kabul_edildi",
        }

        self.islem_gecmisi.append(
            kayit
        )

        if not self.gercek_isleme_izin_ver:
            return {
                **kayit,
                "açıklama": (
                    "Güvenlik nedeniyle yalnız kayıt oluşturuldu."
                ),
            }

        if sys.platform != "win32":
            raise TerminalUygulamasiHatasi(
                "Gerçek sistem işlemleri yalnız Windows "
                "üzerinde desteklenmektedir."
            )

        if islem_turu is IslemTuru.MASAUSTUNU_KAPAT:
            subprocess.run(
                [
                    "shutdown",
                    "/s",
                    "/t",
                    "30",
                    "/c",
                    "SyKaşif yetkili kapatma işlemi",
                ],
                check=True,
            )

        elif islem_turu is IslemTuru.GUVENLI_YENIDEN_BASLAT:
            subprocess.run(
                [
                    "shutdown",
                    "/r",
                    "/t",
                    "30",
                    "/c",
                    "SyKaşif yetkili yeniden başlatma işlemi",
                ],
                check=True,
            )

        elif islem_turu is IslemTuru.MASAUSTUNU_UYANDIR:
            raise TerminalUygulamasiHatasi(
                "Masaüstünü uyandırmak için ağ üzerinden "
                "uyandırma donanım ayarı gereklidir."
            )

        return kayit


class SyKasifTerminalUygulamasi:
    """Terminal, oturum, ağ geçidi, cihaz aracısı ve paneli birleştirir."""

    def __init__(
        self,
        *,
        ayarlar: TerminalUygulamasiAyarlari | None = None,
        saat: Callable[[], datetime] | None = None,
        gercek_uygulama_islemlerine_izin_ver: bool = False,
        gercek_sistem_islemlerine_izin_ver: bool = False,
    ) -> None:
        self.ayarlar = (
            ayarlar
            or TerminalUygulamasiAyarlari.varsayilan()
        )

        self._saat = saat or (
            lambda: datetime.now(UTC)
        )

        self.terminal = CalismaTerminali(
            saat=self._saat
        )

        self.oturum_yoneticisi = (
            TerminalOturumYoneticisi(
                self.terminal,
                saat=self._saat,
            )
        )

        self.uygulama_isletmeni = (
            YerelUygulamaIsletmeni(
                gercek_isleme_izin_ver=(
                    gercek_uygulama_islemlerine_izin_ver
                )
            )
        )

        self.sistem_isletmeni = (
            GuvenliSistemIsletmeni(
                gercek_isleme_izin_ver=(
                    gercek_sistem_islemlerine_izin_ver
                )
            )
        )

        self._cihazlari_kaydet()

        self.cihaz_araci = YetkiliCihazAraci(
            self.terminal,
            cihaz_kimligi=(
                self.ayarlar
                .ana_makine_cihaz_kimligi
            ),
            saat=self._saat,
            uygulama_baslatici=(
                self.uygulama_isletmeni.baslat
            ),
            uygulama_kapatici=(
                self.uygulama_isletmeni.kapat
            ),
            sistem_isleyicisi=(
                self.sistem_isletmeni.calistir
            ),
        )

        self.cihaz_araci.uygulama_kaydet(
            UygulamaTanimi(
                uygulama_kimligi=(
                    self.ayarlar
                    .sykasif_uygulama_kimligi
                ),
                gorunen_ad="SyKaşif",
                calistirma_yolu=(
                    self.ayarlar
                    .sykasif_calistirma_yolu
                ),
                guvenli_kapatma_destegi=True,
            )
        )

        self.ag_gecidi = TerminalAgGecidi(
            self.terminal,
            self.oturum_yoneticisi,
            saat=self._saat,
            ayarlar=AgGecidiAyarlari(
                ana_makine=(
                    self.ayarlar.ana_makine
                ),
                baglanti_noktasi=(
                    self.ayarlar.baglanti_noktasi
                ),
                dis_ag_erisimine_izin_ver=(
                    self.ayarlar
                    .dis_ag_erisimine_izin_ver
                ),
                oturum_anahtarini_yanitta_goster=(
                    self.ayarlar.calisma_kipi
                    is CalismaKipi.GELISTIRME
                ),
            ),
        )

        self.panel = TerminalPaneli(
            self.terminal,
            self.oturum_yoneticisi,
            ag_gecidi=self.ag_gecidi,
            saat=self._saat,
            ayarlar=PanelAyarlari(
                baslik="SyKaşif Terminali",
                alt_baslik=(
                    "Yetkili cihaz ve çalışma sistemi yönetimi"
                ),
            ),
        )

        self.panel.uygulamaya_bagla(
            self.ag_gecidi.uygulama,
            panel_yolu=(
                self.ayarlar.panel_yolu
            ),
            veri_yolu=(
                self.ayarlar.panel_veri_yolu
            ),
        )

        self.uygulama: FastAPI = (
            self.ag_gecidi.uygulama
        )

        self.uygulama.state.sykasif_terminal = self

        self._yasam_dongusunu_kaydet()
        self.durum_kaydi_yaz()

    def _cihazlari_kaydet(
        self,
    ) -> None:
        for cihaz_ayari in (
            self.ayarlar.yetkili_cihazlar
        ):
            cihaz_turu = CihazTuru(
                cihaz_ayari.cihaz_turu
            )

            yetki_seviyesi = YetkiSeviyesi(
                cihaz_ayari.yetki_seviyesi
            )

            self.terminal.cihaz_kaydet(
                YetkiliCihazTanimi(
                    cihaz_kimligi=(
                        cihaz_ayari.cihaz_kimligi
                    ),
                    ad=cihaz_ayari.ad,
                    cihaz_turu=cihaz_turu,
                    yetki_seviyesi=(
                        yetki_seviyesi
                    ),
                    cihaz_parmak_izi=(
                        cihaz_ayari
                        .cihaz_parmak_izi
                    ),
                    aciklama=(
                        cihaz_ayari.aciklama
                    ),
                    veri=dict(
                        cihaz_ayari.veri
                    ),
                )
            )

            if cihaz_ayari.baslangicta_bagli:
                self.terminal.cihaz_bagla(
                    cihaz_ayari.cihaz_kimligi,
                    cihaz_parmak_izi=(
                        cihaz_ayari
                        .cihaz_parmak_izi
                    ),
                )

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "sistem": "SyKaşif",
            "bileşen": "Terminal Uygulaması",
            "durum": "hazır",
            "çalışma_kipi": (
                self.ayarlar.calisma_kipi.value
            ),
            "zaman": self._saat().isoformat(),
            "ayarlar": self.ayarlar.sozluk(),
            "terminal": (
                self.terminal.durum_ozeti()
            ),
            "oturumlar": (
                self.oturum_yoneticisi
                .durum_ozeti()
            ),
            "ağ_geçidi": (
                self.ag_gecidi.durum_ozeti()
            ),
            "panel": (
                self.panel
                .anlik_gorunum_olustur()
                .sozluk()
            ),
            "cihaz_aracı": (
                self.cihaz_araci.durum_ozeti()
            ),
        }

    def durum_kaydi_yaz(
        self,
    ) -> Path:
        yol = (
            self.ayarlar
            .durum_dosyasi_yolu()
        )

        yol.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        gecici_yol = yol.with_suffix(
            yol.suffix + ".tmp"
        )

        gecici_yol.write_text(
            json.dumps(
                self.durum_ozeti(),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        gecici_yol.replace(yol)

        return yol

    def guvenli_durdur(
        self,
    ) -> None:
        self.cihaz_araci.guvenli_durdur()

        for oturum in (
            self.oturum_yoneticisi
            .oturumlari_listele()
        ):
            if oturum.sona_erdi_mi:
                continue

            self.oturum_yoneticisi.oturumu_sonlandir(
                oturum.oturum_kimligi,
                gerekce=(
                    "Terminal uygulaması güvenli durduruldu."
                ),
            )

        self.durum_kaydi_yaz()

    def _yasam_dongusunu_kaydet(
        self,
    ) -> None:
        onceki_yasam_dongusu = (
            self.uygulama.router.lifespan_context
        )

        @asynccontextmanager
        async def terminal_yasam_dongusu(
            uygulama: FastAPI,
        ):
            self.durum_kaydi_yaz()

            if onceki_yasam_dongusu is None:
                try:
                    yield
                finally:
                    self.guvenli_durdur()

                return

            async with onceki_yasam_dongusu(
                uygulama
            ):
                try:
                    yield
                finally:
                    self.guvenli_durdur()

        self.uygulama.router.lifespan_context = (
            terminal_yasam_dongusu
        )


def terminal_uygulamasi_olustur(
    *,
    ayarlar: TerminalUygulamasiAyarlari | None = None,
    gercek_uygulama_islemlerine_izin_ver: bool = False,
    gercek_sistem_islemlerine_izin_ver: bool = False,
) -> FastAPI:
    terminal_uygulamasi = (
        SyKasifTerminalUygulamasi(
            ayarlar=ayarlar,
            gercek_uygulama_islemlerine_izin_ver=(
                gercek_uygulama_islemlerine_izin_ver
            ),
            gercek_sistem_islemlerine_izin_ver=(
                gercek_sistem_islemlerine_izin_ver
            ),
        )
    )

    return terminal_uygulamasi.uygulama


varsayilan_terminal_uygulamasi = (
    SyKasifTerminalUygulamasi()
)

uygulama = (
    varsayilan_terminal_uygulamasi
    .uygulama
)

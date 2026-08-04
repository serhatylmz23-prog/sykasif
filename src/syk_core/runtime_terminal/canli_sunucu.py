"""SyKaşif yönetilebilir canlı terminal sunucusu."""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from threading import RLock, Thread
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn
from fastapi import FastAPI


class CanliSunucuHatasi(RuntimeError):
    """Canlı terminal sunucusu hatası."""


@dataclass(slots=True, frozen=True)
class CanliSunucuAyarlari:
    ana_makine: str = "127.0.0.1"
    baglanti_noktasi: int = 0
    baslama_zaman_asimi_saniye: float = 15.0
    durma_zaman_asimi_saniye: float = 15.0
    saglik_yolu: str = "/saglik"
    gunluk_seviyesi: str = "warning"
    erisim_gunlugu: bool = False

    def __post_init__(self) -> None:
        if not self.ana_makine.strip():
            raise ValueError(
                "Ana makine adresi boş olamaz."
            )

        if not 0 <= self.baglanti_noktasi <= 65535:
            raise ValueError(
                "Bağlantı noktası 0 ile 65535 arasında olmalıdır."
            )

        if self.baslama_zaman_asimi_saniye <= 0:
            raise ValueError(
                "Başlama zaman aşımı sıfırdan büyük olmalıdır."
            )

        if self.durma_zaman_asimi_saniye <= 0:
            raise ValueError(
                "Durma zaman aşımı sıfırdan büyük olmalıdır."
            )

        if not self.saglik_yolu.startswith("/"):
            raise ValueError(
                "Sağlık yolu eğik çizgi ile başlamalıdır."
            )


class CanliTerminalSunucusu:
    """FastAPI terminal uygulamasını ayrı iş parçacığında çalıştırır."""

    def __init__(
        self,
        uygulama: FastAPI,
        *,
        ayarlar: CanliSunucuAyarlari | None = None,
    ) -> None:
        self.uygulama = uygulama
        self.ayarlar = (
            ayarlar
            or CanliSunucuAyarlari()
        )

        self._baglanti_noktasi = (
            self.ayarlar.baglanti_noktasi
        )
        self._sunucu: uvicorn.Server | None = None
        self._is_parcacigi: Thread | None = None
        self._kilit = RLock()
        self._son_hata: str | None = None

    @property
    def baglanti_noktasi(
        self,
    ) -> int:
        return self._baglanti_noktasi

    @property
    def ana_adres(
        self,
    ) -> str:
        return (
            f"http://{self.ayarlar.ana_makine}:"
            f"{self.baglanti_noktasi}"
        )

    @property
    def calisiyor_mu(
        self,
    ) -> bool:
        sunucu = self._sunucu
        is_parcacigi = self._is_parcacigi

        return bool(
            sunucu is not None
            and is_parcacigi is not None
            and is_parcacigi.is_alive()
            and sunucu.started
            and not sunucu.should_exit
        )

    @property
    def son_hata(
        self,
    ) -> str | None:
        return self._son_hata

    def baslat(
        self,
    ) -> "CanliTerminalSunucusu":
        with self._kilit:
            if self.calisiyor_mu:
                return self

            if self._is_parcacigi is not None:
                if self._is_parcacigi.is_alive():
                    raise CanliSunucuHatasi(
                        "Önceki sunucu iş parçacığı hâlâ çalışıyor."
                    )

            self._son_hata = None

            if self._baglanti_noktasi == 0:
                self._baglanti_noktasi = (
                    self._bos_baglanti_noktasi_bul()
                )

            yapilandirma = uvicorn.Config(
                app=self.uygulama,
                host=self.ayarlar.ana_makine,
                port=self._baglanti_noktasi,
                log_level=self.ayarlar.gunluk_seviyesi,
                access_log=self.ayarlar.erisim_gunlugu,
                lifespan="on",
            )

            self._sunucu = uvicorn.Server(
                yapilandirma
            )

            self._sunucu.install_signal_handlers = (
                lambda: None
            )

            self._is_parcacigi = Thread(
                target=self._sunucuyu_calistir,
                name="sykasif-terminal-canli-sunucu",
                daemon=True,
            )

            self._is_parcacigi.start()

        self._baslamayi_bekle()

        return self

    def durdur(
        self,
    ) -> None:
        with self._kilit:
            sunucu = self._sunucu
            is_parcacigi = self._is_parcacigi

            if sunucu is None:
                return

            sunucu.should_exit = True

        if is_parcacigi is not None:
            is_parcacigi.join(
                timeout=(
                    self.ayarlar
                    .durma_zaman_asimi_saniye
                )
            )

            if is_parcacigi.is_alive():
                sunucu.force_exit = True

                is_parcacigi.join(
                    timeout=5.0
                )

        if (
            is_parcacigi is not None
            and is_parcacigi.is_alive()
        ):
            raise CanliSunucuHatasi(
                "Canlı terminal sunucusu durdurulamadı."
            )

        with self._kilit:
            self._sunucu = None
            self._is_parcacigi = None

    def saglikli_mi(
        self,
    ) -> bool:
        if not self.calisiyor_mu:
            return False

        adres = (
            self.ana_adres
            + self.ayarlar.saglik_yolu
        )

        try:
            with urlopen(
                adres,
                timeout=2.0,
            ) as yanit:
                return (
                    int(yanit.status)
                    == 200
                )
        except (
            OSError,
            URLError,
            TimeoutError,
        ):
            return False

    def durum_ozeti(
        self,
    ) -> dict[str, Any]:
        return {
            "ana_makine": (
                self.ayarlar.ana_makine
            ),
            "bağlantı_noktası": (
                self.baglanti_noktasi
            ),
            "ana_adres": self.ana_adres,
            "çalışıyor_mu": self.calisiyor_mu,
            "sağlıklı_mı": self.saglikli_mi(),
            "son_hata": self.son_hata,
        }

    def __enter__(
        self,
    ) -> "CanliTerminalSunucusu":
        return self.baslat()

    def __exit__(
        self,
        hata_turu,
        hata,
        iz,
    ) -> None:
        self.durdur()

    def _sunucuyu_calistir(
        self,
    ) -> None:
        sunucu = self._sunucu

        if sunucu is None:
            self._son_hata = (
                "Sunucu nesnesi oluşturulmadı."
            )
            return

        try:
            sunucu.run()
        except BaseException as hata:
            self._son_hata = str(hata)

    def _baslamayi_bekle(
        self,
    ) -> None:
        bitis = (
            time.monotonic()
            + self.ayarlar
            .baslama_zaman_asimi_saniye
        )

        while time.monotonic() < bitis:
            if self._son_hata:
                self.durdur()

                raise CanliSunucuHatasi(
                    "Canlı terminal sunucusu başlatılamadı: "
                    f"{self._son_hata}"
                )

            is_parcacigi = self._is_parcacigi

            if (
                is_parcacigi is not None
                and not is_parcacigi.is_alive()
            ):
                hata = (
                    self._son_hata
                    or "Sunucu beklenmedik biçimde durdu."
                )

                self.durdur()

                raise CanliSunucuHatasi(
                    hata
                )

            if self.saglikli_mi():
                return

            time.sleep(0.05)

        self.durdur()

        raise CanliSunucuHatasi(
            "Canlı terminal sunucusu zamanında hazır olmadı."
        )

    def _bos_baglanti_noktasi_bul(
        self,
    ) -> int:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as yuva:
            yuva.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            yuva.bind(
                (
                    self.ayarlar.ana_makine,
                    0,
                )
            )

            return int(
                yuva.getsockname()[1]
            )

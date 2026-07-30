from __future__ import annotations

from contextlib import contextmanager
import socket
from threading import Thread
import time
from typing import Iterator

import httpx
from playwright.sync_api import sync_playwright
import uvicorn

from syk_simulasyon.runtime_anlik_gorunum import (
    RuntimeAnlikGorunumSaglayicisi,
)
from syk_simulasyon.runtime_csv import RuntimeCsvSaglayicisi
from syk_simulasyon.runtime_disa_aktarim import RuntimeDisaAktarim
from syk_simulasyon.runtime_durumu import RuntimeDurumTuru
from syk_simulasyon.runtime_fastapi_sunucusu import (
    RuntimeFastApiSunucusu,
)
from syk_simulasyon.runtime_html import RuntimeHtmlSaglayicisi
from syk_simulasyon.runtime_izleme import RuntimeIzlemeSaglayicisi
from syk_simulasyon.runtime_json import RuntimeJsonSaglayicisi
from syk_simulasyon.runtime_markdown import (
    RuntimeMarkdownSaglayicisi,
)
from syk_simulasyon.runtime_servisi import RuntimeServisi
from syk_simulasyon.runtime_websocket import (
    RuntimeWebSocketYayincisi,
)
from syk_simulasyon.runtime_xml import RuntimeXmlSaglayicisi
from syk_simulasyon.runtime_yaml import RuntimeYamlSaglayicisi


def _bos_baglanti_noktasi() -> int:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as soket:
        soket.bind(("127.0.0.1", 0))
        return int(soket.getsockname()[1])


def _uygulama_ve_servis():
    servis = RuntimeServisi()

    gorunum = RuntimeAnlikGorunumSaglayicisi(
        RuntimeIzlemeSaglayicisi(servis)
    )

    disa_aktarim = RuntimeDisaAktarim(
        RuntimeJsonSaglayicisi(gorunum),
        RuntimeCsvSaglayicisi(gorunum),
        RuntimeHtmlSaglayicisi(gorunum),
        RuntimeMarkdownSaglayicisi(gorunum),
        RuntimeXmlSaglayicisi(gorunum),
        RuntimeYamlSaglayicisi(gorunum),
    )

    websocket_yayinci = RuntimeWebSocketYayincisi(
        gorunum,
        servis.durum.sistem_hazirlik_ozeti,
    )

    uygulama = RuntimeFastApiSunucusu(
        disa_aktarim,
        websocket_yayinci,
        servis.durum,
    ).olustur()

    return uygulama, servis


def _sunucuyu_bekle(
    adres: str,
    *,
    zaman_asimi: float = 10.0,
) -> None:
    son_hata: Exception | None = None
    bitis = time.monotonic() + zaman_asimi

    while time.monotonic() < bitis:
        try:
            yanit = httpx.get(
                f"{adres}/terminal",
                timeout=0.5,
            )

            if yanit.status_code == 200:
                return
        except Exception as hata:
            son_hata = hata

        time.sleep(0.05)

    raise RuntimeError(
        "Uvicorn test sunucusu zamanında hazır olmadı."
    ) from son_hata


@contextmanager
def _canli_sunucu() -> Iterator[
    tuple[str, RuntimeServisi]
]:
    uygulama, servis = _uygulama_ve_servis()
    baglanti_noktasi = _bos_baglanti_noktasi()

    ayar = uvicorn.Config(
        uygulama,
        host="127.0.0.1",
        port=baglanti_noktasi,
        log_level="error",
        access_log=False,
        lifespan="off",
    )

    sunucu = uvicorn.Server(ayar)
    sunucu.install_signal_handlers = lambda: None

    is_parcacigi = Thread(
        target=sunucu.run,
        name="sykasif-dsp-0009-uvicorn",
        daemon=True,
    )
    is_parcacigi.start()

    adres = f"http://127.0.0.1:{baglanti_noktasi}"

    try:
        _sunucuyu_bekle(adres)
        yield adres, servis
    finally:
        sunucu.should_exit = True
        is_parcacigi.join(timeout=10)

        if is_parcacigi.is_alive():
            sunucu.force_exit = True
            is_parcacigi.join(timeout=5)

        if is_parcacigi.is_alive():
            raise RuntimeError(
                "Uvicorn test sunucusu kapatılamadı."
            )


def _tanim_degeri(sayfa, baslik: str):
    return sayfa.locator(
        "#syk-cift-panel dt",
        has_text=baslik,
    ).locator("xpath=following-sibling::dd[1]")


def test_terminal_paneli_gercek_tarayıcıda_canli_guncellenir():
    sayfa_hatalari: list[str] = []
    konsol_hatalari: list[str] = []

    with _canli_sunucu() as (adres, servis):
        servis.durum.adimlari_guncelle(
            tamamlanan_adim=1,
            toplam_adim=4,
            aktif_modul="Başlangıç Aşaması",
        )
        servis.durum.durum_guncelle(
            durum=RuntimeDurumTuru.CALISIYOR,
        )

        for alan, deger in (
            ("terminal_arayuzu", 20),
            ("veri_akisi", 40),
            ("kayit_zinciri", 60),
            ("test_durumu", 80),
            ("disa_aktarim_hazirligi", 100),
        ):
            servis.durum.sistem_hazirlik_guncelle(
                alan,
                deger,
            )

        with sync_playwright() as playwright:
            tarayici = playwright.chromium.launch(
                headless=True
            )

            sayfa = tarayici.new_page()

            sayfa.on(
                "pageerror",
                lambda hata: sayfa_hatalari.append(
                    str(hata)
                ),
            )

            sayfa.on(
                "console",
                lambda mesaj: (
                    konsol_hatalari.append(mesaj.text)
                    if mesaj.type == "error"
                    else None
                ),
            )

            try:
                sayfa.goto(
                    f"{adres}/terminal",
                    wait_until="domcontentloaded",
                )

                websocket_karti = sayfa.locator(
                    ".kart",
                    has_text="WebSocket:",
                )

                websocket_karti.wait_for(
                    state="visible",
                    timeout=5000,
                )

                sayfa.wait_for_function(
                    """() => {
                        const kartlar = Array.from(
                            document.querySelectorAll(".kart")
                        );

                        const kart = kartlar.find(
                            (oge) => oge.textContent.includes(
                                "WebSocket:"
                            )
                        );

                        return (
                            kart &&
                            kart.textContent.includes("BAĞLI")
                        );
                    }""",
                    timeout=5000,
                )

                aktif_adim = _tanim_degeri(
                    sayfa,
                    "Aktif Adım",
                )
                calisma_durumu = _tanim_degeri(
                    sayfa,
                    "Çalışma Durumu",
                )
                genel_ilerleme = _tanim_degeri(
                    sayfa,
                    "Genel İlerleme",
                )

                aktif_adim.wait_for(
                    state="visible",
                    timeout=5000,
                )

                assert aktif_adim.text_content() == (
                    "Başlangıç Aşaması"
                )
                assert calisma_durumu.text_content() == (
                    "çalışıyor"
                )
                assert genel_ilerleme.text_content() == "%25"

                assert _tanim_degeri(
                    sayfa,
                    "Terminal Arayüzü",
                ).text_content() == "%20"
                assert _tanim_degeri(
                    sayfa,
                    "Veri Akışı",
                ).text_content() == "%40"
                assert _tanim_degeri(
                    sayfa,
                    "Kayıt Zinciri",
                ).text_content() == "%60"
                assert _tanim_degeri(
                    sayfa,
                    "Test Durumu",
                ).text_content() == "%80"
                assert _tanim_degeri(
                    sayfa,
                    "Dışa Aktarım Hazırlığı",
                ).text_content() == "%100"
                assert _tanim_degeri(
                    sayfa,
                    "Üretime Hazırlık",
                ).text_content() == "%60"

                servis.durum.adimlari_guncelle(
                    tamamlanan_adim=3,
                    toplam_adim=4,
                    aktif_modul="Canlı Sinyal İşleme",
                )

                for alan, deger in (
                    ("terminal_arayuzu", 100),
                    ("veri_akisi", 90),
                    ("kayit_zinciri", 80),
                    ("test_durumu", 70),
                    ("disa_aktarim_hazirligi", 60),
                ):
                    servis.durum.sistem_hazirlik_guncelle(
                        alan,
                        deger,
                    )

                sayfa.wait_for_function(
                    """() => {
                        const basliklar = Array.from(
                            document.querySelectorAll(
                                "#syk-cift-panel dt"
                            )
                        );

                        const deger = (etiket) => {
                            const baslik = basliklar.find(
                                (oge) => (
                                    oge.textContent.trim()
                                    === etiket
                                )
                            );

                            return (
                                baslik &&
                                baslik.nextElementSibling
                                ? baslik.nextElementSibling
                                    .textContent.trim()
                                : null
                            );
                        };

                        return (
                            deger("Aktif Adım")
                                === "Canlı Sinyal İşleme"
                            &&
                            deger("Genel İlerleme")
                                === "%75"
                            &&
                            deger("Terminal Arayüzü")
                                === "%100"
                            &&
                            deger("Veri Akışı")
                                === "%90"
                            &&
                            deger("Üretime Hazırlık")
                                === "%80"
                        );
                    }""",
                    timeout=7000,
                )

                assert aktif_adim.text_content() == (
                    "Canlı Sinyal İşleme"
                )
                assert genel_ilerleme.text_content() == "%75"

                assert _tanim_degeri(
                    sayfa,
                    "Terminal Arayüzü",
                ).text_content() == "%100"
                assert _tanim_degeri(
                    sayfa,
                    "Veri Akışı",
                ).text_content() == "%90"
                assert _tanim_degeri(
                    sayfa,
                    "Kayıt Zinciri",
                ).text_content() == "%80"
                assert _tanim_degeri(
                    sayfa,
                    "Test Durumu",
                ).text_content() == "%70"
                assert _tanim_degeri(
                    sayfa,
                    "Dışa Aktarım Hazırlığı",
                ).text_content() == "%60"
                assert _tanim_degeri(
                    sayfa,
                    "Üretime Hazırlık",
                ).text_content() == "%80"

                assert sayfa_hatalari == []
                assert konsol_hatalari == []
            finally:
                tarayici.close()

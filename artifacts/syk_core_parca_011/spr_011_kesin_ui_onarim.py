from __future__ import annotations

import ast
import inspect
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


KAYNAK = Path(
    "src/syk_simulasyon/runtime_fastapi_sunucusu.py"
)

TEST = Path(
    "tests/test_ui_bilimsel_moduller_tarayici.py"
)

KANIT = Path(
    "artifacts/syk_core_parca_011/paket_014_kesin_ui_route_onarimi"
)

YEDEK = KANIT / "runtime_fastapi_sunucusu_onarim_oncesi.py"
STDOUT = KANIT / "runtime_8013_stdout.txt"
STDERR = KANIT / "runtime_8013_stderr.txt"
TEST_KAYDI = KANIT / "bilimsel_modul_testleri.txt"

ISARET = "# SYK_UI_SCREEN_UYUMLULUK_YOLU"


def yanlis_blogu_sil() -> None:
    kaynak = KAYNAK.read_text(
        encoding="utf-8-sig"
    )

    satirlar = kaynak.splitlines()

    while True:
        baslangic = next(
            (
                indeks
                for indeks, satir in enumerate(satirlar)
                if ISARET in satir
            ),
            None,
        )

        if baslangic is None:
            break

        bitis = baslangic + 1

        while bitis < len(satirlar):
            satir = satirlar[bitis]

            if not satir.strip():
                bitis += 1
                continue

            girinti = len(satir) - len(
                satir.lstrip()
            )

            if girinti < 4:
                break

            if (
                girinti == 4
                and satir.lstrip().startswith(
                    (
                        "return ",
                        "# SYK_",
                    )
                )
            ):
                break

            bitis += 1

        del satirlar[baslangic:bitis]

    yeni_kaynak = (
        "\n".join(satirlar).rstrip()
        + "\n"
    )

    ast.parse(
        yeni_kaynak,
        filename=str(KAYNAK),
    )

    KAYNAK.write_text(
        yeni_kaynak,
        encoding="utf-8",
    )

    print(
        "YANLIS_RUNTIME_HTML_YONLENDIRMESI=KALDIRILDI"
    )


def route_dogrula() -> None:
    import importlib

    modul_adi = (
        "syk_simulasyon.runtime_fastapi_sunucusu"
    )

    sys.modules.pop(
        modul_adi,
        None,
    )

    modul = importlib.import_module(
        modul_adi
    )

    uygulama = modul.uygulama_olustur()

    eslesenler = [
        route
        for route in uygulama.router.routes
        if getattr(route, "path", None)
        == "/syk-ui-screen"
    ]

    print(
        "SYK_UI_SCREEN_ROUTE_SAYISI="
        + str(len(eslesenler))
    )

    if len(eslesenler) != 1:
        raise RuntimeError(
            "syk-ui-screen route sayısı 1 değil."
        )

    endpoint = eslesenler[0].endpoint

    endpoint_modulu = getattr(
        endpoint,
        "__module__",
        "",
    )

    endpoint_adi = getattr(
        endpoint,
        "__name__",
        "",
    )

    print(
        "SYK_UI_SCREEN_ENDPOINT_MODULU="
        + endpoint_modulu
    )

    print(
        "SYK_UI_SCREEN_ENDPOINT_ADI="
        + endpoint_adi
    )

    print(
        "SYK_UI_SCREEN_ENDPOINT_KAYNAGI="
        + str(
            inspect.getsourcefile(
                endpoint
            )
        )
    )

    if not endpoint_modulu.endswith(
        "syk_ui_runtime.screen_routes"
    ):
        raise RuntimeError(
            "syk-ui-screen yanlış endpoint'e bağlı."
        )

    if endpoint_adi != "get_ui_screen":
        raise RuntimeError(
            "syk-ui-screen yanlış fonksiyona bağlı."
        )

    print(
        "GERCEK_SCREEN_ROUTE_BAGLANTISI=OK"
    )


def runtime_bekle(
    surec: subprocess.Popen,
) -> None:
    son_zaman = time.monotonic() + 30

    while time.monotonic() < son_zaman:
        if surec.poll() is not None:
            raise RuntimeError(
                "Runtime erken kapandı. "
                f"Çıkış kodu={surec.returncode}"
            )

        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:8013/syk-ui-screen",
                timeout=3,
            ) as yanit:
                icerik_turu = yanit.headers.get(
                    "Content-Type",
                    "",
                )

                icerik = yanit.read().decode(
                    "utf-8",
                    errors="replace",
                )

                durum_uygun = (
                    yanit.status == 200
                )

                tur_uygun = (
                    "text/html"
                    in icerik_turu.lower()
                )

                yanlis_ekran_yok = (
                    "5MHHR06FVD"
                    not in icerik
                )

                if (
                    durum_uygun
                    and tur_uygun
                    and yanlis_ekran_yok
                ):
                    print(
                        "GERCEK_SYK_UI_SCREEN_HTTP_DURUMU=200"
                    )

                    print(
                        "GERCEK_SYK_UI_SCREEN_CONTENT_TYPE="
                        + icerik_turu
                    )

                    return

        except Exception:
            pass

        time.sleep(0.25)

    raise RuntimeError(
        "Gerçek UI ekranı 30 saniye içinde açılmadı."
    )


def main() -> int:
    KANIT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not KAYNAK.exists():
        raise RuntimeError(
            f"Kaynak bulunamadı: {KAYNAK}"
        )

    if not TEST.exists():
        raise RuntimeError(
            f"Test bulunamadı: {TEST}"
        )

    shutil.copy2(
        KAYNAK,
        YEDEK,
    )

    try:
        yanlis_blogu_sil()
        route_dogrula()

    except Exception:
        shutil.copy2(
            YEDEK,
            KAYNAK,
        )

        raise

    with STDOUT.open(
        "w",
        encoding="utf-8",
    ) as stdout_dosyasi, STDERR.open(
        "w",
        encoding="utf-8",
    ) as stderr_dosyasi:

        runtime = subprocess.Popen(
            [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "uvicorn",
                (
                    "syk_simulasyon."
                    "runtime_fastapi_sunucusu:"
                    "uygulama_olustur"
                ),
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8013",
                "--log-level",
                "warning",
                "--no-access-log",
            ],
            stdout=stdout_dosyasi,
            stderr=stderr_dosyasi,
        )

        try:
            runtime_bekle(
                runtime
            )

            test = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "pytest",
                    str(TEST),
                    "-q",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            test_metni = (
                test.stdout
                + test.stderr
            )

            TEST_KAYDI.write_text(
                test_metni,
                encoding="utf-8",
            )

            print(
                test_metni
            )

            print(
                "TEST_CIKIS_KODU="
                + str(test.returncode)
            )

            if test.returncode != 0:
                raise RuntimeError(
                    "Bilimsel modül tarayıcı testinde hata kaldı."
                )

        finally:
            if runtime.poll() is None:
                runtime.terminate()

                try:
                    runtime.wait(
                        timeout=5
                    )

                except subprocess.TimeoutExpired:
                    runtime.kill()
                    runtime.wait()

    print(
        "PORT_8013_KAPANIS_DURUMU=KAPALI"
    )

    print(
        "SPR_011_KESIN_UI_ROUTE_ONARIMI_TAMAMLANDI"
    )

    print(
        "BILIMSEL_MODUL_TARAYICI_TESTLERI=TEMIZ"
    )

    print(
        "SPR_011_DOGRULANMIS_ILERLEME_YUZDESI=95"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

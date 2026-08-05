from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


HOST = "127.0.0.1"
PORT = 8013
BASE_URL = f"http://{HOST}:{PORT}"

SONUC = Path(
    "artifacts/syk_core_parca_011/"
    "paket_007_canli_http/"
    "ugr_8013_canli_sonuc.json"
)

RUNTIME_LOG = Path(
    "artifacts/syk_core_parca_011/"
    "paket_007_canli_http/"
    "runtime_8013.log"
)


def port_acik_mi() -> bool:
    with socket.socket() as soket:
        soket.settimeout(0.2)
        return soket.connect_ex((HOST, PORT)) == 0


def istek(
    yontem: str,
    yol: str,
    veri: dict | None = None,
) -> dict:
    govde = None
    basliklar = {}

    if veri is not None:
        govde = json.dumps(
            veri,
            ensure_ascii=False,
        ).encode("utf-8")

        basliklar["Content-Type"] = "application/json"

    istek_nesnesi = Request(
        BASE_URL + yol,
        data=govde,
        headers=basliklar,
        method=yontem,
    )

    baslangic = time.perf_counter()

    try:
        with urlopen(
            istek_nesnesi,
            timeout=15,
        ) as yanit:
            icerik = yanit.read()
            durum = yanit.status
            icerik_turu = yanit.headers.get(
                "Content-Type",
                "",
            )

    except HTTPError as hata:
        icerik = hata.read()
        durum = hata.code
        icerik_turu = hata.headers.get(
            "Content-Type",
            "",
        )

    sure_ms = (
        time.perf_counter() - baslangic
    ) * 1000

    metin = icerik.decode(
        "utf-8",
        errors="replace",
    )

    json_verisi = None

    if "json" in icerik_turu.lower():
        try:
            json_verisi = json.loads(metin)
        except json.JSONDecodeError:
            pass

    return {
        "yontem": yontem,
        "yol": yol,
        "durum": durum,
        "sure_ms": round(sure_ms, 3),
        "icerik_turu": icerik_turu,
        "json": json_verisi,
        "metin_ilk_300": metin[:300],
    }


def main() -> int:
    if port_acik_mi():
        raise RuntimeError(
            "8013 portu doğrulama öncesinde kullanımda."
        )

    RUNTIME_LOG.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RUNTIME_LOG.open(
        "w",
        encoding="utf-8",
    ) as log:
        surec = subprocess.Popen(
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
                HOST,
                "--port",
                str(PORT),
                "--log-level",
                "info",
                "--no-access-log",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        try:
            son_zaman = time.monotonic() + 20

            while time.monotonic() < son_zaman:
                if surec.poll() is not None:
                    raise RuntimeError(
                        "Runtime 8013 port açılmadan kapandı."
                    )

                if port_acik_mi():
                    break

                time.sleep(0.15)
            else:
                raise RuntimeError(
                    "Runtime 8013 zamanında açılmadı."
                )

            kontroller = [
                istek(
                    "GET",
                    "/openapi.json",
                ),
                istek(
                    "GET",
                    "/api/ugr/health",
                ),
                istek(
                    "GET",
                    "/api/ugr/snapshot",
                ),
                istek(
                    "GET",
                    "/api/ugr/preview",
                ),
                istek(
                    "GET",
                    (
                        "/api/ugr/assets/"
                        "web/static/css/"
                        "ugr_dynamic_icons.css"
                    ),
                ),
                istek(
                    "GET",
                    (
                        "/api/ugr/assets/"
                        "web/static/js/"
                        "ugr_dynamic_icons.js"
                    ),
                ),
                istek(
                    "POST",
                    "/api/ugr/icons/sys-001/state",
                    {
                        "durum": "calisiyor",
                        "neden": "Runtime 8013 canlı doğrulaması",
                        "zorla": True,
                    },
                ),
                istek(
                    "POST",
                    "/api/ugr/icons/bulk/state",
                    {
                        "ikon_kimlikleri": [
                            "sys-001",
                            "sys-002",
                            "sys-003",
                        ],
                        "durum": "uyari",
                        "neden": "Toplu canlı doğrulama",
                        "zorla": True,
                    },
                ),
            ]

            basarisizlar = [
                kontrol
                for kontrol in kontroller
                if kontrol["durum"] != 200
            ]

            openapi = kontroller[0]["json"]

            if not isinstance(openapi, dict):
                raise RuntimeError(
                    "OpenAPI yanıtı geçerli JSON değil."
                )

            ugr_yollari = sorted(
                yol
                for yol in openapi.get(
                    "paths",
                    {},
                )
                if yol.startswith("/api/ugr")
            )

            if len(ugr_yollari) < 13:
                raise RuntimeError(
                    "Canlı OpenAPI içinde 13 UGR rotası doğrulanamadı."
                )

            if basarisizlar:
                ayrinti = ", ".join(
                    (
                        f"{kayit['yontem']} "
                        f"{kayit['yol']}="
                        f"{kayit['durum']}"
                    )
                    for kayit in basarisizlar
                )

                raise RuntimeError(
                    "Başarısız canlı denetimler: "
                    + ayrinti
                )

            sonuc = {
                "runtime": (
                    "syk_simulasyon."
                    "runtime_fastapi_sunucusu:"
                    "uygulama_olustur"
                ),
                "factory": True,
                "port": PORT,
                "toplam_denetim": len(kontroller),
                "basarili_denetim": len(kontroller),
                "basarisiz_denetim": 0,
                "ugr_route_sayisi": len(ugr_yollari),
                "ugr_yollari": ugr_yollari,
                "kontroller": kontroller,
                "durum": "basarili",
            }

            SONUC.write_text(
                json.dumps(
                    sonuc,
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            print("UGR_8013_CANLI_DOGRULAMA_TAMAMLANDI")
            print(
                "UGR_ROUTE_SAYISI="
                + str(len(ugr_yollari))
            )
            print(
                "TOPLAM_DENETIM="
                + str(len(kontroller))
            )
            print("BASARISIZ_DENETIM=0")

            return 0

        finally:
            if surec.poll() is None:
                surec.terminate()

                try:
                    surec.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    surec.kill()
                    surec.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import httpx


HOST = "127.0.0.1"
PORT = 8013
BASE_URL = f"http://{HOST}:{PORT}"

MODULE_NAME = (
    "syk_simulasyon."
    "runtime_ui_sunucusu"
)

SOURCE_PATH = Path(
    "src/syk_simulasyon/runtime_ui_sunucusu.py"
)


def dotted_name(
    node: ast.AST,
) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(
            node.value
        )

        if parent:
            return (
                f"{parent}.{node.attr}"
            )

        return node.attr

    if isinstance(node, ast.Call):
        return dotted_name(
            node.func
        )

    return None


def port_acik_mi(
    host: str,
    port: int,
    *,
    timeout: float = 0.25,
) -> bool:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as soket:
        soket.settimeout(
            timeout
        )

        return (
            soket.connect_ex(
                (host, port)
            )
            == 0
        )


def port_bekle(
    process: subprocess.Popen[str],
    *,
    timeout: float = 15.0,
) -> None:
    son_zaman = (
        time.monotonic()
        + timeout
    )

    while (
        time.monotonic()
        < son_zaman
    ):
        if process.poll() is not None:
            raise RuntimeError(
                "Uvicorn port açılmadan kapandı. "
                f"CIKIS_KODU={process.returncode}"
            )

        if port_acik_mi(
            HOST,
            PORT,
        ):
            return

        time.sleep(
            0.10
        )

    raise TimeoutError(
        "Runtime 8013 portu açılamadı."
    )


def process_durdur(
    process: subprocess.Popen[str],
) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(
                signal.CTRL_BREAK_EVENT
            )
        else:
            process.send_signal(
                signal.SIGINT
            )

        process.wait(
            timeout=5.0
        )

    except Exception:
        if process.poll() is None:
            process.terminate()

        try:
            process.wait(
                timeout=3.0
            )
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(
                timeout=3.0
            )


def kaynak_ast_incele() -> dict[str, Any]:
    kaynak = SOURCE_PATH.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(
        kaynak,
        filename=str(
            SOURCE_PATH
        ),
    )

    atamalar: list[
        dict[str, Any]
    ] = []

    fonksiyonlar: list[
        dict[str, Any]
    ] = []

    include_router_cagrilari: list[
        dict[str, Any]
    ] = []

    fastapi_cagrilari: list[
        dict[str, Any]
    ] = []

    importlar: list[
        dict[str, Any]
    ] = []

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Import,
        ):
            importlar.append(
                {
                    "satir": node.lineno,
                    "tur": "import",
                    "moduller": [
                        alias.name
                        for alias
                        in node.names
                    ],
                }
            )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            importlar.append(
                {
                    "satir": node.lineno,
                    "tur": "from",
                    "modul": (
                        node.module
                    ),
                    "adlar": [
                        alias.name
                        for alias
                        in node.names
                    ],
                }
            )

        elif isinstance(
            node,
            ast.Assign,
        ):
            hedefler = [
                dotted_name(
                    hedef
                )
                or ast.unparse(
                    hedef
                )
                for hedef
                in node.targets
            ]

            deger = ast.unparse(
                node.value
            )

            atamalar.append(
                {
                    "satir": node.lineno,
                    "hedefler": hedefler,
                    "deger": deger,
                }
            )

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            fonksiyonlar.append(
                {
                    "satir": node.lineno,
                    "bitis": getattr(
                        node,
                        "end_lineno",
                        None,
                    ),
                    "ad": node.name,
                    "async": isinstance(
                        node,
                        ast.AsyncFunctionDef,
                    ),
                    "imza": ast.unparse(
                        node
                    ).splitlines()[0],
                }
            )

        elif isinstance(
            node,
            ast.Call,
        ):
            cagri_adi = dotted_name(
                node.func
            )

            if not cagri_adi:
                continue

            if cagri_adi.endswith(
                "include_router"
            ):
                include_router_cagrilari.append(
                    {
                        "satir": node.lineno,
                        "bitis": getattr(
                            node,
                            "end_lineno",
                            node.lineno,
                        ),
                        "cagri": cagri_adi,
                        "alici": (
                            ast.unparse(
                                node.func.value
                            )
                            if isinstance(
                                node.func,
                                ast.Attribute,
                            )
                            else None
                        ),
                        "argumanlar": [
                            ast.unparse(
                                arguman
                            )
                            for arguman
                            in node.args
                        ],
                        "anahtarlar": {
                            anahtar.arg
                            or "**":
                                ast.unparse(
                                    anahtar.value
                                )
                            for anahtar
                            in node.keywords
                        },
                    }
                )

            if (
                cagri_adi
                .rsplit(
                    ".",
                    1,
                )[-1]
                == "FastAPI"
            ):
                fastapi_cagrilari.append(
                    {
                        "satir": node.lineno,
                        "cagri": cagri_adi,
                        "argumanlar": [
                            ast.unparse(
                                arguman
                            )
                            for arguman
                            in node.args
                        ],
                        "anahtarlar": {
                            anahtar.arg
                            or "**":
                                ast.unparse(
                                    anahtar.value
                                )
                            for anahtar
                            in node.keywords
                        },
                    }
                )

    return {
        "kaynak": (
            SOURCE_PATH.as_posix()
        ),
        "satir_sayisi": len(
            kaynak.splitlines()
        ),
        "atamalar": atamalar,
        "fonksiyonlar": (
            fonksiyonlar
        ),
        "include_router_cagrilari": (
            include_router_cagrilari
        ),
        "fastapi_cagrilari": (
            fastapi_cagrilari
        ),
        "importlar": importlar,
        "ugr_import_isareti": (
            "SYK_UGR_RUNTIME_ROUTER_IMPORT"
            in kaynak
        ),
        "ugr_include_isareti": (
            "SYK_UGR_RUNTIME_ROUTER_BAGLANTISI"
            in kaynak
        ),
        "syk_ugr_router_geciyor": (
            "syk_ugr_router"
            in kaynak
        ),
    }


def nesne_bilgisi(
    ad: str,
    nesne: Any,
) -> dict[str, Any]:
    """Modül adayını güvenli biçimde inceler.

    Sınıf seviyesindeki ``property`` tanımları, descriptor nesneleri,
    modüller ve gerçeklenmemiş route özellikleri gerçek FastAPI/Starlette
    uygulaması olarak değerlendirilmez.
    """

    import inspect
    from collections.abc import Iterable
    from types import ModuleType

    tur = type(
        nesne
    )

    tur_adi = (
        f"{tur.__module__}."
        f"{tur.__qualname__}"
    )

    bilgi: dict[str, Any] = {
        "ad": ad,
        "tur": tur_adi,
        "callable": callable(
            nesne
        ),
        "modul": getattr(
            nesne,
            "__module__",
            None,
        ),
        "sinif_mi": inspect.isclass(
            nesne
        ),
        "modul_nesnesi_mi": isinstance(
            nesne,
            ModuleType,
        ),
        "property_nesnesi_mi": isinstance(
            nesne,
            property,
        ),
    }

    try:
        bilgi["imza"] = str(
            inspect.signature(
                nesne
            )
        )
    except Exception as hata:
        bilgi["imza"] = None
        bilgi["imza_hatasi"] = (
            f"{type(hata).__name__}: {hata}"
        )

    if (
        inspect.isclass(
            nesne
        )
        or isinstance(
            nesne,
            ModuleType,
        )
        or isinstance(
            nesne,
            property,
        )
    ):
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = []
        bilgi["routes_durumu"] = (
            "uygulama_nesnesi_degil"
        )

        return bilgi

    routes: Any = None

    try:
        routes = getattr(
            nesne,
            "routes",
            None,
        )
    except Exception as hata:
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = []
        bilgi["routes_durumu"] = (
            "routes_okuma_hatasi"
        )
        bilgi["routes_hatasi"] = (
            f"{type(hata).__name__}: {hata}"
        )

        return bilgi

    if isinstance(
        routes,
        property,
    ):
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = []
        bilgi["routes_durumu"] = (
            "property_routes"
        )

        return bilgi

    if routes is None:
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = []
        bilgi["routes_durumu"] = (
            "routes_yok"
        )

        return bilgi

    if isinstance(
        routes,
        (
            str,
            bytes,
            dict,
        ),
    ):
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = []
        bilgi["routes_durumu"] = (
            "gecersiz_routes_turu"
        )
        bilgi["routes_turu"] = (
            f"{type(routes).__module__}."
            f"{type(routes).__qualname__}"
        )

        return bilgi

    try:
        iterator = iter(
            routes
        )
    except TypeError:
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = []
        bilgi["routes_durumu"] = (
            "routes_dolasilabilir_degil"
        )
        bilgi["routes_turu"] = (
            f"{type(routes).__module__}."
            f"{type(routes).__qualname__}"
        )

        return bilgi

    route_kayitlari: list[
        dict[str, Any]
    ] = []

    route_hatalari: list[
        dict[str, Any]
    ] = []

    try:
        for indeks, route in enumerate(
            iterator
        ):
            try:
                yol = getattr(
                    route,
                    "path",
                    None,
                )

                ad_degeri = getattr(
                    route,
                    "name",
                    None,
                )

                methods_raw = getattr(
                    route,
                    "methods",
                    None,
                )

                if methods_raw is None:
                    methods: list[str] = []
                else:
                    try:
                        methods = sorted(
                            str(method)
                            for method
                            in methods_raw
                        )
                    except TypeError:
                        methods = [
                            str(
                                methods_raw
                            )
                        ]

                route_kayitlari.append(
                    {
                        "indeks": indeks,
                        "path": yol,
                        "name": ad_degeri,
                        "methods": methods,
                        "tur": (
                            f"{type(route).__module__}."
                            f"{type(route).__qualname__}"
                        ),
                    }
                )

            except Exception as hata:
                route_hatalari.append(
                    {
                        "indeks": indeks,
                        "hata_turu": (
                            type(hata).__name__
                        ),
                        "hata": str(
                            hata
                        ),
                    }
                )

    except Exception as hata:
        bilgi["route_sayisi"] = None
        bilgi["ugr_route_sayisi"] = 0
        bilgi["routes"] = route_kayitlari
        bilgi["route_hatalari"] = (
            route_hatalari
        )
        bilgi["routes_durumu"] = (
            "routes_dolasim_hatasi"
        )
        bilgi["routes_hatasi"] = (
            f"{type(hata).__name__}: {hata}"
        )

        return bilgi

    bilgi["route_sayisi"] = len(
        route_kayitlari
    )

    bilgi["routes"] = (
        route_kayitlari
    )

    bilgi["route_hatalari"] = (
        route_hatalari
    )

    bilgi["ugr_route_sayisi"] = sum(
        1
        for route
        in route_kayitlari
        if (
            isinstance(
                route.get(
                    "path"
                ),
                str,
            )
            and route[
                "path"
            ].startswith(
                "/api/ugr"
            )
        )
    )

    bilgi["routes_durumu"] = (
        "routes_okundu"
    )

    return bilgi


def modul_runtime_incele() -> dict[str, Any]:
    modul = importlib.import_module(
        MODULE_NAME
    )

    aday_adlar = [
        ad
        for ad in dir(
            modul
        )
        if not ad.startswith(
            "__"
        )
    ]

    nesneler: list[
        dict[str, Any]
    ] = []

    for ad in aday_adlar:
        try:
            nesne = getattr(
                modul,
                ad
            )
        except Exception:
            continue

        tur_adi = (
            f"{type(nesne).__module__}."
            f"{type(nesne).__qualname__}"
        )

        ilgi = (
            hasattr(
                nesne,
                "routes",
            )
            or "fastapi"
            in tur_adi.lower()
            or "starlette"
            in tur_adi.lower()
            or ad.lower()
            in {
                "app",
                "uygulama",
                "application",
                "api",
                "create_app",
                "app_factory",
                "uygulama_uret",
                "uygulama_olustur",
            }
        )

        if not ilgi:
            continue

        nesneler.append(
            nesne_bilgisi(
                ad,
                nesne,
            )
        )

    return {
        "modul": MODULE_NAME,
        "dosya": getattr(
            modul,
            "__file__",
            None,
        ),
        "aday_nesneler": (
            nesneler
        ),
    }


def uvicorn_adaylari_uret(
    runtime_bilgisi: dict[str, Any],
) -> list[dict[str, Any]]:
    adaylar: list[
        dict[str, Any]
    ] = []

    for nesne in runtime_bilgisi[
        "aday_nesneler"
    ]:
        ad = nesne["ad"]

        if nesne.get(
            "route_sayisi"
        ) is not None:
            adaylar.append(
                {
                    "import": (
                        f"{MODULE_NAME}:{ad}"
                    ),
                    "factory": False,
                    "kaynak": (
                        "route_tasiyan_nesne"
                    ),
                }
            )

        elif (
            nesne["callable"]
            and (
                "app" in ad.lower()
                or "uygulama"
                in ad.lower()
                or "create" in ad.lower()
                or "olustur" in ad.lower()
                or "uret" in ad.lower()
            )
        ):
            adaylar.append(
                {
                    "import": (
                        f"{MODULE_NAME}:{ad}"
                    ),
                    "factory": True,
                    "kaynak": (
                        "uygulama_fabrikasi_adayi"
                    ),
                }
            )

    benzersiz: list[
        dict[str, Any]
    ] = []

    gorulen: set[
        tuple[str, bool]
    ] = set()

    for aday in adaylar:
        anahtar = (
            aday["import"],
            aday["factory"],
        )

        if anahtar in gorulen:
            continue

        gorulen.add(
            anahtar
        )

        benzersiz.append(
            aday
        )

    return benzersiz


def uvicorn_adayi_denetle(
    aday: dict[str, Any],
    *,
    stdout_path: Path,
    stderr_path: Path,
) -> dict[str, Any]:
    if port_acik_mi(
        HOST,
        PORT,
    ):
        raise RuntimeError(
            "8013 portu aday denetimi öncesinde dolu."
        )

    komut = [
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "uvicorn",
        aday["import"],
        "--host",
        HOST,
        "--port",
        str(PORT),
        "--log-level",
        "warning",
        "--no-access-log",
    ]

    if aday["factory"]:
        komut.append(
            "--factory"
        )

    creation_flags = 0

    if os.name == "nt":
        creation_flags = (
            subprocess
            .CREATE_NEW_PROCESS_GROUP
        )

    stdout_handle = stdout_path.open(
        "w",
        encoding="utf-8",
    )

    stderr_handle = stderr_path.open(
        "w",
        encoding="utf-8",
    )

    process: subprocess.Popen[
        str
    ] | None = None

    try:
        process = subprocess.Popen(
            komut,
            cwd=Path.cwd(),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            creationflags=(
                creation_flags
            ),
        )

        port_bekle(
            process,
            timeout=12.0,
        )

        with httpx.Client(
            base_url=BASE_URL,
            timeout=5.0,
            follow_redirects=True,
        ) as client:
            openapi_yanit = client.get(
                "/openapi.json"
            )

            health_yanit = client.get(
                "/api/ugr/health"
            )

            kok_yanit = client.get(
                "/"
            )

        openapi_json: Any = None

        try:
            openapi_json = (
                openapi_yanit.json()
            )
        except Exception:
            openapi_json = None

        openapi_yollari = []

        if isinstance(
            openapi_json,
            dict,
        ):
            openapi_yollari = sorted(
                (
                    openapi_json
                    .get(
                        "paths",
                        {},
                    )
                    .keys()
                )
            )

        ugr_yollari = [
            yol
            for yol
            in openapi_yollari
            if yol.startswith(
                "/api/ugr"
            )
        ]

        health_json: Any = None

        try:
            health_json = (
                health_yanit.json()
            )
        except Exception:
            health_json = None

        return {
            "import": aday[
                "import"
            ],
            "factory": aday[
                "factory"
            ],
            "kaynak": aday[
                "kaynak"
            ],
            "baslatildi": True,
            "openapi_durum_kodu": (
                openapi_yanit
                .status_code
            ),
            "openapi_icerik_turu": (
                openapi_yanit
                .headers
                .get(
                    "content-type"
                )
            ),
            "openapi_yol_sayisi": len(
                openapi_yollari
            ),
            "openapi_yollari": (
                openapi_yollari
            ),
            "ugr_yol_sayisi": len(
                ugr_yollari
            ),
            "ugr_yollari": ugr_yollari,
            "health_durum_kodu": (
                health_yanit
                .status_code
            ),
            "health_icerik_turu": (
                health_yanit
                .headers
                .get(
                    "content-type"
                )
            ),
            "health_json": (
                health_json
            ),
            "health_metin_ilk_500": (
                health_yanit.text[
                    :500
                ]
            ),
            "kok_durum_kodu": (
                kok_yanit.status_code
            ),
            "kok_icerik_turu": (
                kok_yanit
                .headers
                .get(
                    "content-type"
                )
            ),
            "stdout": (
                stdout_path.as_posix()
            ),
            "stderr": (
                stderr_path.as_posix()
            ),
            "ugr_canli": (
                health_yanit
                .status_code
                == 200
                and len(
                    ugr_yollari
                )
                >= 1
            ),
        }

    except Exception as hata:
        return {
            "import": aday[
                "import"
            ],
            "factory": aday[
                "factory"
            ],
            "kaynak": aday[
                "kaynak"
            ],
            "baslatildi": False,
            "hata_turu": (
                type(hata).__name__
            ),
            "hata": str(
                hata
            ),
            "stdout": (
                stdout_path.as_posix()
            ),
            "stderr": (
                stderr_path.as_posix()
            ),
            "ugr_canli": False,
        }

    finally:
        if process is not None:
            process_durdur(
                process
            )

        stdout_handle.close()
        stderr_handle.close()

        son_zaman = (
            time.monotonic()
            + 5.0
        )

        while (
            port_acik_mi(
                HOST,
                PORT,
            )
            and time.monotonic()
            < son_zaman
        ):
            time.sleep(
                0.10
            )


def metin_raporu(
    rapor: dict[str, Any],
) -> str:
    satirlar = [
        "SPR-011 PAKET-007",
        "RUNTIME 8013 APP VE ROUTE TESHIS RAPORU",
        "",
        (
            "KAYNAK="
            f"{rapor['kaynak_ast']['kaynak']}"
        ),
        (
            "MODUL="
            f"{rapor['runtime_modul']['modul']}"
        ),
        (
            "UVICORN_ADAY_SAYISI="
            f"{len(rapor['uvicorn_adaylari'])}"
        ),
        (
            "CANLI_UGR_ADAY_SAYISI="
            f"{rapor['canli_ugr_aday_sayisi']}"
        ),
        "",
        "KAYNAK_ISARETLERI:",
        (
            "UGR_IMPORT_ISARETI="
            f"{rapor['kaynak_ast']['ugr_import_isareti']}"
        ),
        (
            "UGR_INCLUDE_ISARETI="
            f"{rapor['kaynak_ast']['ugr_include_isareti']}"
        ),
        (
            "SYK_UGR_ROUTER_GECIYOR="
            f"{rapor['kaynak_ast']['syk_ugr_router_geciyor']}"
        ),
        "",
        "INCLUDE_ROUTER_CAGRILARI:",
    ]

    for cagri in rapor[
        "kaynak_ast"
    ][
        "include_router_cagrilari"
    ]:
        satirlar.append(
            json.dumps(
                cagri,
                ensure_ascii=False,
                sort_keys=True,
            )
        )

    satirlar.extend(
        [
            "",
            "RUNTIME_ADAY_NESNELERI:",
        ]
    )

    for nesne in rapor[
        "runtime_modul"
    ][
        "aday_nesneler"
    ]:
        satirlar.append(
            json.dumps(
                nesne,
                ensure_ascii=False,
                sort_keys=True,
            )
        )

    satirlar.extend(
        [
            "",
            "CANLI_UVICORN_DENETIMLERI:",
        ]
    )

    for denetim in rapor[
        "canli_denetimler"
    ]:
        satirlar.extend(
            [
                "-" * 88,
                (
                    "IMPORT="
                    f"{denetim['import']}"
                ),
                (
                    "FACTORY="
                    f"{denetim['factory']}"
                ),
                (
                    "BASLATILDI="
                    f"{denetim['baslatildi']}"
                ),
                (
                    "UGR_CANLI="
                    f"{denetim['ugr_canli']}"
                ),
                (
                    "OPENAPI_DURUM_KODU="
                    f"{denetim.get('openapi_durum_kodu')}"
                ),
                (
                    "HEALTH_DURUM_KODU="
                    f"{denetim.get('health_durum_kodu')}"
                ),
                (
                    "UGR_YOL_SAYISI="
                    f"{denetim.get('ugr_yol_sayisi')}"
                ),
                (
                    "UGR_YOLLARI="
                    + json.dumps(
                        denetim.get(
                            "ugr_yollari"
                        ),
                        ensure_ascii=False,
                    )
                ),
                (
                    "HEALTH_JSON="
                    + json.dumps(
                        denetim.get(
                            "health_json"
                        ),
                        ensure_ascii=False,
                    )
                ),
                (
                    "HATA="
                    f"{denetim.get('hata')}"
                ),
            ]
        )

    satirlar.extend(
        [
            "",
            "KARAR:",
        ]
    )

    if rapor[
        "canli_ugr_aday_sayisi"
    ] == 1:
        kazanan = next(
            denetim
            for denetim
            in rapor[
                "canli_denetimler"
            ]
            if denetim[
                "ugr_canli"
            ]
        )

        satirlar.extend(
            [
                (
                    "DOGRU_APP_IMPORT="
                    f"{kazanan['import']}"
                ),
                (
                    "DOGRU_FACTORY="
                    f"{kazanan['factory']}"
                ),
                (
                    "SONRAKI_ISLEM="
                    "PAKET_007_CANLI_DOGRULAMAYI_DOGRU_IMPORT_ILE_YENIDEN_CALISTIR"
                ),
            ]
        )

    elif rapor[
        "canli_ugr_aday_sayisi"
    ] == 0:
        satirlar.extend(
            [
                "DOGRU_APP_IMPORT=BULUNAMADI",
                (
                    "SONRAKI_ISLEM="
                    "UGR_INCLUDE_ROUTER_CALISAN_APP_FABRIKASINA_TASINACAK"
                ),
            ]
        )

    else:
        satirlar.extend(
            [
                "DOGRU_APP_IMPORT=BIRDEN_FAZLA_ADAY",
                (
                    "SONRAKI_ISLEM="
                    "ANA_RUNTIME_BASLATMA_SOZLESMESINE_GORE_TEK_ADAY_SECILECEK"
                ),
            ]
        )

    satirlar.append("")

    return "\n".join(
        satirlar
    )


def parser_uret() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-json",
        required=True,
    )

    parser.add_argument(
        "--output-text",
        required=True,
    )

    parser.add_argument(
        "--stdout",
        required=True,
    )

    parser.add_argument(
        "--stderr",
        required=True,
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parser_uret().parse_args(
        argv
    )

    output_json = Path(
        args.output_json
    )

    output_text = Path(
        args.output_text
    )

    stdout_base = Path(
        args.stdout
    )

    stderr_base = Path(
        args.stderr
    )

    output_json.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    kaynak_ast = (
        kaynak_ast_incele()
    )

    runtime_modul = (
        modul_runtime_incele()
    )

    uvicorn_adaylari = (
        uvicorn_adaylari_uret(
            runtime_modul
        )
    )

    canli_denetimler: list[
        dict[str, Any]
    ] = []

    for indeks, aday in enumerate(
        uvicorn_adaylari,
        start=1,
    ):
        stdout_path = (
            stdout_base.parent
            / (
                f"{stdout_base.stem}_"
                f"{indeks:02d}"
                f"{stdout_base.suffix}"
            )
        )

        stderr_path = (
            stderr_base.parent
            / (
                f"{stderr_base.stem}_"
                f"{indeks:02d}"
                f"{stderr_base.suffix}"
            )
        )

        canli_denetimler.append(
            uvicorn_adayi_denetle(
                aday,
                stdout_path=(
                    stdout_path
                ),
                stderr_path=(
                    stderr_path
                ),
            )
        )

    canli_ugr_adaylari = [
        denetim
        for denetim
        in canli_denetimler
        if denetim[
            "ugr_canli"
        ]
    ]

    rapor = {
        "sema": (
            "sykasif.runtime-8013."
            "app-route-diagnosis.v1"
        ),
        "kaynak_ast": (
            kaynak_ast
        ),
        "runtime_modul": (
            runtime_modul
        ),
        "uvicorn_adaylari": (
            uvicorn_adaylari
        ),
        "canli_denetimler": (
            canli_denetimler
        ),
        "canli_ugr_aday_sayisi": len(
            canli_ugr_adaylari
        ),
        "dogru_aday": (
            canli_ugr_adaylari[0]
            if len(
                canli_ugr_adaylari
            )
            == 1
            else None
        ),
    }

    output_json.write_text(
        json.dumps(
            rapor,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    output_text.write_text(
        metin_raporu(
            rapor
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "uvicorn_aday_sayisi": len(
                    uvicorn_adaylari
                ),
                "canli_ugr_aday_sayisi": len(
                    canli_ugr_adaylari
                ),
                "dogru_aday": (
                    canli_ugr_adaylari[
                        0
                    ][
                        "import"
                    ]
                    if len(
                        canli_ugr_adaylari
                    )
                    == 1
                    else None
                ),
                "dogru_factory": (
                    canli_ugr_adaylari[
                        0
                    ][
                        "factory"
                    ]
                    if len(
                        canli_ugr_adaylari
                    )
                    == 1
                    else None
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "RUNTIME_8013_APP_ROUTE_TESHISI_TAMAMLANDI"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

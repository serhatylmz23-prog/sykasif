from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(
    "artifacts/"
    "syk_core_parca_011/"
    "paket_007_runtime_8013_app_teshisi/"
    "runtime_8013_app_ve_route_teshis.py"
)

REPORT = Path(
    "artifacts/"
    "syk_core_parca_011/"
    "paket_007_runtime_8013_app_teshisi/"
    "NESNE_BILGISI_PROPERTY_ONARIM_RAPORU.txt"
)


YENI_FONKSIYON = r'''
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
'''.strip()


def fonksiyon_araligi(
    tree: ast.Module,
    fonksiyon_adi: str,
) -> tuple[int, int]:
    for node in tree.body:
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name
            == fonksiyon_adi
        ):
            baslangiclar = [
                node.lineno,
                *[
                    decorator.lineno
                    for decorator
                    in node.decorator_list
                ],
            ]

            baslangic = min(
                baslangiclar
            )

            bitis = int(
                getattr(
                    node,
                    "end_lineno",
                    node.lineno,
                )
            )

            return (
                baslangic,
                bitis,
            )

    raise RuntimeError(
        f"Fonksiyon bulunamadı: {fonksiyon_adi}"
    )


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(
            SOURCE
        )

    original = SOURCE.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(
        original,
        filename=str(
            SOURCE
        ),
    )

    baslangic, bitis = (
        fonksiyon_araligi(
            tree,
            "nesne_bilgisi",
        )
    )

    satirlar = (
        original.splitlines()
    )

    eski_fonksiyon = "\n".join(
        satirlar[
            baslangic - 1:
            bitis
        ]
    )

    yeni_satirlar = (
        satirlar[
            : baslangic - 1
        ]
        + YENI_FONKSIYON.splitlines()
        + satirlar[
            bitis:
        ]
    )

    updated = "\n".join(
        yeni_satirlar
    ) + "\n"

    ast.parse(
        updated,
        filename=str(
            SOURCE
        ),
    )

    SOURCE.write_text(
        updated,
        encoding="utf-8",
    )

    final = SOURCE.read_text(
        encoding="utf-8"
    )

    final_tree = ast.parse(
        final,
        filename=str(
            SOURCE
        ),
    )

    yeni_baslangic, yeni_bitis = (
        fonksiyon_araligi(
            final_tree,
            "nesne_bilgisi",
        )
    )

    if "property_routes" not in final:
        raise RuntimeError(
            "Property koruması kaynak dosyaya eklenemedi."
        )

    if "routes_dolasilabilir_degil" not in final:
        raise RuntimeError(
            "Iterable koruması kaynak dosyaya eklenemedi."
        )

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT.write_text(
        "\n".join(
            [
                "SPR-011 PAKET-007",
                "NESNE BILGISI PROPERTY ONARIM RAPORU",
                "",
                (
                    "KAYNAK="
                    f"{SOURCE.as_posix()}"
                ),
                (
                    "ESKI_FONKSIYON_BASLANGIC="
                    f"{baslangic}"
                ),
                (
                    "ESKI_FONKSIYON_BITIS="
                    f"{bitis}"
                ),
                (
                    "YENI_FONKSIYON_BASLANGIC="
                    f"{yeni_baslangic}"
                ),
                (
                    "YENI_FONKSIYON_BITIS="
                    f"{yeni_bitis}"
                ),
                (
                    "PROPERTY_KORUMASI="
                    "EKLENDI"
                ),
                (
                    "SINIF_KORUMASI="
                    "EKLENDI"
                ),
                (
                    "MODUL_KORUMASI="
                    "EKLENDI"
                ),
                (
                    "ITERABLE_KORUMASI="
                    "EKLENDI"
                ),
                (
                    "TEK_ADAY_HATASI_TUM_TESHISI_DURDURMA="
                    "ENGELLENDI"
                ),
                (
                    "ESKI_FONKSIYON_UZUNLUGU="
                    f"{len(eski_fonksiyon)}"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        "NESNE_BILGISI_PROPERTY_ONARIMI_TAMAMLANDI"
    )
    print(
        f"ESKI_ARALIK={baslangic}-{bitis}"
    )
    print(
        f"YENI_ARALIK={yeni_baslangic}-{yeni_bitis}"
    )
    print(
        "PROPERTY_KORUMASI=HAZIR"
    )
    print(
        "ITERABLE_KORUMASI=HAZIR"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

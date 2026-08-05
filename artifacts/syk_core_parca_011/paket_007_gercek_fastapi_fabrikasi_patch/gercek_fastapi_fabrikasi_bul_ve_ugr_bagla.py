from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence


ROOT = Path.cwd()

SOURCE_ROOT = (
    ROOT
    / "src"
    / "syk_simulasyon"
)

REPORT_JSON = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_007_gercek_fastapi_fabrikasi_patch"
    / "GERCEK_FASTAPI_FABRIKASI_PATCH_RAPORU.json"
)

REPORT_TEXT = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_007_gercek_fastapi_fabrikasi_patch"
    / "GERCEK_FASTAPI_FABRIKASI_PATCH_RAPORU.txt"
)

BACKUP_ROOT = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_007_gercek_fastapi_fabrikasi_patch"
    / "yedekler"
)

IMPORT_MARKER = (
    "# SYK_UGR_GERCEK_FASTAPI_ROUTER_IMPORT"
)

CONNECTION_MARKER = (
    "# SYK_UGR_GERCEK_FASTAPI_ROUTER_BAGLANTISI"
)

IMPORT_BLOCK = """\
# SYK_UGR_GERCEK_FASTAPI_ROUTER_IMPORT
from syk_simulasyon.syk_ui_runtime.ugr_runtime_routes import (
    ugr_router as syk_ugr_router,
)
"""


@dataclass(slots=True)
class FastApiAdayi:
    dosya: str
    modul: str
    tur: str
    nesne_adi: str
    fonksiyon_adi: str | None
    fastapi_satiri: int
    fastapi_bitis_satiri: int
    uygulama_ifadesi: str
    uygulama_degiskeni: str | None
    return_satiri: int | None
    include_router_sayisi: int
    mevcut_ugr_baglantisi: bool
    puan: int = 0
    gerekceler: list[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class PatchSonucu:
    dosya: str
    modul: str
    import_nesnesi: str
    factory: bool
    uygulama_degiskeni: str
    fonksiyon_adi: str | None
    import_eklendi: bool
    router_baglantisi_eklendi: bool
    yedek: str
    aday_puani: int


def dotted_name(
    node: ast.AST,
) -> str | None:
    if isinstance(
        node,
        ast.Name,
    ):
        return node.id

    if isinstance(
        node,
        ast.Attribute,
    ):
        parent = dotted_name(
            node.value
        )

        if parent:
            return (
                f"{parent}.{node.attr}"
            )

        return node.attr

    if isinstance(
        node,
        ast.Call,
    ):
        return dotted_name(
            node.func
        )

    return None


def module_name_for_path(
    path: Path,
) -> str:
    relative = path.relative_to(
        ROOT / "src"
    )

    parts = list(
        relative.with_suffix(
            ""
        ).parts
    )

    if parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(
        parts
    )


def fastapi_call_mi(
    node: ast.AST,
) -> bool:
    if not isinstance(
        node,
        ast.Call,
    ):
        return False

    name = dotted_name(
        node.func
    )

    if not name:
        return False

    return (
        name.rsplit(
            ".",
            1,
        )[-1]
        == "FastAPI"
    )


def include_router_calls(
    node: ast.AST,
) -> list[ast.Call]:
    calls: list[
        ast.Call
    ] = []

    for child in ast.walk(
        node
    ):
        if not isinstance(
            child,
            ast.Call,
        ):
            continue

        if not isinstance(
            child.func,
            ast.Attribute,
        ):
            continue

        if (
            child.func.attr
            != "include_router"
        ):
            continue

        calls.append(
            child
        )

    return calls


def includes_ugr_router(
    node: ast.AST,
) -> bool:
    for call in include_router_calls(
        node
    ):
        for argument in call.args:
            text = ast.unparse(
                argument
            )

            if (
                "syk_ugr_router"
                in text
                or "ugr_router"
                in text
            ):
                return True

    return False


def assignment_targets(
    node: ast.Assign | ast.AnnAssign,
) -> list[str]:
    if isinstance(
        node,
        ast.Assign,
    ):
        targets = node.targets
    else:
        targets = [
            node.target
        ]

    result: list[
        str
    ] = []

    for target in targets:
        if isinstance(
            target,
            ast.Name,
        ):
            result.append(
                target.id
            )
        else:
            result.append(
                ast.unparse(
                    target
                )
            )

    return result


def function_return_lines(
    function: (
        ast.FunctionDef
        | ast.AsyncFunctionDef
    ),
    variable_name: str,
) -> list[int]:
    lines: list[
        int
    ] = []

    for node in ast.walk(
        function
    ):
        if not isinstance(
            node,
            ast.Return,
        ):
            continue

        if node.value is None:
            continue

        returned = ast.unparse(
            node.value
        ).strip()

        if returned == variable_name:
            lines.append(
                node.lineno
            )

    return sorted(
        lines
    )


def aday_puanla(
    candidate: FastApiAdayi,
) -> None:
    file_name = Path(
        candidate.dosya
    ).name.lower()

    object_name = (
        candidate.nesne_adi.lower()
    )

    function_name = (
        candidate.fonksiyon_adi.lower()
        if candidate.fonksiyon_adi
        else ""
    )

    if (
        "fastapi"
        in file_name
    ):
        candidate.puan += 30
        candidate.gerekceler.append(
            "dosya_adinda_fastapi"
        )

    if (
        "sunucu"
        in file_name
    ):
        candidate.puan += 20
        candidate.gerekceler.append(
            "dosya_adinda_sunucu"
        )

    if (
        "runtime"
        in file_name
    ):
        candidate.puan += 10
        candidate.gerekceler.append(
            "dosya_adinda_runtime"
        )

    if object_name in {
        "app",
        "uygulama",
        "application",
        "api",
    }:
        candidate.puan += 25
        candidate.gerekceler.append(
            "standart_uygulama_degiskeni"
        )

    if any(
        word in function_name
        for word in (
            "app",
            "uygulama",
            "fastapi",
            "sunucu",
            "olustur",
            "uret",
            "create",
            "build",
        )
    ):
        candidate.puan += 25
        candidate.gerekceler.append(
            "fabrika_fonksiyon_adi"
        )

    if (
        candidate.return_satiri
        is not None
    ):
        candidate.puan += 20
        candidate.gerekceler.append(
            "uygulama_return_ediliyor"
        )

    if (
        candidate.include_router_sayisi
        > 0
    ):
        candidate.puan += 15
        candidate.gerekceler.append(
            "mevcut_router_baglantilari_var"
        )

    if (
        candidate.mevcut_ugr_baglantisi
    ):
        candidate.puan += 50
        candidate.gerekceler.append(
            "ugr_zaten_bagli"
        )

    if candidate.tur == "top_level":
        candidate.puan += 10
        candidate.gerekceler.append(
            "ust_seviye_uygulama"
        )


def dosya_adaylarini_bul(
    path: Path,
) -> list[FastApiAdayi]:
    source = path.read_text(
        encoding="utf-8-sig"
    )

    try:
        tree = ast.parse(
            source,
            filename=str(
                path
            ),
        )
    except SyntaxError:
        return []

    module_name = module_name_for_path(
        path
    )

    candidates: list[
        FastApiAdayi
    ] = []

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
            ),
        ):
            value = node.value

            if value is None:
                continue

            if not fastapi_call_mi(
                value
            ):
                continue

            targets = assignment_targets(
                node
            )

            for target in targets:
                candidate = FastApiAdayi(
                    dosya=path.as_posix(),
                    modul=module_name,
                    tur="top_level",
                    nesne_adi=target,
                    fonksiyon_adi=None,
                    fastapi_satiri=node.lineno,
                    fastapi_bitis_satiri=int(
                        getattr(
                            node,
                            "end_lineno",
                            node.lineno,
                        )
                    ),
                    uygulama_ifadesi=(
                        ast.unparse(
                            value
                        )
                    ),
                    uygulama_degiskeni=target,
                    return_satiri=None,
                    include_router_sayisi=len(
                        include_router_calls(
                            tree
                        )
                    ),
                    mevcut_ugr_baglantisi=(
                        includes_ugr_router(
                            tree
                        )
                    ),
                )

                aday_puanla(
                    candidate
                )

                candidates.append(
                    candidate
                )

        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        function = node

        for child in function.body:
            if not isinstance(
                child,
                (
                    ast.Assign,
                    ast.AnnAssign,
                ),
            ):
                continue

            value = child.value

            if value is None:
                continue

            if not fastapi_call_mi(
                value
            ):
                continue

            targets = assignment_targets(
                child
            )

            for target in targets:
                return_lines = (
                    function_return_lines(
                        function,
                        target,
                    )
                )

                candidate = FastApiAdayi(
                    dosya=path.as_posix(),
                    modul=module_name,
                    tur="factory",
                    nesne_adi=target,
                    fonksiyon_adi=(
                        function.name
                    ),
                    fastapi_satiri=(
                        child.lineno
                    ),
                    fastapi_bitis_satiri=int(
                        getattr(
                            child,
                            "end_lineno",
                            child.lineno,
                        )
                    ),
                    uygulama_ifadesi=(
                        ast.unparse(
                            value
                        )
                    ),
                    uygulama_degiskeni=target,
                    return_satiri=(
                        return_lines[-1]
                        if return_lines
                        else None
                    ),
                    include_router_sayisi=len(
                        include_router_calls(
                            function
                        )
                    ),
                    mevcut_ugr_baglantisi=(
                        includes_ugr_router(
                            function
                        )
                    ),
                )

                aday_puanla(
                    candidate
                )

                candidates.append(
                    candidate
                )

    return candidates


def import_insert_line(
    tree: ast.Module,
) -> int:
    line = 0

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            line = int(
                getattr(
                    node,
                    "end_lineno",
                    node.lineno,
                )
            )

    return line


def indentation_of_line(
    lines: list[str],
    line_number: int,
) -> str:
    if (
        line_number <= 0
        or line_number > len(
            lines
        )
    ):
        return ""

    line = lines[
        line_number - 1
    ]

    return line[
        : len(line)
        - len(
            line.lstrip()
        )
    ]


def insert_after(
    lines: list[str],
    line_number: int,
    block_lines: list[str],
) -> list[str]:
    index = max(
        0,
        min(
            line_number,
            len(lines),
        ),
    )

    return (
        lines[:index]
        + [""]
        + block_lines
        + [""]
        + lines[index:]
    )


def patch_candidate(
    candidate: FastApiAdayi,
) -> PatchSonucu:
    path = Path(
        candidate.dosya
    )

    original = path.read_text(
        encoding="utf-8-sig"
    )

    original_tree = ast.parse(
        original,
        filename=str(
            path
        ),
    )

    backup_relative = path.relative_to(
        ROOT
    )

    backup = (
        BACKUP_ROOT
        / backup_relative
    )

    backup.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not backup.exists():
        shutil.copy2(
            path,
            backup,
        )

    updated = original
    import_added = False
    connection_added = False

    if IMPORT_MARKER not in updated:
        tree = ast.parse(
            updated,
            filename=str(
                path
            ),
        )

        lines = updated.splitlines()

        insert_line = (
            import_insert_line(
                tree
            )
        )

        lines = insert_after(
            lines,
            insert_line,
            IMPORT_BLOCK.rstrip(
                "\n"
            ).splitlines(),
        )

        updated = "\n".join(
            lines
        ) + "\n"

        import_added = True

    if CONNECTION_MARKER not in updated:
        tree = ast.parse(
            updated,
            filename=str(
                path
            ),
        )

        candidates_after_import = (
            dosya_adaylarini_bul(
                path
            )
        )

        selected = None

        for item in candidates_after_import:
            if (
                item.modul
                == candidate.modul
                and item.tur
                == candidate.tur
                and item.nesne_adi
                == candidate.nesne_adi
                and item.fonksiyon_adi
                == candidate.fonksiyon_adi
            ):
                selected = item
                break

        if selected is None:
            source_after_import = (
                "\n".join(
                    updated.splitlines()
                )
                + "\n"
            )

            temporary_tree = ast.parse(
                source_after_import,
                filename=str(
                    path
                ),
            )

            found_fastapi_line = None

            for node in ast.walk(
                temporary_tree
            ):
                if isinstance(
                    node,
                    (
                        ast.Assign,
                        ast.AnnAssign,
                    ),
                ):
                    if (
                        node.value is not None
                        and fastapi_call_mi(
                            node.value
                        )
                    ):
                        targets = (
                            assignment_targets(
                                node
                            )
                        )

                        if (
                            candidate.nesne_adi
                            in targets
                        ):
                            found_fastapi_line = int(
                                getattr(
                                    node,
                                    "end_lineno",
                                    node.lineno,
                                )
                            )
                            break

            if found_fastapi_line is None:
                raise RuntimeError(
                    "Import sonrası FastAPI ataması yeniden bulunamadı."
                )

            selected_fastapi_end = (
                found_fastapi_line
            )
        else:
            selected_fastapi_end = (
                selected.fastapi_bitis_satiri
            )

        lines = updated.splitlines()

        indentation = indentation_of_line(
            lines,
            selected_fastapi_end,
        )

        application_name = (
            candidate.uygulama_degiskeni
        )

        if not application_name:
            raise RuntimeError(
                "FastAPI uygulama değişkeni belirlenemedi."
            )

        connection_block = [
            (
                indentation
                + CONNECTION_MARKER
            ),
            (
                indentation
                + application_name
                + ".include_router("
            ),
            (
                indentation
                + "    syk_ugr_router,"
            ),
            (
                indentation
                + ")"
            ),
        ]

        lines = insert_after(
            lines,
            selected_fastapi_end,
            connection_block,
        )

        updated = "\n".join(
            lines
        ) + "\n"

        connection_added = True

    ast.parse(
        updated,
        filename=str(
            path
        ),
    )

    path.write_text(
        updated,
        encoding="utf-8",
    )

    final_source = path.read_text(
        encoding="utf-8"
    )

    final_tree = ast.parse(
        final_source,
        filename=str(
            path
        ),
    )

    ugr_connections = 0

    for call in include_router_calls(
        final_tree
    ):
        arguments = [
            ast.unparse(
                argument
            )
            for argument in call.args
        ]

        if any(
            "syk_ugr_router"
            in argument
            for argument in arguments
        ):
            ugr_connections += 1

    if ugr_connections != 1:
        raise RuntimeError(
            "UGR router bağlantısı tam olarak bir adet olmalıdır. "
            f"BULUNAN={ugr_connections}"
        )

    if (
        candidate.tur
        == "top_level"
    ):
        import_object = (
            f"{candidate.modul}:"
            f"{candidate.nesne_adi}"
        )

        factory = False

    else:
        if not candidate.fonksiyon_adi:
            raise RuntimeError(
                "Fabrika fonksiyonu adı bulunamadı."
            )

        import_object = (
            f"{candidate.modul}:"
            f"{candidate.fonksiyon_adi}"
        )

        factory = True

    return PatchSonucu(
        dosya=path.as_posix(),
        modul=candidate.modul,
        import_nesnesi=(
            import_object
        ),
        factory=factory,
        uygulama_degiskeni=(
            candidate.uygulama_degiskeni
            or candidate.nesne_adi
        ),
        fonksiyon_adi=(
            candidate.fonksiyon_adi
        ),
        import_eklendi=(
            import_added
        ),
        router_baglantisi_eklendi=(
            connection_added
        ),
        yedek=backup.as_posix(),
        aday_puani=(
            candidate.puan
        ),
    )


def runtime_nesnesi_dogrula(
    patch: PatchSonucu,
) -> dict[str, Any]:
    module_name, object_name = (
        patch.import_nesnesi.split(
            ":",
            1,
        )
    )

    module = importlib.import_module(
        module_name
    )

    target = getattr(
        module,
        object_name,
    )

    if patch.factory:
        if not callable(
            target
        ):
            raise RuntimeError(
                "Belirlenen FastAPI fabrikası çağrılabilir değil."
            )

        signature = inspect.signature(
            target
        )

        required_parameters = [
            parameter
            for parameter
            in signature.parameters.values()
            if (
                parameter.default
                is inspect.Parameter.empty
                and parameter.kind
                in {
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                }
            )
        ]

        if required_parameters:
            return {
                "import_edildi": True,
                "factory": True,
                "fabrika_cagrilamadi": True,
                "zorunlu_parametreler": [
                    parameter.name
                    for parameter
                    in required_parameters
                ],
                "route_sayisi": None,
                "ugr_route_sayisi": None,
            }

        application = target()

    else:
        application = target

    routes = getattr(
        application,
        "routes",
        None,
    )

    if routes is None:
        raise RuntimeError(
            "Belirlenen uygulama nesnesinde routes bulunamadı."
        )

    route_paths = [
        getattr(
            route,
            "path",
            None,
        )
        for route in routes
    ]

    ugr_paths = [
        path
        for path in route_paths
        if (
            isinstance(
                path,
                str,
            )
            and path.startswith(
                "/api/ugr"
            )
        )
    ]

    if not ugr_paths:
        raise RuntimeError(
            "Patch sonrasında uygulama nesnesinde UGR rotası bulunamadı."
        )

    return {
        "import_edildi": True,
        "factory": (
            patch.factory
        ),
        "fabrika_cagrilamadi": False,
        "route_sayisi": len(
            route_paths
        ),
        "ugr_route_sayisi": len(
            ugr_paths
        ),
        "ugr_yollari": sorted(
            ugr_paths
        ),
    }


def text_report(
    candidates: list[FastApiAdayi],
    patch: PatchSonucu,
    runtime_result: dict[str, Any],
) -> str:
    lines = [
        "SPR-011 PAKET-007",
        "GERCEK FASTAPI FABRIKASI UGR PATCH RAPORU",
        "",
        (
            "TOPLAM_FASTAPI_ADAYI="
            f"{len(candidates)}"
        ),
        (
            "SECILEN_DOSYA="
            f"{patch.dosya}"
        ),
        (
            "SECILEN_MODUL="
            f"{patch.modul}"
        ),
        (
            "SECILEN_IMPORT="
            f"{patch.import_nesnesi}"
        ),
        (
            "FACTORY="
            f"{patch.factory}"
        ),
        (
            "UYGULAMA_DEGISKENI="
            f"{patch.uygulama_degiskeni}"
        ),
        (
            "FONKSIYON="
            f"{patch.fonksiyon_adi}"
        ),
        (
            "ADAY_PUANI="
            f"{patch.aday_puani}"
        ),
        (
            "IMPORT_EKLENDI="
            f"{patch.import_eklendi}"
        ),
        (
            "ROUTER_BAGLANTISI_EKLENDI="
            f"{patch.router_baglantisi_eklendi}"
        ),
        (
            "YEDEK="
            f"{patch.yedek}"
        ),
        "",
        "RUNTIME_DOGRULAMA:",
        json.dumps(
            runtime_result,
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "ADAYLAR:",
    ]

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        lines.extend(
            [
                "-" * 88,
                f"SIRA={index}",
                f"DOSYA={candidate.dosya}",
                f"MODUL={candidate.modul}",
                f"TUR={candidate.tur}",
                (
                    "NESNE="
                    f"{candidate.nesne_adi}"
                ),
                (
                    "FONKSIYON="
                    f"{candidate.fonksiyon_adi}"
                ),
                (
                    "FASTAPI_SATIRI="
                    f"{candidate.fastapi_satiri}"
                ),
                (
                    "RETURN_SATIRI="
                    f"{candidate.return_satiri}"
                ),
                (
                    "INCLUDE_ROUTER="
                    f"{candidate.include_router_sayisi}"
                ),
                (
                    "MEVCUT_UGR="
                    f"{candidate.mevcut_ugr_baglantisi}"
                ),
                f"PUAN={candidate.puan}",
                (
                    "GEREKCELER="
                    + ",".join(
                        candidate.gerekceler
                    )
                ),
            ]
        )

    lines.extend(
        [
            "",
            "KARAR=GERCEK_FASTAPI_URETIM_NOKTASI_PATCH_EDILDI",
            "UGR_ROUTER_BAGLANTISI=GERCEK_UYGULAMA_NESNESINDE",
            "",
        ]
    )

    return "\n".join(
        lines
    )


def parser_create() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output-json",
        default=str(
            REPORT_JSON
        ),
    )

    parser.add_argument(
        "--output-text",
        default=str(
            REPORT_TEXT
        ),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    arguments = parser_create().parse_args(
        argv
    )

    source_files = sorted(
        path
        for path in SOURCE_ROOT.rglob(
            "*.py"
        )
        if (
            "__pycache__"
            not in path.parts
            and ".venv"
            not in path.parts
        )
    )

    candidates: list[
        FastApiAdayi
    ] = []

    for source_file in source_files:
        candidates.extend(
            dosya_adaylarini_bul(
                source_file
            )
        )

    if not candidates:
        raise RuntimeError(
            "src/syk_simulasyon altında FastAPI() üretim noktası bulunamadı."
        )

    candidates.sort(
        key=lambda candidate: (
            candidate.puan,
            candidate.include_router_sayisi,
            candidate.return_satiri
            is not None,
        ),
        reverse=True,
    )

    best_score = candidates[
        0
    ].puan

    best_candidates = [
        candidate
        for candidate in candidates
        if candidate.puan
        == best_score
    ]

    if len(
        best_candidates
    ) > 1:
        preferred = [
            candidate
            for candidate
            in best_candidates
            if (
                Path(
                    candidate.dosya
                ).name
                == "runtime_fastapi_sunucusu.py"
            )
        ]

        if len(
            preferred
        ) == 1:
            selected = preferred[
                0
            ]
        else:
            raise RuntimeError(
                "Birden fazla eşit puanlı FastAPI adayı bulundu: "
                + ", ".join(
                    (
                        f"{candidate.modul}:"
                        f"{candidate.fonksiyon_adi or candidate.nesne_adi}"
                    )
                    for candidate
                    in best_candidates
                )
            )
    else:
        selected = best_candidates[
            0
        ]

    patch = patch_candidate(
        selected
    )

    runtime_result = (
        runtime_nesnesi_dogrula(
            patch
        )
    )

    report = {
        "schema": (
            "sykasif.real-fastapi-factory-ugr-patch.v1"
        ),
        "toplam_fastapi_adayi": len(
            candidates
        ),
        "adaylar": [
            asdict(
                candidate
            )
            for candidate
            in candidates
        ],
        "secili_aday": asdict(
            selected
        ),
        "patch": asdict(
            patch
        ),
        "runtime_dogrulama": (
            runtime_result
        ),
    }

    output_json = Path(
        arguments.output_json
    )

    output_text = Path(
        arguments.output_text
    )

    output_json.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_json.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    output_text.write_text(
        text_report(
            candidates,
            patch,
            runtime_result,
        ),
        encoding="utf-8",
    )

    print(
        "GERCEK_FASTAPI_FABRIKASI_BULUNDU"
    )
    print(
        f"SECILEN_DOSYA={patch.dosya}"
    )
    print(
        f"DOGRU_APP_IMPORT={patch.import_nesnesi}"
    )
    print(
        f"DOGRU_FACTORY={patch.factory}"
    )
    print(
        f"UYGULAMA_DEGISKENI={patch.uygulama_degiskeni}"
    )
    print(
        "UGR_ROUTER_GERCEK_FASTAPI_NOKTASINA_BAGLANDI"
    )
    print(
        "GERCEK_FASTAPI_FABRIKASI_PATCH_TAMAMLANDI"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path.cwd()

SOURCE = (
    ROOT
    / "src"
    / "syk_simulasyon"
    / "syk_ui_runtime"
    / "ugr_runtime_routes.py"
)

REPORT = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_006_ugr_runtime_route_patch"
    / "UGR_BULK_ROUTE_SIRA_ONARIM_RAPORU.txt"
)

BULK_FUNCTION = "ugr_toplu_ikon_durumu"
DYNAMIC_FUNCTION = "ugr_ikon_durumu_degistir"


def function_nodes(
    tree: ast.Module,
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    }


def block_start(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> int:
    """Dekoratörleri de kapsayan 1 tabanlı başlangıç satırını döndürür."""

    lines = [
        node.lineno,
        *[
            decorator.lineno
            for decorator in node.decorator_list
        ],
    ]

    return min(lines)


def block_end(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> int:
    """Fonksiyon bloğunun 1 tabanlı son satırını döndürür."""

    return int(
        getattr(
            node,
            "end_lineno",
            node.lineno,
        )
    )


def route_paths(
    source: str,
) -> list[tuple[str, str, int]]:
    """Kaynak sırasına göre route yolu, fonksiyon ve satır listesini üretir."""

    tree = ast.parse(
        source,
        filename=str(SOURCE),
    )

    routes: list[
        tuple[str, str, int]
    ] = []

    for node in tree.body:
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        for decorator in node.decorator_list:
            if not isinstance(
                decorator,
                ast.Call,
            ):
                continue

            if not isinstance(
                decorator.func,
                ast.Attribute,
            ):
                continue

            if decorator.func.attr not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "websocket",
            }:
                continue

            if not decorator.args:
                continue

            first_argument = decorator.args[0]

            if not isinstance(
                first_argument,
                ast.Constant,
            ):
                continue

            if not isinstance(
                first_argument.value,
                str,
            ):
                continue

            routes.append(
                (
                    first_argument.value,
                    node.name,
                    decorator.lineno,
                )
            )

    return routes


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(
            SOURCE
        )

    original = SOURCE.read_text(
        encoding="utf-8-sig"
    )

    original_tree = ast.parse(
        original,
        filename=str(SOURCE),
    )

    functions = function_nodes(
        original_tree
    )

    if BULK_FUNCTION not in functions:
        raise RuntimeError(
            f"Toplu route fonksiyonu bulunamadı: {BULK_FUNCTION}"
        )

    if DYNAMIC_FUNCTION not in functions:
        raise RuntimeError(
            f"Dinamik route fonksiyonu bulunamadı: {DYNAMIC_FUNCTION}"
        )

    bulk_node = functions[
        BULK_FUNCTION
    ]

    dynamic_node = functions[
        DYNAMIC_FUNCTION
    ]

    bulk_start = block_start(
        bulk_node
    )

    bulk_end = block_end(
        bulk_node
    )

    dynamic_start = block_start(
        dynamic_node
    )

    original_routes = route_paths(
        original
    )

    original_bulk_index = next(
        (
            index
            for index, route
            in enumerate(original_routes)
            if route[0]
            == "/icons/bulk/state"
        ),
        -1,
    )

    original_dynamic_index = next(
        (
            index
            for index, route
            in enumerate(original_routes)
            if route[0]
            == "/icons/{ikon_kimligi}/state"
        ),
        -1,
    )

    if original_bulk_index < 0:
        raise RuntimeError(
            "/icons/bulk/state rotası bulunamadı."
        )

    if original_dynamic_index < 0:
        raise RuntimeError(
            "/icons/{ikon_kimligi}/state rotası bulunamadı."
        )

    if original_bulk_index < original_dynamic_index:
        updated = original
        changed = False

    else:
        lines = original.splitlines()

        bulk_block = lines[
            bulk_start - 1:
            bulk_end
        ]

        before_bulk = lines[
            : bulk_start - 1
        ]

        after_bulk = lines[
            bulk_end:
        ]

        without_bulk = (
            before_bulk
            + after_bulk
        )

        removed_line_count = (
            bulk_end
            - bulk_start
            + 1
        )

        if bulk_start < dynamic_start:
            adjusted_dynamic_start = (
                dynamic_start
                - removed_line_count
            )
        else:
            adjusted_dynamic_start = (
                dynamic_start
            )

        insertion_index = (
            adjusted_dynamic_start
            - 1
        )

        updated_lines = (
            without_bulk[
                :insertion_index
            ]
            + bulk_block
            + [""]
            + without_bulk[
                insertion_index:
            ]
        )

        updated = "\n".join(
            updated_lines
        ) + "\n"

        changed = True

    ast.parse(
        updated,
        filename=str(SOURCE),
    )

    updated_routes = route_paths(
        updated
    )

    updated_bulk_index = next(
        index
        for index, route
        in enumerate(updated_routes)
        if route[0]
        == "/icons/bulk/state"
    )

    updated_dynamic_index = next(
        index
        for index, route
        in enumerate(updated_routes)
        if route[0]
        == "/icons/{ikon_kimligi}/state"
    )

    if updated_bulk_index >= updated_dynamic_index:
        raise RuntimeError(
            "Sabit bulk rotası dinamik ikon rotasının önüne taşınamadı."
        )

    SOURCE.write_text(
        updated,
        encoding="utf-8",
    )

    report_lines = [
        "SPR-011 PAKET-006",
        "UGR BULK ROUTE SIRA ONARIM RAPORU",
        "",
        f"DOSYA={SOURCE.as_posix()}",
        f"DEGISIKLIK_YAPILDI={changed}",
        (
            "ONCEKI_BULK_ROUTE_INDEX="
            f"{original_bulk_index}"
        ),
        (
            "ONCEKI_DYNAMIC_ROUTE_INDEX="
            f"{original_dynamic_index}"
        ),
        (
            "YENI_BULK_ROUTE_INDEX="
            f"{updated_bulk_index}"
        ),
        (
            "YENI_DYNAMIC_ROUTE_INDEX="
            f"{updated_dynamic_index}"
        ),
        "SABIT_ROUTE=/icons/bulk/state",
        (
            "DINAMIK_ROUTE="
            "/icons/{ikon_kimligi}/state"
        ),
        "SABIT_ROUTE_ONDE=EVET",
        "FASTAPI_ROUTE_GOLGELEMESI=GIDERILDI",
        "",
        "ROUTE_SIRASI:",
    ]

    for index, route in enumerate(
        updated_routes
    ):
        report_lines.append(
            (
                f"{index:02d} "
                f"YOL={route[0]} "
                f"FONKSIYON={route[1]} "
                f"SATIR={route[2]}"
            )
        )

    REPORT.write_text(
        "\n".join(report_lines)
        + "\n",
        encoding="utf-8",
    )

    print(
        "UGR_BULK_ROUTE_SIRA_ONARIMI_TAMAMLANDI"
    )
    print(
        f"DEGISIKLIK_YAPILDI={changed}"
    )
    print(
        f"BULK_ROUTE_INDEX={updated_bulk_index}"
    )
    print(
        f"DYNAMIC_ROUTE_INDEX={updated_dynamic_index}"
    )
    print(
        "SABIT_ROUTE_ONDE=EVET"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

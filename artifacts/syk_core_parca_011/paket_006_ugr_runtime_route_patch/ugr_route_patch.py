from __future__ import annotations

import ast
import shutil
from pathlib import Path


ROOT = Path.cwd()

SOURCE = (
    ROOT
    / "src"
    / "syk_simulasyon"
    / "runtime_ui_sunucusu.py"
)

BACKUP = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_006_ugr_runtime_route_patch"
    / "runtime_ui_sunucusu_patch_oncesi.py"
)

REPORT = (
    ROOT
    / "artifacts"
    / "syk_core_parca_011"
    / "paket_006_ugr_runtime_route_patch"
    / "UGR_RUNTIME_ROUTE_PATCH_RAPORU.txt"
)

IMPORT_MARKER = "# SYK_UGR_RUNTIME_ROUTER_IMPORT"
INCLUDE_MARKER = "# SYK_UGR_RUNTIME_ROUTER_BAGLANTISI"

IMPORT_BLOCK = """\
# SYK_UGR_RUNTIME_ROUTER_IMPORT
from syk_simulasyon.syk_ui_runtime.ugr_runtime_routes import (
    ugr_router as syk_ugr_router,
)
"""


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    if isinstance(node, ast.Call):
        return dotted_name(node.func)

    return None


def import_insert_line(tree: ast.Module) -> int:
    """Son üst seviye import satırını bulur."""

    son_import = 0

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            son_import = int(
                getattr(
                    node,
                    "end_lineno",
                    node.lineno,
                )
            )

    return son_import


def include_router_calls(
    tree: ast.Module,
) -> list[ast.Call]:
    """Kaynak içindeki bütün include_router çağrılarını bulur."""

    sonuclar: list[ast.Call] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Attribute):
            continue

        if node.func.attr != "include_router":
            continue

        sonuclar.append(node)

    return sorted(
        sonuclar,
        key=lambda node: node.lineno,
    )


def receiver_source(
    call: ast.Call,
) -> str:
    """include_router çağrısının uygulama nesnesini alır."""

    if not isinstance(call.func, ast.Attribute):
        raise RuntimeError(
            "include_router çağrısı Attribute yapısında değil."
        )

    receiver = ast.unparse(
        call.func.value
    ).strip()

    if not receiver:
        raise RuntimeError(
            "include_router uygulama nesnesi belirlenemedi."
        )

    return receiver


def indentation_at(
    lines: list[str],
    line_number: int,
) -> str:
    """Belirtilen satırın girintisini döndürür."""

    if line_number <= 0:
        return ""

    if line_number > len(lines):
        return ""

    line = lines[
        line_number - 1
    ]

    return line[
        : len(line) - len(line.lstrip())
    ]


def insert_after_line(
    text: str,
    line_number: int,
    block: str,
) -> str:
    """Metin bloğunu verilen satırdan sonra ekler."""

    lines = text.splitlines()

    index = max(
        0,
        min(
            line_number,
            len(lines),
        ),
    )

    block_lines = block.rstrip(
        "\n"
    ).splitlines()

    updated = (
        lines[:index]
        + [""]
        + block_lines
        + [""]
        + lines[index:]
    )

    return "\n".join(
        updated
    ) + "\n"


def include_block(
    receiver: str,
    indentation: str,
) -> str:
    """Gerçek girintiye uygun UGR include_router bloğu üretir."""

    return "\n".join(
        [
            (
                indentation
                + INCLUDE_MARKER
            ),
            (
                indentation
                + receiver
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
    )


def validate_patch(
    text: str,
) -> tuple[str, int]:
    """Patch sonrası kaynak sözleşmesini doğrular."""

    tree = ast.parse(
        text,
        filename=str(SOURCE),
    )

    calls = include_router_calls(
        tree
    )

    ugr_calls: list[
        ast.Call
    ] = []

    for call in calls:
        for argument in call.args:
            if (
                isinstance(
                    argument,
                    ast.Name,
                )
                and argument.id
                == "syk_ugr_router"
            ):
                ugr_calls.append(
                    call
                )

    if len(ugr_calls) != 1:
        raise RuntimeError(
            "UGR include_router bağlantısı tam olarak bir adet olmalıdır. "
            f"BULUNAN={len(ugr_calls)}"
        )

    receiver = receiver_source(
        ugr_calls[0]
    )

    return receiver, len(calls)


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

    existing_calls = include_router_calls(
        original_tree
    )

    if not existing_calls:
        raise RuntimeError(
            "Ana UI sunucusunda include_router çağrısı bulunamadı."
        )

    reference_call = existing_calls[-1]

    receiver = receiver_source(
        reference_call
    )

    include_end_line = int(
        getattr(
            reference_call,
            "end_lineno",
            reference_call.lineno,
        )
    )

    original_lines = original.splitlines()

    indentation = indentation_at(
        original_lines,
        reference_call.lineno,
    )

    BACKUP.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not BACKUP.exists():
        shutil.copy2(
            SOURCE,
            BACKUP,
        )

    updated = original
    import_added = False
    include_added = False

    if IMPORT_MARKER not in updated:
        import_line = import_insert_line(
            original_tree
        )

        updated = insert_after_line(
            updated,
            import_line,
            IMPORT_BLOCK,
        )

        import_added = True

    if INCLUDE_MARKER not in updated:
        updated_tree = ast.parse(
            updated,
            filename=str(SOURCE),
        )

        updated_calls = include_router_calls(
            updated_tree
        )

        if not updated_calls:
            raise RuntimeError(
                "Import eklenmesinden sonra include_router çağrısı kayboldu."
            )

        reference_call = updated_calls[-1]

        receiver = receiver_source(
            reference_call
        )

        include_end_line = int(
            getattr(
                reference_call,
                "end_lineno",
                reference_call.lineno,
            )
        )

        updated_lines = updated.splitlines()

        indentation = indentation_at(
            updated_lines,
            reference_call.lineno,
        )

        updated = insert_after_line(
            updated,
            include_end_line,
            include_block(
                receiver,
                indentation,
            ),
        )

        include_added = True

    final_receiver, total_include_calls = validate_patch(
        updated
    )

    SOURCE.write_text(
        updated,
        encoding="utf-8",
    )

    final_text = SOURCE.read_text(
        encoding="utf-8"
    )

    if IMPORT_MARKER not in final_text:
        raise RuntimeError(
            "UGR router import bağlantısı oluşmadı."
        )

    if INCLUDE_MARKER not in final_text:
        raise RuntimeError(
            "UGR include_router bağlantısı oluşmadı."
        )

    report_lines = [
        "SPR-011 PAKET-006",
        "UGR RUNTIME 8013 ROUTE PATCH RAPORU",
        "",
        f"ANA_DOSYA={SOURCE.as_posix()}",
        f"YEDEK={BACKUP.as_posix()}",
        f"UYGULAMA_NESNESI={final_receiver}",
        f"IMPORT_EKLENDI={import_added}",
        f"INCLUDE_ROUTER_EKLENDI={include_added}",
        f"TOPLAM_INCLUDE_ROUTER={total_include_calls}",
        "UGR_INCLUDE_ROUTER_SAYISI=1",
        "UGR_ROUTER=syk_ugr_router",
        "PREFIX=/api/ugr",
        "TESPIT_YONTEMI=MEVCUT_INCLUDE_ROUTER_RECEIVER",
        "TEKRAR_CALISTIRILABILIR=EVET",
        "GERI_ALINABILIR=EVET",
        "",
        "ROUTES:",
        "GET /api/ugr/health",
        "GET /api/ugr/snapshot",
        "GET /api/ugr/icons",
        "GET /api/ugr/icons/{ikon_kimligi}",
        "GET /api/ugr/icons/{ikon_kimligi}/html",
        "POST /api/ugr/icons/{ikon_kimligi}/state",
        "POST /api/ugr/icons/{ikon_kimligi}/view",
        "POST /api/ugr/icons/{ikon_kimligi}/active",
        "POST /api/ugr/icons/bulk/state",
        "GET /api/ugr/events/history",
        "GET /api/ugr/events",
        "GET /api/ugr/preview",
        "GET /api/ugr/assets/{goreli_yol:path}",
        "",
    ]

    REPORT.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(
        "UGR_RUNTIME_ROUTE_PATCH_COMPLETED"
    )
    print(
        f"UYGULAMA_NESNESI={final_receiver}"
    )
    print(
        f"IMPORT_EKLENDI={import_added}"
    )
    print(
        f"INCLUDE_ROUTER_EKLENDI={include_added}"
    )
    print(
        "UGR_INCLUDE_ROUTER_SAYISI=1"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any, Sequence


HTTP_DECORATORS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "route",
    "websocket",
}

SERVER_TERMS = {
    "FastAPI",
    "APIRouter",
    "StaticFiles",
    "StreamingResponse",
    "JSONResponse",
    "HTMLResponse",
    "FileResponse",
    "WebSocket",
    "WebSocketDisconnect",
    "HTTPException",
    "uvicorn",
}


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return None


def literal_value(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def decorator_record(
    decorator: ast.AST,
) -> dict[str, Any] | None:
    call = decorator if isinstance(
        decorator,
        ast.Call,
    ) else None

    target = (
        call.func
        if call is not None
        else decorator
    )

    name = dotted_name(target)

    if not name:
        return None

    final_name = name.rsplit(".", 1)[-1]

    if final_name not in HTTP_DECORATORS:
        return None

    arguments: list[Any] = []
    keywords: dict[str, Any] = {}

    if call is not None:
        arguments = [
            literal_value(argument)
            for argument in call.args
        ]

        keywords = {
            keyword.arg or "**":
                literal_value(keyword.value)
            for keyword in call.keywords
        }

    path = (
        arguments[0]
        if arguments
        and isinstance(arguments[0], str)
        else None
    )

    return {
        "decorator": name,
        "method": final_name.upper(),
        "path": path,
        "arguments": arguments,
        "keywords": keywords,
    }


def function_signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    parts: list[str] = []

    positional = (
        list(node.args.posonlyargs)
        + list(node.args.args)
    )

    defaults = [None] * (
        len(positional)
        - len(node.args.defaults)
    ) + list(node.args.defaults)

    for argument, default in zip(
        positional,
        defaults,
        strict=True,
    ):
        piece = argument.arg

        if argument.annotation is not None:
            piece += ": " + ast.unparse(
                argument.annotation
            )

        if default is not None:
            piece += " = " + ast.unparse(
                default
            )

        parts.append(piece)

    if node.args.vararg is not None:
        parts.append(
            "*" + node.args.vararg.arg
        )
    elif node.args.kwonlyargs:
        parts.append("*")

    for argument, default in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
        strict=True,
    ):
        piece = argument.arg

        if argument.annotation is not None:
            piece += ": " + ast.unparse(
                argument.annotation
            )

        if default is not None:
            piece += " = " + ast.unparse(
                default
            )

        parts.append(piece)

    if node.args.kwarg is not None:
        parts.append(
            "**" + node.args.kwarg.arg
        )

    result = (
        f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}"
        f"def {node.name}("
        + ", ".join(parts)
        + ")"
    )

    if node.returns is not None:
        result += " -> " + ast.unparse(
            node.returns
        )

    return result


def inspect_file(path: Path) -> dict[str, Any]:
    source = path.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(
        source,
        filename=str(path),
    )

    imports: list[str] = []
    assignments: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(
                alias.name
                for alias in node.names
            )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            imports.extend(
                f"{module}.{alias.name}"
                for alias in node.names
            )

        elif isinstance(
            node,
            (ast.Assign, ast.AnnAssign),
        ):
            targets: list[str] = []

            if isinstance(node, ast.Assign):
                targets = [
                    dotted_name(target) or ast.unparse(
                        target
                    )
                    for target in node.targets
                ]
                value = node.value
            else:
                targets = [
                    dotted_name(node.target)
                    or ast.unparse(node.target)
                ]
                value = node.value

            assignments.append(
                {
                    "targets": targets,
                    "value": (
                        ast.unparse(value)
                        if value is not None
                        else None
                    ),
                    "line": node.lineno,
                }
            )

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            record = {
                "name": node.name,
                "signature": function_signature(
                    node
                ),
                "async": isinstance(
                    node,
                    ast.AsyncFunctionDef,
                ),
                "line": node.lineno,
                "end_line": getattr(
                    node,
                    "end_lineno",
                    None,
                ),
                "decorators": [],
            }

            for decorator in node.decorator_list:
                route = decorator_record(
                    decorator
                )

                if route:
                    route.update(
                        {
                            "function": node.name,
                            "signature": record[
                                "signature"
                            ],
                            "async": record[
                                "async"
                            ],
                            "line": node.lineno,
                        }
                    )
                    routes.append(route)
                    record[
                        "decorators"
                    ].append(route)
                else:
                    record[
                        "decorators"
                    ].append(
                        {
                            "raw": ast.unparse(
                                decorator
                            )
                        }
                    )

            functions.append(record)

        elif isinstance(node, ast.ClassDef):
            methods: list[
                dict[str, Any]
            ] = []

            for child in node.body:
                if isinstance(
                    child,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                    ),
                ):
                    methods.append(
                        {
                            "name": child.name,
                            "signature":
                                function_signature(
                                    child
                                ),
                            "async": isinstance(
                                child,
                                ast.AsyncFunctionDef,
                            ),
                            "line": child.lineno,
                        }
                    )

            classes.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [
                        ast.unparse(base)
                        for base in node.bases
                    ],
                    "methods": methods,
                }
            )

    server_terms = sorted(
        term
        for term in SERVER_TERMS
        if re.search(
            rf"\b{re.escape(term)}\b",
            source,
        )
    )

    port_matches = sorted(
        {
            int(match)
            for match in re.findall(
                r"(?<!\d)(\d{4,5})(?!\d)",
                source,
            )
            if 1 <= int(match) <= 65535
        }
    )

    route_paths = sorted(
        {
            route["path"]
            for route in routes
            if route["path"]
        }
    )

    return {
        "path": path.as_posix(),
        "exists": True,
        "line_count": len(
            source.splitlines()
        ),
        "imports": imports,
        "assignments": assignments,
        "functions": functions,
        "classes": classes,
        "routes": routes,
        "route_paths": route_paths,
        "server_terms": server_terms,
        "port_candidates": port_matches,
        "contains_main_guard": (
            'if __name__ == "__main__"'
            in source
        ),
    }


def render_text(
    report: dict[str, Any],
) -> str:
    lines = [
        "SPR-011 PAKET-006",
        "RUNTIME 8013 GERCEK SOZLESME INCELEME RAPORU",
        "",
        f"TOPLAM_DOSYA={report['file_count']}",
        f"MEVCUT_DOSYA={report['existing_file_count']}",
        f"TOPLAM_ROUTE={report['route_count']}",
        "",
    ]

    for file_record in report["files"]:
        lines.extend(
            [
                "=" * 78,
                f"DOSYA={file_record['path']}",
                f"MEVCUT={file_record['exists']}",
            ]
        )

        if not file_record["exists"]:
            lines.append("")
            continue

        lines.extend(
            [
                f"SATIR_SAYISI={file_record['line_count']}",
                (
                    "SUNUCU_TERIMLERI="
                    + ",".join(
                        file_record[
                            "server_terms"
                        ]
                    )
                ),
                (
                    "PORT_ADAYLARI="
                    + ",".join(
                        str(port)
                        for port in file_record[
                            "port_candidates"
                        ]
                    )
                ),
                (
                    "MAIN_GUARD="
                    + str(
                        file_record[
                            "contains_main_guard"
                        ]
                    ).upper()
                ),
                "",
                "ROUTES:",
            ]
        )

        if file_record["routes"]:
            for route in file_record["routes"]:
                lines.append(
                    (
                        f"LINE={route['line']} "
                        f"METHOD={route['method']} "
                        f"PATH={route['path']} "
                        f"FUNCTION={route['function']} "
                        f"ASYNC={route['async']}"
                    )
                )
        else:
            lines.append("ROUTE_BULUNMADI")

        lines.extend(
            [
                "",
                "UST_SEVIYE_FONKSIYONLAR:",
            ]
        )

        if file_record["functions"]:
            for function in file_record[
                "functions"
            ]:
                lines.append(
                    (
                        f"LINE={function['line']} "
                        f"{function['signature']}"
                    )
                )
        else:
            lines.append(
                "UST_SEVIYE_FONKSIYON_BULUNMADI"
            )

        lines.extend(
            [
                "",
                "SINIFLAR:",
            ]
        )

        if file_record["classes"]:
            for class_record in file_record[
                "classes"
            ]:
                lines.append(
                    (
                        f"LINE={class_record['line']} "
                        f"CLASS={class_record['name']} "
                        f"BASES={','.join(class_record['bases'])}"
                    )
                )

                for method in class_record[
                    "methods"
                ]:
                    lines.append(
                        (
                            f"  LINE={method['line']} "
                            f"{method['signature']}"
                        )
                    )
        else:
            lines.append("SINIF_BULUNMADI")

        lines.append("")

    lines.extend(
        [
            "=" * 78,
            "KARAR:",
            (
                "Bu rapor tamamlanmadan runtime_ui_sunucusu.py "
                "dosyasına otomatik route patch uygulanmayacaktır."
            ),
            (
                "Paket-006 ikinci adımı gerçek route, uygulama nesnesi, "
                "yanıt sınıfı ve başlatma sözleşmesine göre üretilecektir."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def parser_create() -> argparse.ArgumentParser:
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
        "files",
        nargs="+",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parser_create().parse_args(
        argv
    )

    file_records: list[
        dict[str, Any]
    ] = []

    for raw_path in args.files:
        path = Path(raw_path)

        if not path.exists():
            file_records.append(
                {
                    "path": path.as_posix(),
                    "exists": False,
                }
            )
            continue

        file_records.append(
            inspect_file(path)
        )

    report = {
        "schema": (
            "sykasif.ugr.runtime-8013-contract-report.v1"
        ),
        "file_count": len(file_records),
        "existing_file_count": sum(
            record["exists"]
            for record in file_records
        ),
        "route_count": sum(
            len(record.get("routes", []))
            for record in file_records
        ),
        "files": file_records,
    }

    output_json = Path(
        args.output_json
    )

    output_text = Path(
        args.output_text
    )

    output_json.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_text.parent.mkdir(
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
        render_text(report),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "file_count": report[
                    "file_count"
                ],
                "existing_file_count": report[
                    "existing_file_count"
                ],
                "route_count": report[
                    "route_count"
                ],
                "output_json": (
                    output_json.as_posix()
                ),
                "output_text": (
                    output_text.as_posix()
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "UGR_RUNTIME_8013_CONTRACT_INSPECTION_COMPLETED"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

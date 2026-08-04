from __future__ import annotations

import ast
import json
from pathlib import Path

repo = Path(r"D:\sykasif_repo\sykasif")
src = repo / "src"
tests = repo / "tests"

route_text = "/syk-ui-screen"
records: list[dict[str, object]] = []

for root in (src, tests):
    if not root.exists():
        continue

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if route_text not in text:
            continue

        tree = ast.parse(text, filename=str(path))

        module_name = None
        try:
            relative = path.relative_to(src)
            module_name = ".".join(relative.with_suffix("").parts)
        except ValueError:
            pass

        imports: list[str] = []
        assignments: list[str] = []
        functions: list[str] = []
        decorators: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.extend(
                    f"{module}.{alias.name}".strip(".")
                    for alias in node.names
                )

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments.append(target.id)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)

                for decorator in node.decorator_list:
                    try:
                        decorators.append(ast.unparse(decorator))
                    except Exception:
                        decorators.append(type(decorator).__name__)

        records.append(
            {
                "path": str(path.relative_to(repo)),
                "module": module_name,
                "imports": sorted(set(imports)),
                "assignments": sorted(set(assignments)),
                "functions": sorted(set(functions)),
                "decorators": sorted(set(decorators)),
            }
        )

output = repo / "artifacts" / "syk_core_parca_004" / "r5_gercek_route"
output.mkdir(parents=True, exist_ok=True)

(output / "route_ast.json").write_text(
    json.dumps(
        records,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)

print(json.dumps(records, ensure_ascii=False, indent=2))

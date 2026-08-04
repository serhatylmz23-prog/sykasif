from __future__ import annotations

import ast
from pathlib import Path


integration_path = Path(
    "src/syk_jarmin/runtime/integration_runtime.py"
)

runtime_path = Path(
    "src/syk_jarmin/runtime/runtime.py"
)

if not integration_path.is_file():
    raise FileNotFoundError(
        f"Dosya bulunamadı: {integration_path}"
    )

if not runtime_path.is_file():
    raise FileNotFoundError(
        f"Dosya bulunamadı: {runtime_path}"
    )


integration_text = integration_path.read_text(
    encoding="utf-8"
)

runtime_text = runtime_path.read_text(
    encoding="utf-8"
)

integration_tree = ast.parse(
    integration_text
)

runtime_tree = ast.parse(
    runtime_text
)


def attribute_chain(
    node: ast.AST,
) -> list[str]:
    parts: list[str] = []

    current = node

    while isinstance(
        current,
        ast.Attribute,
    ):
        parts.append(
            current.attr
        )
        current = current.value

    if isinstance(
        current,
        ast.Name,
    ):
        parts.append(
            current.id
        )

    return list(
        reversed(parts)
    )


runtime_chains: set[str] = set()
runtime_calls: set[str] = set()

for node in ast.walk(
    integration_tree
):
    if isinstance(
        node,
        ast.Attribute,
    ):
        chain = attribute_chain(
            node
        )

        if (
            len(chain) >= 2
            and chain[0] == "self"
            and "runtime" in chain
        ):
            runtime_chains.add(
                ".".join(chain)
            )

    if isinstance(
        node,
        ast.Call,
    ):
        chain = attribute_chain(
            node.func
        )

        if (
            len(chain) >= 2
            and chain[0] == "self"
            and "runtime" in chain
        ):
            runtime_calls.add(
                ".".join(chain)
            )


runtime_methods: set[str] = set()
runtime_attributes: set[str] = set()

for node in ast.walk(
    runtime_tree
):
    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        runtime_methods.add(
            node.name
        )

    if isinstance(
        node,
        ast.Assign,
    ):
        for target in node.targets:
            chain = attribute_chain(
                target
            )

            if (
                len(chain) == 2
                and chain[0] == "self"
            ):
                runtime_attributes.add(
                    chain[1]
                )

    if isinstance(
        node,
        ast.AnnAssign,
    ):
        chain = attribute_chain(
            node.target
        )

        if (
            len(chain) == 2
            and chain[0] == "self"
        ):
            runtime_attributes.add(
                chain[1]
            )


print()
print(
    "=== INTEGRATION RUNTIME ZINCIRLERI ==="
)

for chain in sorted(
    runtime_chains
):
    print(chain)


print()
print(
    "=== INTEGRATION RUNTIME CAGİLARI ==="
)

for call in sorted(
    runtime_calls
):
    print(call)


print()
print(
    "=== JARMIN RUNTIME METOTLARI ==="
)

for method in sorted(
    runtime_methods
):
    print(method)


print()
print(
    "=== JARMIN RUNTIME ALANLARI ==="
)

for attribute in sorted(
    runtime_attributes
):
    print(attribute)


missing_calls: list[str] = []

for call in sorted(
    runtime_calls
):
    method_name = call.split(".")[-1]

    if method_name not in runtime_methods:
        missing_calls.append(
            call
        )


print()
print(
    "=== EKSİK METOT BEKLENTİLERİ ==="
)

if missing_calls:
    for call in missing_calls:
        print(call)
else:
    print(
        "EKSİK_METOT_YOK"
    )


report_path = Path(
    "artifacts/"
    "JARMIN_INTEGRATION_CONTRACT_REPORT.txt"
)

report_lines = [
    "JARMIN INTEGRATION CONTRACT REPORT",
    "",
    "RUNTIME CHAINS",
    *sorted(runtime_chains),
    "",
    "RUNTIME CALLS",
    *sorted(runtime_calls),
    "",
    "RUNTIME METHODS",
    *sorted(runtime_methods),
    "",
    "RUNTIME ATTRIBUTES",
    *sorted(runtime_attributes),
    "",
    "MISSING CALLS",
    *(
        missing_calls
        if missing_calls
        else ["NONE"]
    ),
]

report_path.write_text(
    "\n".join(report_lines),
    encoding="utf-8",
)

print()
print(
    "JARMIN_CONTRACT_ANALYSIS_OK"
)

print(
    "REPORT_PATH",
    report_path
)

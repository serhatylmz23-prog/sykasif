from pathlib import Path
import ast


dosyalar = [
    Path("src/syk_jarmin/jarmin_core.py"),
    Path("src/syk_jarmin/runtime/command_router.py"),
    Path("tests/test_jarmin_core.py"),
]

for path in dosyalar:
    if not path.is_file():
        raise FileNotFoundError(path)

    text = path.read_text(
        encoding="utf-8",
    )

    print()
    print("=" * 78)
    print(path)
    print("=" * 78)

    if path.name == "jarmin_core.py":
        tree = ast.parse(text)

        hedefler = {
            "__init__",
            "process",
            "_reply",
        }

        lines = text.splitlines()

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name in hedefler
            ):
                print()
                print(
                    f"--- {node.name} "
                    f"SATIR {node.lineno}-{node.end_lineno} ---"
                )

                for number in range(
                    node.lineno,
                    node.end_lineno + 1,
                ):
                    print(
                        f"{number:04d}: "
                        f"{lines[number - 1]}"
                    )

    else:
        print(text)


print()
print("KASIF_KOMUT_SOZLESMESI_INCELEME_OK")

from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path

from terminal_v2.scaffold.core.parser import Manifest


ROOT = Path("terminal_v2")
MANIFEST_PATH = ROOT / "scaffold" / "manifest" / "terminal.yml"
TEMPLATE_ROOT = ROOT / "generator" / "templates"
OUTPUT_ROOT = ROOT / "generated"
TEST_ROOT = ROOT / "tests"


DEFAULT_TEMPLATES = {
    "module.py.tpl": '''\
class {{CLASS_NAME}}:
    NAME = "{{MODULE_NAME}}"

    def status(self) -> dict[str, str]:
        return {
            "module": self.NAME,
            "status": "READY",
        }
''',
    "page.html.tpl": '''\
<section
    id="module-{{MODULE_NAME}}"
    class="syk-module"
    data-module="{{MODULE_NAME}}"
>
    <header class="syk-module__header">
        <h2>{{DISPLAY_NAME}}</h2>
        <span class="syk-module__status">HAZIR</span>
    </header>

    <div class="syk-module__content">
        <p>{{DISPLAY_NAME}} modülü Terminal V2 üretim motoru tarafından oluşturuldu.</p>
    </div>
</section>
''',
    "style.css.tpl": '''\
#module-{{MODULE_NAME}} {
    display: grid;
    gap: 1rem;
    min-width: 0;
}

#module-{{MODULE_NAME}} .syk-module__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

#module-{{MODULE_NAME}} .syk-module__content {
    overflow: auto;
}
''',
    "module.js.tpl": '''\
(() => {
    "use strict";

    const moduleName = "{{MODULE_NAME}}";
    const root = document.querySelector(`#module-${moduleName}`);

    if (!root) {
        return;
    }

    root.dataset.runtimeStatus = "ready";

    window.dispatchEvent(
        new CustomEvent("syk:module-ready", {
            detail: {
                module: moduleName,
                status: "READY",
            },
        }),
    );
})();
''',
}


def class_name(module_name: str) -> str:
    return "".join(
        part.capitalize()
        for part in module_name.replace("-", "_").split("_")
        if part
    )


def display_name(module_name: str) -> str:
    return module_name.replace("_", " ").replace("-", " ").title()


def ensure_templates() -> None:
    TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)

    for filename, content in DEFAULT_TEMPLATES.items():
        target = TEMPLATE_ROOT / filename

        if not target.exists():
            target.write_text(content, encoding="utf-8")


def render(template_name: str, module_name: str) -> str:
    source = (TEMPLATE_ROOT / template_name).read_text(encoding="utf-8")

    replacements = {
        "{{MODULE_NAME}}": module_name,
        "{{CLASS_NAME}}": class_name(module_name),
        "{{DISPLAY_NAME}}": display_name(module_name),
    }

    for marker, value in replacements.items():
        source = source.replace(marker, value)

    unresolved = [
        marker
        for marker in ("{{MODULE_NAME}}", "{{CLASS_NAME}}", "{{DISPLAY_NAME}}")
        if marker in source
    ]

    if unresolved:
        raise RuntimeError(
            f"Çözümlenemeyen şablon alanları: {template_name}: {unresolved}"
        )

    return source.rstrip() + "\n"


def generate_module(module_name: str) -> list[Path]:
    module_root = OUTPUT_ROOT / module_name
    module_root.mkdir(parents=True, exist_ok=True)

    targets = {
        module_root / "__init__.py": (
            f'from .{module_name} import {class_name(module_name)}\n\n'
            f'__all__ = ["{class_name(module_name)}"]\n'
        ),
        module_root / f"{module_name}.py": render(
            "module.py.tpl",
            module_name,
        ),
        module_root / f"{module_name}.html": render(
            "page.html.tpl",
            module_name,
        ),
        module_root / f"{module_name}.css": render(
            "style.css.tpl",
            module_name,
        ),
        module_root / f"{module_name}.js": render(
            "module.js.tpl",
            module_name,
        ),
    }

    for target, content in targets.items():
        target.write_text(content, encoding="utf-8")

    return list(targets)


def verify_outputs(modules: list[str]) -> int:
    expected_extensions = {
        ".py",
        ".html",
        ".css",
        ".js",
    }

    total = 0

    for module_name in modules:
        module_root = OUTPUT_ROOT / module_name

        required = [
            module_root / "__init__.py",
            module_root / f"{module_name}.py",
            module_root / f"{module_name}.html",
            module_root / f"{module_name}.css",
            module_root / f"{module_name}.js",
        ]

        missing = [
            str(path)
            for path in required
            if not path.is_file() or path.stat().st_size == 0
        ]

        if missing:
            raise RuntimeError(
                f"Eksik veya boş üretim dosyaları: {missing}"
            )

        produced_extensions = {
            path.suffix
            for path in required
            if path.name != "__init__.py"
        }

        if produced_extensions != expected_extensions:
            raise RuntimeError(
                f"Beklenmeyen dosya türleri: {module_name}: "
                f"{sorted(produced_extensions)}"
            )

        total += len(required)

    return total


def run_tests() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(TEST_ROOT),
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Pytest başarısız. Çıkış kodu: {result.returncode}"
        )


def main() -> int:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(
            f"Manifest bulunamadı: {MANIFEST_PATH}"
        )

    manifest = Manifest.load(MANIFEST_PATH)
    modules = list(dict.fromkeys(manifest.modules))

    if not modules:
        raise RuntimeError("Manifest içinde modül bulunamadı.")

    ensure_templates()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "__init__.py").touch(exist_ok=True)

    print()
    print("=" * 48)
    print("PRODUCTION BUILDER PIPELINE")
    print("=" * 48)

    generated_files: list[Path] = []

    for index, module_name in enumerate(modules, start=1):
        files = generate_module(module_name)
        generated_files.extend(files)
        print(
            f"[{index:02d}/{len(modules):02d}] "
            f"{module_name:<20} {len(files)} DOSYA"
        )

    verified_count = verify_outputs(modules)

    print()
    print(f"MODULE_COUNT   = {len(modules)}")
    print(f"GENERATED_FILE = {len(generated_files)}")
    print(f"VERIFIED_FILE  = {verified_count}")

    compile_ok = compileall.compile_dir(
        str(ROOT),
        quiet=1,
        force=True,
    )

    if not compile_ok:
        raise RuntimeError("Python compileall başarısız.")

    print("COMPILE        = PASS")

    run_tests()

    print()
    print("PYTEST         = PASS")
    print("PRODUCTION_BUILD_ENGINE_READY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

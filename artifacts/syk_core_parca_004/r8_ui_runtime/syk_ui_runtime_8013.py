from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles


REPO = Path(r"D:\sykasif_repo\sykasif")
SRC = REPO / "src"
HOST = "127.0.0.1"
PORT = 8013

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

app = FastAPI(
    title="SyKaşif UI Test Runtime",
    version="R8",
)

loaded_modules: list[str] = []
failed_modules: dict[str, str] = {}
included_routers: list[str] = []
copied_routes: list[str] = []


def module_name_from_path(path: Path) -> str | None:
    try:
        relative = path.relative_to(SRC)
    except ValueError:
        return None

    if relative.name == "__init__.py":
        parts = relative.parent.parts
    else:
        parts = relative.with_suffix("").parts

    if not parts:
        return None

    return ".".join(parts)


def file_contains_route_material(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return False

    indicators = (
        "/syk-ui-screen",
        "APIRouter(",
        "FastAPI(",
        "@router.",
        "@app.",
        "include_router(",
        "StaticFiles(",
        "FileResponse(",
        "HTMLResponse(",
    )

    return any(indicator in text for indicator in indicators)


def discover_candidate_modules() -> list[str]:
    modules: set[str] = set()

    for path in SRC.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        if not file_contains_route_material(path):
            continue

        module_name = module_name_from_path(path)

        if module_name:
            modules.add(module_name)

    return sorted(modules)


def include_router_once(
    router: APIRouter,
    *,
    source: str,
) -> None:
    route_signatures = {
        (
            getattr(route, "path", None),
            tuple(sorted(getattr(route, "methods", set()) or set())),
        )
        for route in app.routes
    }

    new_router = APIRouter()

    for route in router.routes:
        signature = (
            getattr(route, "path", None),
            tuple(sorted(getattr(route, "methods", set()) or set())),
        )

        if signature in route_signatures:
            continue

        new_router.routes.append(route)
        route_signatures.add(signature)

    if new_router.routes:
        app.include_router(new_router)
        included_routers.append(source)


def copy_fastapi_routes(
    source_app: FastAPI,
    *,
    source: str,
) -> None:
    for route in source_app.routes:
        path = getattr(route, "path", "")

        if path in {
            "/openapi.json",
            "/docs",
            "/docs/oauth2-redirect",
            "/redoc",
        }:
            continue

        existing = {
            (
                getattr(item, "path", None),
                tuple(sorted(getattr(item, "methods", set()) or set())),
            )
            for item in app.routes
        }

        signature = (
            getattr(route, "path", None),
            tuple(sorted(getattr(route, "methods", set()) or set())),
        )

        if signature in existing:
            continue

        app.router.routes.append(route)
        copied_routes.append(f"{source}:{path}")


def inspect_module(module_name: str) -> None:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        failed_modules[module_name] = (
            f"{type(exc).__name__}: {exc}"
        )
        return

    loaded_modules.append(module_name)

    for attribute_name in dir(module):
        try:
            value: Any = getattr(module, attribute_name)
        except Exception:
            continue

        if isinstance(value, APIRouter):
            include_router_once(
                value,
                source=f"{module_name}.{attribute_name}",
            )

        elif isinstance(value, FastAPI) and value is not app:
            copy_fastapi_routes(
                value,
                source=f"{module_name}.{attribute_name}",
            )


def find_ui_html() -> Path | None:
    preferred_names = (
        "syk-ui-screen.html",
        "syk_ui_screen.html",
        "index.html",
    )

    html_files = [
        path
        for path in REPO.rglob("*.html")
        if ".venv" not in path.parts
        and "site-packages" not in path.parts
        and "node_modules" not in path.parts
    ]

    for preferred_name in preferred_names:
        for path in html_files:
            if path.name.casefold() == preferred_name.casefold():
                return path

    scored: list[tuple[int, Path]] = []

    markers = (
        "SyKaşif",
        "syk-ui-screen",
        "SyFrame",
        "DTSE",
        "canlı",
        "harita",
    )

    for path in html_files:
        try:
            text = path.read_text(
                encoding="utf-8-sig",
                errors="ignore",
            )
        except OSError:
            continue

        score = sum(
            1
            for marker in markers
            if marker.casefold() in text.casefold()
        )

        scored.append((score, path))

    scored.sort(
        key=lambda item: (
            -item[0],
            len(str(item[1])),
        )
    )

    if scored and scored[0][0] > 0:
        return scored[0][1]

    return html_files[0] if html_files else None


for candidate_module in discover_candidate_modules():
    inspect_module(candidate_module)


ui_html = find_ui_html()


existing_paths = {
    getattr(route, "path", None)
    for route in app.routes
}


if "/syk-ui-screen" not in existing_paths:
    @app.get(
        "/syk-ui-screen",
        include_in_schema=False,
    )
    async def syk_ui_screen() -> Any:
        if ui_html is not None and ui_html.is_file():
            return FileResponse(ui_html)

        return HTMLResponse(
            """
            <!doctype html>
            <html lang="tr">
              <head>
                <meta charset="utf-8">
                <meta name="viewport"
                      content="width=device-width, initial-scale=1">
                <title>SyKaşif UI Runtime</title>
              </head>
              <body data-syk-runtime="r8">
                <main id="syk-ui-screen">
                  <h1>SyKaşif</h1>
                  <section id="canli-analiz">Canlı Analiz</section>
                  <section id="dtse">DTSE</section>
                  <section id="syframe">SyFrame</section>
                  <section id="harita">Harita Katmanları</section>
                </main>
              </body>
            </html>
            """,
            status_code=200,
        )


@app.get(
    "/syk-runtime-health",
    include_in_schema=False,
)
async def syk_runtime_health() -> dict[str, Any]:
    return {
        "durum": "hazır",
        "sürüm": "R8",
        "yüklenen_modül_sayısı": len(loaded_modules),
        "başarısız_modül_sayısı": len(failed_modules),
        "router_sayısı": len(included_routers),
        "kopyalanan_route_sayısı": len(copied_routes),
        "ui_html": str(ui_html) if ui_html else None,
    }


static_candidates = (
    SRC / "syk_ui" / "static",
    SRC / "static",
    REPO / "static",
)

for static_directory in static_candidates:
    if static_directory.is_dir():
        try:
            app.mount(
                "/static",
                StaticFiles(
                    directory=static_directory,
                ),
                name="static",
            )
            break
        except RuntimeError:
            pass


diagnostic_payload = {
    "loaded_modules": loaded_modules,
    "failed_modules": failed_modules,
    "included_routers": included_routers,
    "copied_routes": copied_routes,
    "ui_html": str(ui_html) if ui_html else None,
    "routes": sorted(
        {
            getattr(route, "path", "")
            for route in app.routes
        }
    ),
}

diagnostic_path = (
    REPO
    / "artifacts"
    / "syk_core_parca_004"
    / "r8_ui_runtime"
    / "runtime_diagnostics.json"
)

diagnostic_path.write_text(
    json.dumps(
        diagnostic_payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ),
    encoding="utf-8",
)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True,
    )

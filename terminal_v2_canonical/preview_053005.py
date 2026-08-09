from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parent
UI = ROOT / "ui"

app = FastAPI(
    title="SyKaşif Terminal V2",
    docs_url=None,
    redoc_url=None,
)

app.mount(
    "/ui",
    StaticFiles(directory=str(UI)),
    name="ui",
)


@app.middleware("http")
async def cache_kapat(request: Request, call_next):
    response = await call_next(request)

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


@app.get("/", include_in_schema=False)
async def ana_sayfa():
    return FileResponse(
        UI / "index.html",
        headers={
            "Cache-Control":
            "no-store, no-cache, must-revalidate, max-age=0"
        },
    )


@app.get("/saglik", include_in_schema=False)
async def saglik():
    return {
        "durum": "çevrim içi",
        "sprint": "SPRINT_053_006B",
        "cache": "kapali",
        "arayuz": "kanonik",
    }

from pathlib import Path

from fastapi import FastAPI
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


@app.get("/", include_in_schema=False)
async def ana_sayfa():
    return FileResponse(UI / "index.html")


@app.get("/saglik", include_in_schema=False)
async def saglik():
    return {
        "durum": "çevrim içi",
        "arayuz": "kanonik",
        "dil": "Türkçe",
        "sprint": "SPRINT_053_005",
    }

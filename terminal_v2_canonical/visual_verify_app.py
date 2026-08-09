from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "templates" / "index.html"
STATIC = ROOT / "static"

app = FastAPI(
    title="SyKaşif Terminal V2 Görsel Doğrulama",
    docs_url=None,
    redoc_url=None,
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC)),
    name="static",
)


@app.get("/", include_in_schema=False)
async def ana_sayfa():
    return FileResponse(str(INDEX))


@app.get("/saglik", include_in_schema=False)
async def saglik():
    return {
        "durum": "hazir",
        "amac": "yalniz_gorsel_dogrulama",
        "arayuz": "07_08_2026_kanonik",
    }

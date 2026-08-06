from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles


PWA_DIZINI = (
    Path(__file__).resolve().parents[1]
    / "pwa"
)


def pwa_rotalarini_bagla(
    app: FastAPI,
) -> None:
    if not PWA_DIZINI.is_dir():
        raise RuntimeError(
            f"PWA dizini bulunamadi: {PWA_DIZINI}"
        )

    app.mount(
        "/pwa",
        StaticFiles(
            directory=str(PWA_DIZINI),
            html=True,
        ),
        name="sykasif-pwa",
    )

    @app.get(
        "/mobil",
        include_in_schema=False,
    )
    async def mobil_uygulamaya_git():
        return RedirectResponse(
            url="/pwa/",
            status_code=307,
        )

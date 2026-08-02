"""
SPR-003-UI-0010
SyKaşif Static Routes
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

router = APIRouter()


def mount_static(app):

    app.mount(
        "/syk-ui",
        StaticFiles(directory=STATIC),
        name="syk-ui",
    )

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "static" / "index.html"

router = APIRouter()


@router.get("/syk-ui-screen", include_in_schema=False)
def get_ui_screen() -> FileResponse:
    return FileResponse(
        INDEX,
        media_type="text/html",
    )
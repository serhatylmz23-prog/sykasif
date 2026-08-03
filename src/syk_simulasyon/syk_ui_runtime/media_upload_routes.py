from __future__ import annotations

from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import (
    FileResponse,
    JSONResponse,
)

from .media_upload_service import (
    MediaUploadService,
)


router = APIRouter(
    prefix="/media-analysis",
    tags=["sykasif-media-analysis"],
)

media_upload_service = (
    MediaUploadService()
)


@router.post("")
async def analyze_uploaded_media(
    file: UploadFile = File(...),
    media_id: str | None = Form(
        default=None
    ),
    location: str = Form(
        default="Belirtilmedi"
    ),
) -> dict:
    try:
        content = await file.read()

        return media_upload_service.analyze(
            filename=file.filename
            or "upload.bin",
            content_type=(
                file.content_type
                or "application/octet-stream"
            ),
            content=content,
            media_id=media_id,
            location=location,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error


@router.get("")
def list_media_analyses() -> list[dict]:
    return media_upload_service.list()


@router.get("/{analysis_id}")
def get_media_analysis(
    analysis_id: str,
) -> dict:
    try:
        return (
            media_upload_service
            .read_result(
                analysis_id
            )
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=(
                "Görüntü analizi bulunamadı."
            ),
        ) from error


@router.get("/{analysis_id}/report")
def download_media_report(
    analysis_id: str,
):
    try:
        record = (
            media_upload_service.get(
                analysis_id
            )
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Rapor bulunamadı.",
        ) from error

    path = Path(record.pdf_path)

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="PDF dosyası bulunamadı.",
        )

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=(
            f"{record.media_id}_"
            "sykasif_raporu.pdf"
        ),
    )


@router.get("/{analysis_id}/manifest")
def download_media_manifest(
    analysis_id: str,
):
    try:
        record = (
            media_upload_service.get(
                analysis_id
            )
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail="Manifest bulunamadı.",
        ) from error

    path = Path(record.manifest_path)

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "Manifest dosyası bulunamadı."
            ),
        )

    return JSONResponse(
        content=__import__(
            "json"
        ).loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    )
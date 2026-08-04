from __future__ import annotations

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from .kasif_icon_registry import (
    kasif_icon_registry,
)


router = APIRouter(
    prefix="/kasif-icons",
    tags=["kasif-icon-library"],
)


@router.get("")
def list_kasif_icons(
    group: str | None = None,
    theme: str | None = None,
    enabled_only: bool = True,
) -> dict:
    try:
        icons = kasif_icon_registry.list(
            group=group,
            theme=theme,
            enabled_only=enabled_only,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "icon_count": len(icons),
        "icons": icons,
    }


@router.get("/manifest")
def get_kasif_icon_manifest() -> dict:
    return kasif_icon_registry \
        .snapshot()


@router.get("/groups")
def get_kasif_icon_groups() -> dict:
    groups = kasif_icon_registry.groups()

    return {
        "group_count": len(groups),
        "groups": groups,
    }


@router.get("/assistant")
def get_kasif_assistant_profile() -> dict:
    return kasif_icon_registry \
        .assistant_profile()


@router.get("/search")
def search_kasif_icons(
    q: str = Query(
        min_length=1,
        max_length=100,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> dict:
    icons = kasif_icon_registry.search(
        q,
        limit=limit,
    )

    return {
        "query": q,
        "result_count": len(icons),
        "icons": icons,
    }


@router.post("/reload")
def reload_kasif_icons() -> dict:
    try:
        return kasif_icon_registry \
            .reload()

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@router.get("/{icon_id}")
def get_kasif_icon(
    icon_id: str,
) -> dict:
    try:
        return kasif_icon_registry.get(
            icon_id
        )

    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
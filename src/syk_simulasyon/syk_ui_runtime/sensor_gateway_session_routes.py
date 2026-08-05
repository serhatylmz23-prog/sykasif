from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)
from pydantic import BaseModel, Field

from .sensor_gateway_session_runtime import (
    SensorSessionState,
    sensor_gateway_session_runtime,
)


class SensorSessionCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    source_ids: list[str] = Field(
        min_length=1,
        max_length=64,
    )
    research_id: str | None = Field(
        default=None,
        max_length=180,
    )
    workspace_id: str | None = Field(
        default=None,
        max_length=180,
    )


sensor_gateway_session_router = APIRouter(
    prefix="/api/syk-ui/sensor-sessions",
    tags=["syk-ui-sensor-sessions"],
)


@sensor_gateway_session_router.get("")
def list_sessions(
    research_id: Annotated[
        str | None,
        Query(),
    ] = None,
    workspace_id: Annotated[
        str | None,
        Query(),
    ] = None,
    state: Annotated[
        SensorSessionState | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    sessions = (
        sensor_gateway_session_runtime.list(
            research_id=research_id,
            workspace_id=workspace_id,
            state=state,
        )
    )

    return {
        "count": len(sessions),
        "sessions": [
            sensor_gateway_session_runtime.serialize(
                session
            )
            for session in sessions
        ],
    }


@sensor_gateway_session_router.post(
    "",
    status_code=201,
)
def create_session(
    request: SensorSessionCreateRequest,
) -> dict[str, object]:
    try:
        session = (
            sensor_gateway_session_runtime.create(
                name=request.name,
                source_ids=request.source_ids,
                research_id=request.research_id,
                workspace_id=request.workspace_id,
            )
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return (
        sensor_gateway_session_runtime.serialize(
            session
        )
    )


@sensor_gateway_session_router.get(
    "/{session_id}"
)
def get_session(
    session_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    session = (
        sensor_gateway_session_runtime.get(
            session_id
        )
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sensör oturumu bulunamadı.",
        )

    return (
        sensor_gateway_session_runtime.serialize(
            session
        )
    )


@sensor_gateway_session_router.post(
    "/{session_id}/start"
)
def start_session(
    session_id: str,
) -> dict[str, object]:
    try:
        session = (
            sensor_gateway_session_runtime.start(
                session_id
            )
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sensör oturumu bulunamadı.",
        )

    return (
        sensor_gateway_session_runtime.serialize(
            session
        )
    )


@sensor_gateway_session_router.post(
    "/{session_id}/sync"
)
def sync_session(
    session_id: str,
) -> dict[str, object]:
    try:
        session = (
            sensor_gateway_session_runtime.sync(
                session_id
            )
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sensör oturumu bulunamadı.",
        )

    return (
        sensor_gateway_session_runtime.serialize(
            session
        )
    )


@sensor_gateway_session_router.post(
    "/{session_id}/stop"
)
def stop_session(
    session_id: str,
) -> dict[str, object]:
    try:
        session = (
            sensor_gateway_session_runtime.stop(
                session_id
            )
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sensör oturumu bulunamadı.",
        )

    return (
        sensor_gateway_session_runtime.serialize(
            session
        )
    )
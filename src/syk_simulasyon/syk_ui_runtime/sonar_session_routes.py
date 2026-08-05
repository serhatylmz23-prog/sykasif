from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Query,
)
from pydantic import BaseModel, Field

from .sonar_session_runtime import (
    SonarSessionState,
    sonar_session_runtime,
)


class SonarSessionCreateRequest(BaseModel):
    device_id: str = Field(
        min_length=1,
        max_length=180,
    )
    name: str = Field(
        min_length=1,
        max_length=200,
    )
    research_id: str | None = Field(
        default=None,
        max_length=180,
    )
    workspace_id: str | None = Field(
        default=None,
        max_length=180,
    )
    maximum_priority_depth_m: float = Field(
        default=2.0,
        gt=0.0,
        le=1000.0,
    )


class SonarCaptureRequest(BaseModel):
    frame_count: int = Field(
        default=1,
        ge=1,
        le=250,
    )


sonar_session_router = APIRouter(
    prefix="/api/syk-ui/sonar-sessions",
    tags=["syk-ui-sonar-sessions"],
)


@sonar_session_router.get("")
def list_sessions(
    device_id: Annotated[
        str | None,
        Query(),
    ] = None,
    research_id: Annotated[
        str | None,
        Query(),
    ] = None,
    workspace_id: Annotated[
        str | None,
        Query(),
    ] = None,
    state: Annotated[
        SonarSessionState | None,
        Query(),
    ] = None,
) -> dict[str, object]:
    sessions = sonar_session_runtime.list(
        device_id=device_id,
        research_id=research_id,
        workspace_id=workspace_id,
        state=state,
    )

    return {
        "count": len(sessions),
        "sessions": [
            session.to_dict()
            for session in sessions
        ],
    }


@sonar_session_router.post(
    "",
    status_code=201,
)
def create_session(
    request: SonarSessionCreateRequest,
) -> dict[str, object]:
    try:
        session = sonar_session_runtime.create(
            device_id=request.device_id,
            name=request.name,
            research_id=request.research_id,
            workspace_id=request.workspace_id,
            maximum_priority_depth_m=(
                request.maximum_priority_depth_m
            ),
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

    return session.to_dict()


@sonar_session_router.get(
    "/{session_id}"
)
def get_session(
    session_id: Annotated[
        str,
        Path(min_length=1),
    ],
) -> dict[str, object]:
    session = sonar_session_runtime.get(
        session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sonar oturumu bulunamadı.",
        )

    return session.to_dict()


@sonar_session_router.post(
    "/{session_id}/start"
)
def start_session(
    session_id: str,
) -> dict[str, object]:
    try:
        session = sonar_session_runtime.start(
            session_id
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sonar oturumu bulunamadı.",
        )

    return session.to_dict()


@sonar_session_router.post(
    "/{session_id}/capture"
)
def capture_session(
    session_id: str,
    request: SonarCaptureRequest,
) -> dict[str, object]:
    try:
        session = sonar_session_runtime.capture(
            session_id,
            frame_count=request.frame_count,
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
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sonar oturumu bulunamadı.",
        )

    return session.to_dict()


@sonar_session_router.post(
    "/{session_id}/stop"
)
def stop_session(
    session_id: str,
) -> dict[str, object]:
    try:
        session = sonar_session_runtime.stop(
            session_id
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sonar oturumu bulunamadı.",
        )

    return session.to_dict()
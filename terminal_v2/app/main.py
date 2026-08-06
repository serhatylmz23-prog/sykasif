from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from terminal_v2.core.api import router as api_router
from terminal_v2.core.connection_registry import registry
from terminal_v2.core.sse import router as sse_router
from terminal_v2.core.device_routes import router as device_router
from terminal_v2.core.panel_routes import router as panel_router
from terminal_v2.core.panel_broadcast_routes import router as panel_broadcast_router
from terminal_v2.core.runtime_state_routes import router as runtime_state_router
from terminal_v2.core.module_card_routes import router as module_card_router
from terminal_v2.core.tablet_validation import (
    tablet_validation_registry,
)
from terminal_v2.core.tablet_validation_routes import (
    validation_page,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "index.html"
STATIC_PATH = ROOT / "static"


class TabletAckRequest(BaseModel):
    token: str = Field(min_length=16, max_length=128)
    viewport_width: int = Field(ge=240, le=10000)
    viewport_height: int = Field(ge=240, le=10000)
    touch_supported: bool
    event_source_supported: bool
    sse_connected: bool


def create_app() -> FastAPI:
    app = FastAPI(
        title="SYK Terminal V2",
        version="2.0.0",
    )

    app.include_router(api_router)
    app.include_router(sse_router)
    app.include_router(device_router)
    app.include_router(panel_router)
    app.include_router(panel_broadcast_router)
    app.include_router(runtime_state_router)
    app.include_router(module_card_router)

    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_PATH)),
        name="static",
    )

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(
            content=TEMPLATE_PATH.read_text(
                encoding="utf-8",
            ),
            status_code=200,
        )

    @app.get(
        "/tablet-validation/{token}",
        response_class=HTMLResponse,
    )
    async def tablet_validation_page(
        token: str,
    ) -> HTMLResponse:
        return await validation_page(token)

    @app.post("/api/v2/tablet-validation/session")
    async def create_tablet_validation_session(
        request: Request,
    ) -> dict[str, object]:
        session = await tablet_validation_registry.create()

        return {
            "token": session.token,
            "validation_path": (
                f"/tablet-validation/{session.token}"
            ),
            "status_path": (
                "/api/v2/tablet-validation/session/"
                f"{session.token}"
            ),
            "status": "WAITING",
        }

    @app.get(
        "/api/v2/tablet-validation/session/{token}"
    )
    async def tablet_validation_status(
        token: str,
    ) -> dict[str, object]:
        session = await tablet_validation_registry.get(token)

        if session is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Tablet doğrulama oturumu bulunamadı."
                ),
            )

        return session.export()

    @app.post("/api/v2/tablet-validation/ack")
    async def acknowledge_tablet_validation(
        payload: TabletAckRequest,
        request: Request,
    ) -> dict[str, object]:
        client_host = (
            request.client.host
            if request.client is not None
            else "unknown"
        )

        session = await tablet_validation_registry.acknowledge(
            token=payload.token,
            client_host=client_host,
            user_agent=request.headers.get(
                "user-agent",
                "unknown",
            ),
            viewport_width=payload.viewport_width,
            viewport_height=payload.viewport_height,
            touch_supported=payload.touch_supported,
            event_source_supported=(
                payload.event_source_supported
            ),
            sse_connected=payload.sse_connected,
        )

        if session is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Tablet doğrulama oturumu bulunamadı."
                ),
            )

        return session.export()

    @app.delete(
        "/api/v2/tablet-validation/session/{token}"
    )
    async def delete_tablet_validation_session(
        token: str,
    ) -> dict[str, object]:
        removed = await tablet_validation_registry.reset(token)

        return {
            "removed": removed,
            "token": token,
        }

    @app.get("/health")
    async def health() -> dict[str, object]:
        await registry.remove_stale()

        connection_data = await registry.snapshot()

        return {
            "status": "ok",
            "terminal": "v2",
            "runtime": "ONLINE",
            "port": 8013,
            "active_connections": connection_data[
                "active_connections"
            ],
            "active_tablet": connection_data[
                "active_tablet"
            ],
            "active_desktop": connection_data[
                "active_desktop"
            ],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @app.get("/api/v2/status")
    async def terminal_status() -> dict[str, object]:
        await registry.remove_stale()

        connection_data = await registry.snapshot()

        return {
            "terminal": {
                "name": "SyKaşif Terminal V2",
                "version": "2.0.0",
                "status": "ONLINE",
            },
            "runtime": {
                "status": "ONLINE",
                "port": 8013,
            },
            "connection": {
                "tablet": (
                    connection_data["active_tablet"] > 0
                ),
                "desktop": (
                    connection_data["active_desktop"] > 0
                ),
                "mobile": (
                    connection_data["active_mobile"] > 0
                ),
                "active_streams": connection_data[
                    "active_connections"
                ],
                "active_tablets": connection_data[
                    "active_tablet"
                ],
                "active_desktops": connection_data[
                    "active_desktop"
                ],
                "total_streams": connection_data[
                    "total_connections"
                ],
                "transport": "SSE",
                "stream": "ONLINE",
            },
            "modules": [
                "dashboard",
                "analysis",
                "evidence",
                "reports",
                "map",
                "ai",
                "settings",
                "notifications",
            ],
            "timestamp": datetime.now(UTC).isoformat(),
        }

    return app


app = create_app()

# === SYKASIF_PWA_RUNTIME_BAGLANTISI_BASLANGIC ===
from terminal_v2.app.pwa_routes import (
    pwa_rotalarini_bagla as _pwa_rotalarini_bagla,
)

_pwa_rotalarini_bagla(app)
# === SYKASIF_PWA_RUNTIME_BAGLANTISI_BITIS ===

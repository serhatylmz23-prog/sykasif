from __future__ import annotations

from html import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from terminal_v2.core.tablet_validation import (
    tablet_validation_registry,
)


router = APIRouter(
    prefix="/api/v2/tablet-validation",
    tags=["Terminal V2 Tablet Validation"],
)


class TabletAckRequest(BaseModel):
    token: str = Field(min_length=16, max_length=128)
    viewport_width: int = Field(ge=240, le=10000)
    viewport_height: int = Field(ge=240, le=10000)
    touch_supported: bool
    event_source_supported: bool
    sse_connected: bool


@router.post("/session")
async def create_session(
    request: Request,
) -> dict[str, object]:
    session = await tablet_validation_registry.create()

    host = request.url.hostname or "127.0.0.1"
    port = request.url.port or 8013

    return {
        "token": session.token,
        "validation_path": (
            f"/tablet-validation/{session.token}"
        ),
        "validation_url": (
            f"http://{host}:{port}"
            f"/tablet-validation/{session.token}"
        ),
        "status_path": (
            f"/api/v2/tablet-validation/"
            f"session/{session.token}"
        ),
        "status": "WAITING",
    }


@router.get("/session/{token}")
async def session_status(
    token: str,
) -> dict[str, object]:
    session = await tablet_validation_registry.get(token)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Tablet doğrulama oturumu bulunamadı.",
        )

    return session.export()


@router.post("/ack")
async def acknowledge(
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
            detail="Tablet doğrulama oturumu bulunamadı.",
        )

    return session.export()


@router.delete("/session/{token}")
async def delete_session(
    token: str,
) -> dict[str, object]:
    removed = await tablet_validation_registry.reset(token)

    return {
        "removed": removed,
        "token": token,
    }


@router.get(
    "/page/{token}",
    response_class=HTMLResponse,
)
async def validation_page_api(
    token: str,
) -> HTMLResponse:
    return await validation_page(token)


async def validation_page(
    token: str,
) -> HTMLResponse:
    session = await tablet_validation_registry.get(token)

    if session is None:
        return HTMLResponse(
            content=(
                "<h1>Doğrulama oturumu bulunamadı.</h1>"
            ),
            status_code=404,
        )

    safe_token = escape(token)

    html = f"""
<!doctype html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width,initial-scale=1,viewport-fit=cover"
    >
    <title>SyKaşif Tablet Doğrulama</title>

    <style>
        :root {{
            color-scheme: dark;
            font-family: "Segoe UI", system-ui, sans-serif;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            min-height: 100vh;
            margin: 0;
            display: grid;
            place-items: center;
            padding: 24px;
            color: #edf3f4;
            background:
                radial-gradient(
                    circle at top,
                    rgba(82, 194, 220, .16),
                    transparent 40%
                ),
                #090c0e;
        }}

        main {{
            width: min(100%, 620px);
            padding: 28px;
            border: 1px solid rgba(180, 220, 230, .18);
            border-radius: 22px;
            background: rgba(20, 25, 28, .94);
            box-shadow: 0 30px 80px rgba(0, 0, 0, .38);
        }}

        h1 {{
            margin: 0;
            font-size: clamp(1.7rem, 7vw, 3rem);
        }}

        p {{
            color: #9fb0b6;
            line-height: 1.65;
        }}

        .status {{
            margin-top: 22px;
            padding: 18px;
            border-radius: 15px;
            background: rgba(255, 255, 255, .045);
        }}

        .status strong {{
            display: block;
            color: #63dba5;
            font-size: 1.1rem;
        }}

        .status small {{
            display: block;
            margin-top: 8px;
            color: #9fb0b6;
        }}

        button {{
            width: 100%;
            min-height: 54px;
            margin-top: 20px;
            border: 1px solid rgba(92, 211, 238, .35);
            border-radius: 14px;
            color: #f4fbfc;
            background: rgba(92, 211, 238, .12);
            font-weight: 700;
        }}
    </style>
</head>

<body>
    <main>
        <p>SYKAŞİF TERMINAL V2</p>
        <h1>Tablet / LAN Doğrulaması</h1>

        <p>
            Bu sayfa tabletin bilgisayardaki Terminal V2
            çalışma alanına yerel ağ üzerinden erişebildiğini
            doğrular.
        </p>

        <div class="status">
            <strong id="status">SSE bağlantısı kuruluyor…</strong>
            <small id="detail">Terminal yanıtı bekleniyor.</small>
        </div>

        <button id="ack-button" type="button" disabled>
            TABLETİ DOĞRULA
        </button>
    </main>

    <script>
        (() => {{
            "use strict";

            const token = {safe_token!r};
            const status = document.getElementById("status");
            const detail = document.getElementById("detail");
            const button = document.getElementById("ack-button");

            let sseConnected = false;

            const source = new EventSource("/api/v2/events");

            source.addEventListener("open", () => {{
                sseConnected = true;
                status.textContent = "SSE V2 BAĞLANDI";
                detail.textContent =
                    "Canlı akış hazır. Doğrulama düğmesine basın.";
                button.disabled = false;
            }});

            source.addEventListener("error", () => {{
                sseConnected = false;
                status.textContent = "SSE YENİDEN BAĞLANIYOR";
                detail.textContent =
                    "Bilgisayar ve tablet aynı ağda olmalıdır.";
                button.disabled = true;
            }});

            button.addEventListener("click", async () => {{
                button.disabled = true;
                status.textContent = "DOĞRULANIYOR";

                const response = await fetch(
                    "/api/v2/tablet-validation/ack",
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json",
                        }},
                        body: JSON.stringify({{
                            token,
                            viewport_width: window.innerWidth,
                            viewport_height: window.innerHeight,
                            touch_supported: (
                                navigator.maxTouchPoints > 0
                                || "ontouchstart" in window
                            ),
                            event_source_supported: (
                                "EventSource" in window
                            ),
                            sse_connected: sseConnected,
                        }}),
                    }},
                );

                if (!response.ok) {{
                    status.textContent = "DOĞRULAMA BAŞARISIZ";
                    detail.textContent =
                        `HTTP ${{response.status}}`;
                    button.disabled = false;
                    return;
                }}

                const payload = await response.json();

                if (payload.digital_checks_passed) {{
                    status.textContent =
                        "TABLET / LAN DOĞRULAMASI BAŞARILI";

                    detail.textContent =
                        `${{payload.viewport_width}}×` +
                        `${{payload.viewport_height}} · ` +
                        `${{payload.client_host}}`;
                }} else {{
                    status.textContent =
                        "DOĞRULAMA EKSİK";

                    detail.textContent =
                        "SSE veya tarayıcı yetenekleri doğrulanamadı.";

                    button.disabled = false;
                }}
            }});

            window.addEventListener("beforeunload", () => {{
                source.close();
            }});
        }})();
    </script>
</body>
</html>
"""

    return HTMLResponse(
        content=html,
        status_code=200,
    )

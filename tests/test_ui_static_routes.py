"""
SPR-003-UI-0016
SyKaşif Static Routes Test
"""

from fastapi import FastAPI

from syk_ui.static_routes import mount_static


def test_ui_static_route_registration():
    app = FastAPI()

    mount_static(app)

    assert any(route.path == "/syk-ui" for route in app.routes)

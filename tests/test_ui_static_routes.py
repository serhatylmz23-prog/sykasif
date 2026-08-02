from fastapi import FastAPI

from syk_simulasyon.syk_ui_runtime.static_routes import mount_static


def test_ui_static_route_registration():
    app = FastAPI()

    mount_static(app)

    assert any(route.path == "/syk-ui" for route in app.routes)
from fastapi import FastAPI

from .api_routes import router as api_router
from .screen_routes import router as screen_router
from .static_routes import mount_static


def install_ui(app: FastAPI) -> FastAPI:
    mount_static(app)
    app.include_router(api_router)
    app.include_router(screen_router)
    return app
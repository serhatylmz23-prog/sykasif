from fastapi import FastAPI

from .module_catalog_routes import router as module_catalog_router
from .screen_routes import router as screen_router


def create_application() -> FastAPI:
    app = FastAPI(
        title="SyKaşif Terminal V2",
        version="2.0",
    )

    app.include_router(screen_router)
    app.include_router(module_catalog_router)

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "runtime": "syk-ui-runtime",
        }

    return app


app = create_application()

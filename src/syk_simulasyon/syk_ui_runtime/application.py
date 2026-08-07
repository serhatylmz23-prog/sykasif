from fastapi import FastAPI

from .screen_routes import router as screen_router


def create_application() -> FastAPI:
    app = FastAPI(
        title="SyKaşif Terminal V2",
        version="2.0",
    )

    app.include_router(screen_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_application()

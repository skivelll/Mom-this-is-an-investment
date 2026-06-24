from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from sqlalchemy import text

from app.api.router import register_api_routes
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.session import engine

settings = get_settings()
cors_allow_origins = [
    origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mom-this-is-an-investment",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
        return {"status": "ok", "database": "ok"}

    if settings.enable_metrics:
        app.mount("/metrics", make_asgi_app())

    register_api_routes(app, prefix=settings.api_prefix)
    return app


app = create_app()

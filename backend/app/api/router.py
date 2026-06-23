from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.catalog_requests import moderation_router
from app.api.routes.catalog_requests import router as catalog_requests_router
from app.api.routes.collections import router as collections_router
from app.api.routes.wishlist import router as wishlist_router


def register_api_routes(app: FastAPI, *, prefix: str) -> None:
    app.include_router(admin_router, prefix=prefix)
    app.include_router(auth_router, prefix=prefix)
    app.include_router(catalog_router, prefix=prefix)
    app.include_router(catalog_requests_router, prefix=prefix)
    app.include_router(collections_router, prefix=prefix)
    app.include_router(moderation_router, prefix=prefix)
    app.include_router(wishlist_router, prefix=prefix)

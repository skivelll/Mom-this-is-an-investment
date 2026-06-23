from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.item import CatalogItem, CatalogStatus
from app.models.user import User, UserRole
from app.models.variant import CatalogVariant
from app.repositories.catalog import CatalogItemRepository, CatalogVariantRepository

CATALOG_EDITOR_ROLES = {
    UserRole.SENIOR_MODERATOR,
    UserRole.ADMIN,
}


@dataclass(slots=True)
class CreateCatalogItemCommand:
    category_id: UUID
    canonical_title: str
    normalized_title: str
    description: str | None = None
    release_year: int | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE


@dataclass(slots=True)
class CreateCatalogVariantCommand:
    catalog_item_id: UUID
    canonical_title: str
    normalized_title: str
    sku: str | None = None
    barcode: str | None = None
    release_date: date | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._items = CatalogItemRepository(session)
        self._variants = CatalogVariantRepository(session)

    async def get_item(self, item_id: UUID) -> CatalogItem:
        item = await self._items.get_by_id(item_id)
        if item is None:
            raise NotFoundError("Catalog item was not found.")
        return item

    async def get_variant(self, variant_id: UUID) -> CatalogVariant:
        variant = await self._variants.get_by_id(variant_id)
        if variant is None:
            raise NotFoundError("Catalog variant was not found.")
        return variant

    async def search_items(
        self,
        *,
        query: str | None = None,
        category_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CatalogItem]:
        return await self._items.search(
            query=query,
            category_id=category_id,
            limit=limit,
            offset=offset,
        )

    async def search_variants(
        self,
        *,
        query: str | None = None,
        category_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CatalogVariant]:
        return await self._variants.search(
            query=query,
            category_id=category_id,
            limit=limit,
            offset=offset,
        )

    async def create_item(
        self,
        *,
        actor: User,
        command: CreateCatalogItemCommand,
    ) -> CatalogItem:
        self._ensure_catalog_editor(actor)

        async with self._session.begin():
            return await self._items.create(
                CatalogItem(
                    category_id=command.category_id,
                    canonical_title=command.canonical_title,
                    normalized_title=command.normalized_title,
                    description=command.description,
                    release_year=command.release_year,
                    status=command.status,
                    created_by_id=actor.id,
                    updated_by_id=actor.id,
                ),
            )

    async def create_variant(
        self,
        *,
        actor: User,
        command: CreateCatalogVariantCommand,
    ) -> CatalogVariant:
        self._ensure_catalog_editor(actor)

        async with self._session.begin():
            item = await self._items.get_by_id(command.catalog_item_id)
            if item is None:
                raise NotFoundError("Catalog item was not found.")

            return await self._variants.create(
                CatalogVariant(
                    catalog_item_id=item.id,
                    canonical_title=command.canonical_title,
                    normalized_title=command.normalized_title,
                    sku=command.sku,
                    barcode=command.barcode,
                    release_date=command.release_date,
                    status=command.status,
                    created_by_id=actor.id,
                    updated_by_id=actor.id,
                ),
            )

    def _ensure_catalog_editor(self, user: User) -> None:
        if not user.is_active or user.role not in CATALOG_EDITOR_ROLES:
            raise ForbiddenError("Senior moderator permissions are required.")

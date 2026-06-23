from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import CatalogItem
from app.models.variant import CatalogVariant


class CatalogItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: UUID) -> CatalogItem | None:
        return await self._session.get(CatalogItem, item_id)

    async def list_by_ids(self, item_ids: set[UUID]) -> list[CatalogItem]:
        if not item_ids:
            return []

        statement = select(CatalogItem).where(CatalogItem.id.in_(item_ids))
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def search(
        self,
        *,
        query: str | None = None,
        category_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CatalogItem]:
        statement = select(CatalogItem).order_by(CatalogItem.canonical_title.asc())
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(
                    CatalogItem.canonical_title.ilike(pattern),
                    CatalogItem.normalized_title.ilike(pattern),
                ),
            )
        if category_id is not None:
            statement = statement.where(CatalogItem.category_id == category_id)

        result = await self._session.execute(statement.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def create(self, item: CatalogItem) -> CatalogItem:
        self._session.add(item)
        await self._session.flush()
        return item


class CatalogVariantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, variant_id: UUID) -> CatalogVariant | None:
        return await self._session.get(CatalogVariant, variant_id)

    async def search(
        self,
        *,
        query: str | None = None,
        category_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CatalogVariant]:
        statement = (
            select(CatalogVariant)
            .join(CatalogItem)
            .order_by(
                CatalogVariant.canonical_title.asc(),
            )
        )
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(
                    CatalogVariant.canonical_title.ilike(pattern),
                    CatalogVariant.normalized_title.ilike(pattern),
                    CatalogItem.canonical_title.ilike(pattern),
                    CatalogItem.normalized_title.ilike(pattern),
                ),
            )
        if category_id is not None:
            statement = statement.where(CatalogItem.category_id == category_id)

        result = await self._session.execute(statement.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_by_id_for_item(
        self,
        *,
        variant_id: UUID,
        catalog_item_id: UUID,
    ) -> CatalogVariant | None:
        statement = select(CatalogVariant).where(
            CatalogVariant.id == variant_id,
            CatalogVariant.catalog_item_id == catalog_item_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, variant: CatalogVariant) -> CatalogVariant:
        self._session.add(variant)
        await self._session.flush()
        return variant

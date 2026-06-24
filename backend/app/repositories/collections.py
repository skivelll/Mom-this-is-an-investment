from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collections import Collection, CollectionItem


class CollectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, collection: Collection) -> Collection:
        self._session.add(collection)
        await self._session.flush()
        return collection

    async def get_owned(self, *, collection_id: UUID, owner_id: UUID) -> Collection | None:
        statement = select(Collection).where(
            Collection.id == collection_id,
            Collection.owner_id == owner_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_owned(self, *, owner_id: UUID) -> list[Collection]:
        statement = (
            select(Collection)
            .where(Collection.owner_id == owner_id)
            .order_by(Collection.created_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def delete(self, collection: Collection) -> None:
        await self._session.delete(collection)
        await self._session.flush()


class CollectionItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: CollectionItem) -> CollectionItem:
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_owned(
        self,
        *,
        item_id: UUID,
        owner_id: UUID,
    ) -> CollectionItem | None:
        statement = (
            select(CollectionItem)
            .join(Collection)
            .where(CollectionItem.id == item_id, Collection.owner_id == owner_id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, item_id: UUID) -> CollectionItem | None:
        return await self._session.get(CollectionItem, item_id)

    async def list_for_collection(
        self,
        *,
        collection_id: UUID,
        owner_id: UUID,
    ) -> list[CollectionItem]:
        statement = (
            select(CollectionItem)
            .join(Collection)
            .where(CollectionItem.collection_id == collection_id, Collection.owner_id == owner_id)
            .order_by(CollectionItem.created_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def delete(self, item: CollectionItem) -> None:
        await self._session.delete(item)
        await self._session.flush()

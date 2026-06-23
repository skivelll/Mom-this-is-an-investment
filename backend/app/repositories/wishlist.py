from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wishlist import WishlistItem, WishlistStatus


class WishlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: WishlistItem) -> WishlistItem:
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_owned(self, *, item_id: UUID, user_id: UUID) -> WishlistItem | None:
        statement = select(WishlistItem).where(
            WishlistItem.id == item_id,
            WishlistItem.user_id == user_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_owned(self, *, user_id: UUID) -> list[WishlistItem]:
        statement = (
            select(WishlistItem)
            .where(WishlistItem.user_id == user_id)
            .order_by(WishlistItem.priority.desc(), WishlistItem.created_at.desc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def delete(self, item: WishlistItem) -> None:
        await self._session.delete(item)
        await self._session.flush()

    async def list_by_request_id(self, request_id: UUID) -> list[WishlistItem]:
        statement = select(WishlistItem).where(
            WishlistItem.catalog_request_id == request_id,
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def relink_request_items_to_variant(
        self,
        *,
        request_id: UUID,
        variant_id: UUID,
    ) -> list[WishlistItem]:
        items = await self.list_by_request_id(request_id)
        for item in items:
            item.catalog_variant_id = variant_id
            item.catalog_request_id = None
            item.status = WishlistStatus.ACTIVE
        await self._session.flush()
        return items

    async def reject_request_items(self, request_id: UUID) -> list[WishlistItem]:
        items = await self.list_by_request_id(request_id)
        for item in items:
            item.status = WishlistStatus.REJECTED
        await self._session.flush()
        return items

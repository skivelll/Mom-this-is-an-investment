from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.models.wishlist import WishlistItem, WishlistStatus
from app.repositories.catalog import CatalogVariantRepository
from app.repositories.moderation import CatalogRequestRepository
from app.repositories.wishlist import WishlistRepository


@dataclass(slots=True)
class CreateWishlistItemCommand:
    catalog_variant_id: UUID | None = None
    catalog_request_id: UUID | None = None
    target_price: Decimal | None = None
    currency: str | None = None
    source_url: str | None = None
    priority: int = 0
    status: WishlistStatus = WishlistStatus.ACTIVE
    comment: str | None = None


@dataclass(slots=True)
class UpdateWishlistItemCommand:
    target_price: Decimal | None = None
    currency: str | None = None
    source_url: str | None = None
    priority: int | None = None
    status: WishlistStatus | None = None
    comment: str | None = None


class WishlistService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._wishlist = WishlistRepository(session)
        self._variants = CatalogVariantRepository(session)
        self._requests = CatalogRequestRepository(session)

    async def list_items(self, *, user: User) -> list[WishlistItem]:
        return await self._wishlist.list_owned(user_id=user.id)

    async def get_item(self, *, user: User, item_id: UUID) -> WishlistItem:
        item = await self._wishlist.get_owned(item_id=item_id, user_id=user.id)
        if item is None:
            raise NotFoundError("Wishlist item was not found.")
        return item

    async def create_item(self, *, user: User, command: CreateWishlistItemCommand) -> WishlistItem:
        if (command.catalog_variant_id is None) == (command.catalog_request_id is None):
            raise ConflictError("Exactly one wishlist target is required.")

        async with self._session.begin():
            status = command.status
            if command.catalog_variant_id is not None:
                variant = await self._variants.get_by_id(command.catalog_variant_id)
                if variant is None:
                    raise NotFoundError("Catalog variant was not found.")
                status = WishlistStatus.ACTIVE
            if command.catalog_request_id is not None:
                request = await self._requests.get_by_id_for_user(
                    request_id=command.catalog_request_id,
                    user_id=user.id,
                )
                if request is None:
                    raise NotFoundError("Catalog request was not found.")
                status = WishlistStatus.PENDING_MODERATION

            return await self._wishlist.create(
                WishlistItem(
                    user_id=user.id,
                    catalog_variant_id=command.catalog_variant_id,
                    catalog_request_id=command.catalog_request_id,
                    target_price=command.target_price,
                    currency=command.currency,
                    source_url=command.source_url,
                    priority=command.priority,
                    status=status,
                    comment=command.comment,
                ),
            )

    async def update_item(
        self,
        *,
        user: User,
        item_id: UUID,
        command: UpdateWishlistItemCommand,
    ) -> WishlistItem:
        async with self._session.begin():
            item = await self.get_item(user=user, item_id=item_id)
            if command.target_price is not None:
                item.target_price = command.target_price
            if command.currency is not None:
                item.currency = command.currency
            if command.source_url is not None:
                item.source_url = command.source_url
            if command.priority is not None:
                item.priority = command.priority
            if command.status is not None:
                item.status = command.status
            if command.comment is not None:
                item.comment = command.comment
            await self._session.flush()
            return item

    async def delete_item(self, *, user: User, item_id: UUID) -> None:
        async with self._session.begin():
            item = await self.get_item(user=user, item_id=item_id)
            await self._wishlist.delete(item)

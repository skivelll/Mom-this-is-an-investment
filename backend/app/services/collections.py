from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.collections import Collection, CollectionItem, CollectionVisibility, ItemCondition
from app.models.user import User
from app.repositories.catalog import CatalogVariantRepository
from app.repositories.collections import CollectionItemRepository, CollectionRepository


@dataclass(slots=True)
class CreateCollectionCommand:
    name: str
    description: str | None = None
    visibility: CollectionVisibility = CollectionVisibility.PRIVATE


@dataclass(slots=True)
class UpdateCollectionCommand:
    name: str | None = None
    description: str | None = None
    visibility: CollectionVisibility | None = None


@dataclass(slots=True)
class AddCollectionItemCommand:
    catalog_variant_id: UUID
    condition: ItemCondition | None = None
    quantity: int = 1
    purchase_price: Decimal | None = None
    purchase_currency: str | None = None
    purchase_date: date | None = None
    comment: str | None = None


class CollectionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._collections = CollectionRepository(session)
        self._items = CollectionItemRepository(session)
        self._variants = CatalogVariantRepository(session)

    async def list_collections(self, *, user: User) -> list[Collection]:
        return await self._collections.list_owned(owner_id=user.id)

    async def get_collection(self, *, user: User, collection_id: UUID) -> Collection:
        collection = await self._collections.get_owned(
            collection_id=collection_id, owner_id=user.id
        )
        if collection is None:
            raise NotFoundError("Collection was not found.")
        return collection

    async def create_collection(
        self, *, user: User, command: CreateCollectionCommand
    ) -> Collection:
        async with self._session.begin():
            return await self._collections.create(
                Collection(
                    owner_id=user.id,
                    name=command.name,
                    description=command.description,
                    visibility=command.visibility,
                ),
            )

    async def update_collection(
        self,
        *,
        user: User,
        collection_id: UUID,
        command: UpdateCollectionCommand,
    ) -> Collection:
        async with self._session.begin():
            collection = await self.get_collection(user=user, collection_id=collection_id)
            if command.name is not None:
                collection.name = command.name
            if command.description is not None:
                collection.description = command.description
            if command.visibility is not None:
                collection.visibility = command.visibility
            await self._session.flush()
            return collection

    async def delete_collection(self, *, user: User, collection_id: UUID) -> None:
        async with self._session.begin():
            collection = await self.get_collection(user=user, collection_id=collection_id)
            await self._collections.delete(collection)

    async def list_items(self, *, user: User, collection_id: UUID) -> list[CollectionItem]:
        await self.get_collection(user=user, collection_id=collection_id)
        return await self._items.list_for_collection(collection_id=collection_id, owner_id=user.id)

    async def add_item(
        self,
        *,
        user: User,
        collection_id: UUID,
        command: AddCollectionItemCommand,
    ) -> CollectionItem:
        async with self._session.begin():
            await self.get_collection(user=user, collection_id=collection_id)
            variant = await self._variants.get_by_id(command.catalog_variant_id)
            if variant is None:
                raise NotFoundError("Catalog variant was not found.")

            return await self._items.create(
                CollectionItem(
                    collection_id=collection_id,
                    catalog_variant_id=command.catalog_variant_id,
                    condition=command.condition,
                    quantity=command.quantity,
                    purchase_price=command.purchase_price,
                    purchase_currency=command.purchase_currency,
                    purchase_date=command.purchase_date,
                    comment=command.comment,
                ),
            )

    async def delete_item(self, *, user: User, item_id: UUID) -> None:
        async with self._session.begin():
            item = await self._items.get_owned(item_id=item_id, owner_id=user.id)
            if item is None:
                raise NotFoundError("Collection item was not found.")
            await self._items.delete(item)

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import AttributeDefinition, Category
from app.models.reference import ReferenceEntity


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, category: Category) -> Category:
        self._session.add(category)
        await self._session.flush()
        return category

    async def get_by_id(self, category_id: UUID) -> Category | None:
        return await self._session.get(Category, category_id)

    async def list_all(self) -> list[Category]:
        result = await self._session.execute(select(Category).order_by(Category.slug.asc()))
        return list(result.scalars().all())


class AttributeDefinitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, definition: AttributeDefinition) -> AttributeDefinition:
        self._session.add(definition)
        await self._session.flush()
        return definition

    async def get_by_id(self, definition_id: UUID) -> AttributeDefinition | None:
        return await self._session.get(AttributeDefinition, definition_id)

    async def list_for_category(self, category_id: UUID) -> list[AttributeDefinition]:
        statement = (
            select(AttributeDefinition)
            .where(AttributeDefinition.category_id == category_id)
            .order_by(AttributeDefinition.sort_order.asc(), AttributeDefinition.code.asc())
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())


class ReferenceEntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, reference: ReferenceEntity) -> ReferenceEntity:
        self._session.add(reference)
        await self._session.flush()
        return reference

    async def get_by_id(self, reference_id: UUID) -> ReferenceEntity | None:
        return await self._session.get(ReferenceEntity, reference_id)

    async def list_all(self) -> list[ReferenceEntity]:
        statement = select(ReferenceEntity).order_by(
            ReferenceEntity.type.asc(),
            ReferenceEntity.canonical_name.asc(),
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

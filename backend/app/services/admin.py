from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.category import AttributeDefinition, AttributeValueType, Category
from app.models.reference import ReferenceEntity, ReferenceType
from app.models.user import User, UserRole
from app.repositories.admin import (
    AttributeDefinitionRepository,
    CategoryRepository,
    ReferenceEntityRepository,
)


@dataclass(slots=True)
class CreateCategoryCommand:
    name: str
    slug: str
    description: str | None = None
    is_active: bool = True


@dataclass(slots=True)
class CreateAttributeDefinitionCommand:
    category_id: UUID
    code: str
    name: str
    value_type: AttributeValueType
    reference_type: ReferenceType | None = None
    is_required: bool = False
    is_filterable: bool = False
    is_searchable: bool = False
    is_variant_attribute: bool = False
    sort_order: int = 0
    validation_rules: dict[str, Any] | None = None


@dataclass(slots=True)
class CreateReferenceEntityCommand:
    type: ReferenceType
    canonical_name: str
    normalized_name: str


class AdminCatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._categories = CategoryRepository(session)
        self._attributes = AttributeDefinitionRepository(session)
        self._references = ReferenceEntityRepository(session)

    async def list_categories(self) -> list[Category]:
        return await self._categories.list_all()

    async def create_category(self, *, actor: User, command: CreateCategoryCommand) -> Category:
        self._ensure_admin(actor)
        async with self._session.begin():
            return await self._categories.create(
                Category(
                    name=command.name,
                    slug=command.slug,
                    description=command.description,
                    is_active=command.is_active,
                ),
            )

    async def list_attributes(self, *, category_id: UUID) -> list[AttributeDefinition]:
        return await self._attributes.list_for_category(category_id)

    async def create_attribute(
        self,
        *,
        actor: User,
        command: CreateAttributeDefinitionCommand,
    ) -> AttributeDefinition:
        self._ensure_admin(actor)
        async with self._session.begin():
            category = await self._categories.get_by_id(command.category_id)
            if category is None:
                raise NotFoundError("Category was not found.")
            self._validate_attribute_reference_type(command)
            return await self._attributes.create(
                AttributeDefinition(
                    category_id=command.category_id,
                    code=command.code,
                    name=command.name,
                    value_type=command.value_type,
                    reference_type=command.reference_type,
                    is_required=command.is_required,
                    is_filterable=command.is_filterable,
                    is_searchable=command.is_searchable,
                    is_variant_attribute=command.is_variant_attribute,
                    sort_order=command.sort_order,
                    validation_rules=command.validation_rules,
                ),
            )

    async def list_references(
        self,
        *,
        reference_type: ReferenceType | None = None,
    ) -> list[ReferenceEntity]:
        return await self._references.list_all(reference_type=reference_type)

    async def create_reference(
        self,
        *,
        actor: User,
        command: CreateReferenceEntityCommand,
    ) -> ReferenceEntity:
        self._ensure_admin(actor)
        async with self._session.begin():
            return await self._references.create(
                ReferenceEntity(
                    type=command.type,
                    canonical_name=command.canonical_name,
                    normalized_name=command.normalized_name,
                ),
            )

    def _ensure_admin(self, user: User) -> None:
        if not user.is_active or user.role != UserRole.ADMIN:
            raise ForbiddenError("Admin permissions are required.")

    def _validate_attribute_reference_type(
        self,
        command: CreateAttributeDefinitionCommand,
    ) -> None:
        if command.value_type == AttributeValueType.REFERENCE and command.reference_type is None:
            raise BadRequestError("reference_type is required for reference attributes.")
        if (
            command.value_type != AttributeValueType.REFERENCE
            and command.reference_type is not None
        ):
            raise BadRequestError("reference_type is allowed only for reference attributes.")

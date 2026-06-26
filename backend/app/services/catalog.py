from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.attribute import CatalogItemAttribute, CatalogVariantAttribute
from app.models.category import AttributeDefinition, AttributeValueType
from app.models.item import CatalogItem, CatalogStatus
from app.models.reference import ReferenceEntity
from app.models.user import User, UserRole
from app.models.variant import CatalogVariant
from app.repositories.catalog import CatalogItemRepository, CatalogVariantRepository

CATALOG_EDITOR_ROLES = {
    UserRole.SENIOR_MODERATOR,
    UserRole.ADMIN,
}


@dataclass(slots=True)
class CatalogAttributeValueCommand:
    attribute_definition_id: UUID
    value_text: str | None = None
    value_integer: int | None = None
    value_decimal: Decimal | None = None
    value_boolean: bool | None = None
    value_date: date | None = None
    reference_entity_id: UUID | None = None


@dataclass(slots=True)
class CreateCatalogItemCommand:
    category_id: UUID
    canonical_title: str
    normalized_title: str
    description: str | None = None
    release_year: int | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE
    attributes: list[CatalogAttributeValueCommand] | None = None


@dataclass(slots=True)
class CreateCatalogVariantCommand:
    catalog_item_id: UUID
    canonical_title: str
    normalized_title: str
    sku: str | None = None
    barcode: str | None = None
    release_date: date | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE
    attributes: list[CatalogAttributeValueCommand] | None = None


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
            item = await self._items.create(
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
            await self._replace_item_attributes(
                item=item,
                values=command.attributes or [],
            )
            return item

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

            variant = await self._variants.create(
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
            await self._replace_variant_attributes(
                variant=variant,
                category_id=item.category_id,
                values=command.attributes or [],
            )
            return variant

    async def _replace_item_attributes(
        self,
        *,
        item: CatalogItem,
        values: list[CatalogAttributeValueCommand],
    ) -> None:
        definitions = await self._definitions_by_id(category_id=item.category_id)
        self._validate_required_attributes(
            definitions=definitions,
            values=values,
            variant_attributes=False,
        )
        for value in values:
            definition = definitions.get(value.attribute_definition_id)
            if definition is None or definition.is_variant_attribute:
                raise BadRequestError("Attribute does not belong to this item category.")
            if not _has_value(value):
                continue
            await self._validate_attribute_value(definition=definition, value=value)
            self._session.add(
                CatalogItemAttribute(
                    catalog_item_id=item.id,
                    attribute_definition_id=definition.id,
                    value_text=value.value_text,
                    value_integer=value.value_integer,
                    value_decimal=value.value_decimal,
                    value_boolean=value.value_boolean,
                    value_date=value.value_date,
                    reference_entity_id=value.reference_entity_id,
                )
            )

    async def _replace_variant_attributes(
        self,
        *,
        variant: CatalogVariant,
        category_id: UUID,
        values: list[CatalogAttributeValueCommand],
    ) -> None:
        definitions = await self._definitions_by_id(category_id=category_id)
        self._validate_required_attributes(
            definitions=definitions,
            values=values,
            variant_attributes=True,
        )
        for value in values:
            definition = definitions.get(value.attribute_definition_id)
            if definition is None or not definition.is_variant_attribute:
                raise BadRequestError("Attribute does not belong to this variant category.")
            if not _has_value(value):
                continue
            await self._validate_attribute_value(definition=definition, value=value)
            self._session.add(
                CatalogVariantAttribute(
                    catalog_variant_id=variant.id,
                    attribute_definition_id=definition.id,
                    value_text=value.value_text,
                    value_integer=value.value_integer,
                    value_decimal=value.value_decimal,
                    value_boolean=value.value_boolean,
                    value_date=value.value_date,
                    reference_entity_id=value.reference_entity_id,
                )
            )

    async def _definitions_by_id(self, *, category_id: UUID) -> dict[UUID, AttributeDefinition]:
        result = await self._session.execute(
            select(AttributeDefinition).where(AttributeDefinition.category_id == category_id)
        )
        return {definition.id: definition for definition in result.scalars().all()}

    def _validate_required_attributes(
        self,
        *,
        definitions: dict[UUID, AttributeDefinition],
        values: list[CatalogAttributeValueCommand],
        variant_attributes: bool,
    ) -> None:
        values_by_definition_id = {value.attribute_definition_id: value for value in values}
        for definition in definitions.values():
            if definition.is_variant_attribute != variant_attributes or not definition.is_required:
                continue
            value = values_by_definition_id.get(definition.id)
            if value is None or not _has_expected_value(
                value=value,
                value_type=definition.value_type,
            ):
                raise BadRequestError(f"Attribute '{definition.name}' is required.")

    async def _validate_attribute_value(
        self,
        *,
        definition: AttributeDefinition,
        value: CatalogAttributeValueCommand,
    ) -> None:
        if definition.value_type == AttributeValueType.REFERENCE:
            if definition.reference_type is None:
                raise BadRequestError(
                    f"Attribute '{definition.name}' has no configured reference type."
                )
            if _has_non_reference_value(value):
                raise BadRequestError(f"Attribute '{definition.name}' expects a reference value.")
            if value.reference_entity_id is None:
                raise BadRequestError(f"Attribute '{definition.name}' expects a reference value.")
            reference = await self._session.get(ReferenceEntity, value.reference_entity_id)
            if reference is None:
                raise BadRequestError(f"Reference for attribute '{definition.name}' was not found.")
            if reference.type != definition.reference_type:
                raise BadRequestError(
                    f"Attribute '{definition.name}' expects reference type "
                    f"'{definition.reference_type.value}'."
                )
            return

        if value.reference_entity_id is not None:
            raise BadRequestError(
                f"Attribute '{definition.name}' does not accept reference values."
            )
        if not _has_expected_value(value=value, value_type=definition.value_type):
            raise BadRequestError(f"Attribute '{definition.name}' has invalid value type.")
        if _has_unexpected_scalar_value(value=value, value_type=definition.value_type):
            raise BadRequestError(f"Attribute '{definition.name}' has mixed value types.")

    def _ensure_catalog_editor(self, user: User) -> None:
        if not user.is_active or user.role not in CATALOG_EDITOR_ROLES:
            raise ForbiddenError("Senior moderator permissions are required.")


def _has_value(value: CatalogAttributeValueCommand) -> bool:
    return any(
        item is not None and item != ""
        for item in (
            value.value_text,
            value.value_integer,
            value.value_decimal,
            value.value_boolean,
            value.value_date,
            value.reference_entity_id,
        )
    )


def _has_expected_value(
    *,
    value: CatalogAttributeValueCommand,
    value_type: AttributeValueType,
) -> bool:
    if value_type == AttributeValueType.TEXT:
        return value.value_text not in (None, "")
    if value_type == AttributeValueType.INTEGER:
        return value.value_integer is not None
    if value_type == AttributeValueType.DECIMAL:
        return value.value_decimal is not None
    if value_type == AttributeValueType.BOOLEAN:
        return value.value_boolean is not None
    if value_type == AttributeValueType.DATE:
        return value.value_date is not None
    if value_type == AttributeValueType.REFERENCE:
        return value.reference_entity_id is not None
    return False


def _has_non_reference_value(value: CatalogAttributeValueCommand) -> bool:
    return any(
        item is not None and item != ""
        for item in (
            value.value_text,
            value.value_integer,
            value.value_decimal,
            value.value_boolean,
            value.value_date,
        )
    )


def _has_unexpected_scalar_value(
    *,
    value: CatalogAttributeValueCommand,
    value_type: AttributeValueType,
) -> bool:
    fields = {
        AttributeValueType.TEXT: value.value_text,
        AttributeValueType.INTEGER: value.value_integer,
        AttributeValueType.DECIMAL: value.value_decimal,
        AttributeValueType.BOOLEAN: value.value_boolean,
        AttributeValueType.DATE: value.value_date,
    }
    return any(
        item is not None and item != ""
        for expected_type, item in fields.items()
        if expected_type != value_type
    )

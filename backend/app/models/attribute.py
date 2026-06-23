from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.category import AttributeDefinition
    from app.models.item import CatalogItem
    from app.models.reference import ReferenceEntity
    from app.models.variant import CatalogVariant


class CatalogItemAttribute(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "catalog_item_attributes"
    __table_args__ = (
        UniqueConstraint(
            "catalog_item_id",
            "attribute_definition_id",
            name="uq_catalog_item_attribute",
        ),
    )

    catalog_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        index=True,
    )

    attribute_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("attribute_definitions.id"),
        index=True,
    )

    value_text: Mapped[str | None] = mapped_column(String(1000))
    value_integer: Mapped[int | None] = mapped_column(Integer)
    value_decimal: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_date: Mapped[date | None] = mapped_column(Date)

    reference_entity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reference_entities.id"),
        index=True,
    )

    catalog_item: Mapped[CatalogItem] = relationship(
        back_populates="attributes",
    )

    definition: Mapped[AttributeDefinition] = relationship()
    reference_entity: Mapped[ReferenceEntity | None] = relationship()


class CatalogVariantAttribute(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "catalog_variant_attributes"
    __table_args__ = (
        UniqueConstraint(
            "catalog_variant_id",
            "attribute_definition_id",
            name="uq_catalog_variant_attribute",
        ),
    )

    catalog_variant_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_variants.id", ondelete="CASCADE"),
        index=True,
    )

    attribute_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("attribute_definitions.id"),
        index=True,
    )

    value_text: Mapped[str | None] = mapped_column(String(1000))
    value_integer: Mapped[int | None] = mapped_column(Integer)
    value_decimal: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_date: Mapped[date | None] = mapped_column(Date)

    reference_entity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reference_entities.id"),
        index=True,
    )

    variant: Mapped[CatalogVariant] = relationship(
        back_populates="attributes",
    )

    definition: Mapped[AttributeDefinition] = relationship()
    reference_entity: Mapped[ReferenceEntity | None] = relationship()

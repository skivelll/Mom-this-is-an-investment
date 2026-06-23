from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_values
from app.models.variant import CatalogVariant


class CollectionVisibility(StrEnum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"


class Collection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collections"
    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "name",
            name="uq_collection_owner_name",
        ),
    )

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    visibility: Mapped[CollectionVisibility] = mapped_column(
        Enum(
            CollectionVisibility,
            name="collection_visibility",
            values_callable=enum_values,
        ),
        default=CollectionVisibility.PRIVATE,
        server_default=CollectionVisibility.PRIVATE.value,
    )

    items: Mapped[list[CollectionItem]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
    )


class ItemCondition(StrEnum):
    SEALED = "sealed"
    NEW = "new"
    OPENED = "opened"
    USED = "used"
    DAMAGED = "damaged"


class CollectionItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "collection_items"

    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True,
    )

    catalog_variant_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_variants.id"),
        index=True,
    )

    condition: Mapped[ItemCondition | None] = mapped_column(
        Enum(ItemCondition, name="item_condition", values_callable=enum_values),
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )

    purchase_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
    )

    purchase_currency: Mapped[str | None] = mapped_column(
        String(3),
    )

    purchase_date: Mapped[date | None] = mapped_column(Date)
    comment: Mapped[str | None] = mapped_column(Text)

    collection: Mapped[Collection] = relationship(
        back_populates="items",
    )

    catalog_variant: Mapped[CatalogVariant] = relationship()

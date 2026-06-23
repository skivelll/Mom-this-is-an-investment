# app/modules/catalog/models/item.py

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, enum_values

if TYPE_CHECKING:
    from app.models.alias import CatalogAlias
    from app.models.attribute import CatalogItemAttribute
    from app.models.category import Category
    from app.models.variant import CatalogVariant


class CatalogStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CatalogItem(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "catalog_items"

    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id"),
        index=True,
    )

    canonical_title: Mapped[str] = mapped_column(
        String(500),
        index=True,
    )

    normalized_title: Mapped[str] = mapped_column(
        String(500),
        index=True,
    )

    description: Mapped[str | None] = mapped_column(Text)
    release_year: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[CatalogStatus] = mapped_column(
        Enum(CatalogStatus, name="catalog_status", values_callable=enum_values),
        default=CatalogStatus.ACTIVE,
        server_default=CatalogStatus.ACTIVE.value,
    )

    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
    )

    updated_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
    )

    category: Mapped[Category] = relationship()

    variants: Mapped[list[CatalogVariant]] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
    )

    attributes: Mapped[list[CatalogItemAttribute]] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
    )

    aliases: Mapped[list[CatalogAlias]] = relationship(
        back_populates="catalog_item",
        cascade="all, delete-orphan",
    )

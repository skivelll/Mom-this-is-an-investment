# app/modules/catalog/models/alias.py

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.item import CatalogItem
    from app.models.variant import CatalogVariant


class CatalogAlias(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "catalog_aliases"
    __table_args__ = (
        CheckConstraint(
            """
            (
                catalog_item_id IS NOT NULL
                AND catalog_variant_id IS NULL
            )
            OR
            (
                catalog_item_id IS NULL
                AND catalog_variant_id IS NOT NULL
            )
            """,
            name="ck_catalog_alias_single_owner",
        ),
    )

    catalog_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        index=True,
    )

    catalog_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_variants.id", ondelete="CASCADE"),
        index=True,
    )

    alias: Mapped[str] = mapped_column(String(500))
    normalized_alias: Mapped[str] = mapped_column(
        String(500),
        index=True,
    )

    language: Mapped[str | None] = mapped_column(String(10))

    catalog_item: Mapped[CatalogItem | None] = relationship(
        back_populates="aliases",
    )

    catalog_variant: Mapped[CatalogVariant | None] = relationship(
        back_populates="aliases",
    )

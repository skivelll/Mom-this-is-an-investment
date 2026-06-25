from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, enum_values

if TYPE_CHECKING:
    from app.models.item import CatalogItem
    from app.models.variant import CatalogVariant


class CatalogMediaType(StrEnum):
    IMAGE = "image"


class CatalogMedia(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "catalog_media"

    catalog_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_variants.id", ondelete="CASCADE"),
        index=True,
    )
    object_key: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    media_type: Mapped[CatalogMediaType] = mapped_column(
        Enum(CatalogMediaType, name="catalog_media_type", values_callable=enum_values),
        default=CatalogMediaType.IMAGE,
        server_default=CatalogMediaType.IMAGE.value,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    alt_text: Mapped[str | None] = mapped_column(Text)

    catalog_item: Mapped[CatalogItem] = relationship()
    catalog_variant: Mapped[CatalogVariant | None] = relationship()

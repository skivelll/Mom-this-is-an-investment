from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, enum_values
from app.models.item import CatalogStatus

if TYPE_CHECKING:
    from app.models.alias import CatalogAlias
    from app.models.attribute import CatalogVariantAttribute
    from app.models.item import CatalogItem


class CatalogVariant(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "catalog_variants"
    __table_args__ = (
        Index(
            "uq_catalog_variants_sku_not_null",
            "sku",
            unique=True,
            postgresql_where=text("sku IS NOT NULL"),
        ),
        Index(
            "uq_catalog_variants_barcode_not_null",
            "barcode",
            unique=True,
            postgresql_where=text("barcode IS NOT NULL"),
        ),
    )

    catalog_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
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

    sku: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
    )

    release_date: Mapped[date | None] = mapped_column(Date)

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

    catalog_item: Mapped[CatalogItem] = relationship(
        back_populates="variants",
    )

    attributes: Mapped[list[CatalogVariantAttribute]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
    )

    aliases: Mapped[list[CatalogAlias]] = relationship(
        back_populates="catalog_variant",
        cascade="all, delete-orphan",
    )

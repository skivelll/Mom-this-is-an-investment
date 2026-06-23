from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class CatalogRequestStatus(StrEnum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    NEEDS_INFORMATION = "needs_information"
    APPROVED = "approved"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    CANCELLED = "cancelled"


class CatalogRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "catalog_requests"

    created_by_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id"),
        index=True,
    )

    raw_title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2000))

    proposed_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    status: Mapped[CatalogRequestStatus] = mapped_column(
        Enum(
            CatalogRequestStatus,
            name="catalog_request_status",
            values_callable=enum_values,
        ),
        default=CatalogRequestStatus.PENDING,
        server_default=CatalogRequestStatus.PENDING.value,
        index=True,
    )

    assigned_to_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
    )

    moderated_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
    )

    rejection_reason: Mapped[str | None] = mapped_column(Text)

    approved_catalog_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_items.id"),
    )

    approved_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_variants.id"),
    )

import enum
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class WishlistStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING_MODERATION = "pending_moderation"
    REJECTED = "rejected"
    PURCHASED = "purchased"
    ARCHIVED = "archived"


class WishlistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        CheckConstraint(
            """
            (
                catalog_variant_id IS NOT NULL
                AND catalog_request_id IS NULL
            )
            OR
            (
                catalog_variant_id IS NULL
                AND catalog_request_id IS NOT NULL
            )
            """,
            name="ck_wishlist_catalog_or_request",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    catalog_variant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_variants.id"),
        index=True,
    )

    catalog_request_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog_requests.id"),
        index=True,
    )

    target_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
    )

    currency: Mapped[str | None] = mapped_column(String(3))
    source_url: Mapped[str | None] = mapped_column(String(2000))

    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )

    status: Mapped[WishlistStatus] = mapped_column(
        Enum(WishlistStatus, name="wishlist_status", values_callable=enum_values),
        default=WishlistStatus.ACTIVE,
        server_default=WishlistStatus.ACTIVE.value,
    )

    comment: Mapped[str | None] = mapped_column(Text)

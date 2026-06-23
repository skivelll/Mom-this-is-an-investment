import enum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class AttributeValueType(str, enum.Enum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    REFERENCE = "reference"


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )

    attribute_definitions: Mapped[list[AttributeDefinition]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )


class AttributeDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attribute_definitions"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "code",
            name="uq_attribute_definition_category_code",
        ),
    )

    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
    )

    code: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))

    value_type: Mapped[AttributeValueType] = mapped_column(
        Enum(
            AttributeValueType,
            name="attribute_value_type",
            values_callable=enum_values,
        ),
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )

    is_filterable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )

    is_searchable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )

    is_variant_attribute: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
    )

    validation_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    category: Mapped[Category] = relationship(
        back_populates="attribute_definitions",
    )

from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_values


class ReferenceType(StrEnum):
    MANUFACTURER = "manufacturer"
    PUBLISHER = "publisher"
    FRANCHISE = "franchise"
    CHARACTER = "character"
    AUTHOR = "author"
    SERIES = "series"


class ReferenceEntity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reference_entities"
    __table_args__ = (
        UniqueConstraint(
            "type",
            "normalized_name",
            name="uq_reference_type_normalized_name",
        ),
    )

    type: Mapped[ReferenceType] = mapped_column(
        Enum(ReferenceType, name="reference_type", values_callable=enum_values),
        index=True,
    )

    canonical_name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)

    aliases: Mapped[list[ReferenceAlias]] = relationship(
        back_populates="reference",
        cascade="all, delete-orphan",
    )


class ReferenceAlias(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reference_aliases"
    __table_args__ = (
        UniqueConstraint(
            "reference_id",
            "normalized_alias",
            name="uq_reference_alias",
        ),
    )

    reference_id: Mapped[UUID] = mapped_column(
        ForeignKey("reference_entities.id", ondelete="CASCADE"),
    )

    alias: Mapped[str] = mapped_column(String(255))
    normalized_alias: Mapped[str] = mapped_column(String(255), index=True)
    language: Mapped[str | None] = mapped_column(String(10))

    reference: Mapped[ReferenceEntity] = relationship(
        back_populates="aliases",
    )

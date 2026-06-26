"""add media processing fields

Revision ID: 9d3b0e6a5c42
Revises: 2b1e4a9c8d31
Create Date: 2026-06-26 00:10:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9d3b0e6a5c42"
down_revision: str | Sequence[str] | None = "2b1e4a9c8d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


processing_status_enum = sa.Enum(
    "pending",
    "processing",
    "ready",
    "failed",
    name="catalog_media_processing_status",
)


def upgrade() -> None:
    processing_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "catalog_media",
        sa.Column("thumbnail_object_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "catalog_media",
        sa.Column("card_object_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "catalog_media",
        sa.Column("full_object_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "catalog_media",
        sa.Column(
            "processing_status",
            processing_status_enum,
            server_default="ready",
            nullable=False,
        ),
    )
    op.add_column("catalog_media", sa.Column("processing_error", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_catalog_media_thumbnail_object_key"),
        "catalog_media",
        ["thumbnail_object_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_catalog_media_card_object_key"),
        "catalog_media",
        ["card_object_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_catalog_media_full_object_key"),
        "catalog_media",
        ["full_object_key"],
        unique=True,
    )
    op.alter_column("catalog_media", "processing_status", server_default="pending")


def downgrade() -> None:
    op.drop_index(op.f("ix_catalog_media_full_object_key"), table_name="catalog_media")
    op.drop_index(op.f("ix_catalog_media_card_object_key"), table_name="catalog_media")
    op.drop_index(op.f("ix_catalog_media_thumbnail_object_key"), table_name="catalog_media")
    op.drop_column("catalog_media", "processing_error")
    op.drop_column("catalog_media", "processing_status")
    op.drop_column("catalog_media", "full_object_key")
    op.drop_column("catalog_media", "card_object_key")
    op.drop_column("catalog_media", "thumbnail_object_key")
    processing_status_enum.drop(op.get_bind(), checkfirst=True)

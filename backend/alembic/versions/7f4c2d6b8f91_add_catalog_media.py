"""add catalog media

Revision ID: 7f4c2d6b8f91
Revises: c279e5cec234
Create Date: 2026-06-25 20:40:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7f4c2d6b8f91"
down_revision: str | Sequence[str] | None = "c279e5cec234"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "catalog_media",
        sa.Column("catalog_item_id", sa.Uuid(), nullable=False),
        sa.Column("catalog_variant_id", sa.Uuid(), nullable=True),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column(
            "media_type",
            sa.Enum("image", name="catalog_media_type"),
            server_default="image",
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["catalog_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["catalog_variant_id"], ["catalog_variants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_catalog_media_catalog_item_id"), "catalog_media", ["catalog_item_id"])
    op.create_index(
        op.f("ix_catalog_media_catalog_variant_id"), "catalog_media", ["catalog_variant_id"]
    )
    op.create_index(
        op.f("ix_catalog_media_object_key"), "catalog_media", ["object_key"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_catalog_media_object_key"), table_name="catalog_media")
    op.drop_index(op.f("ix_catalog_media_catalog_variant_id"), table_name="catalog_media")
    op.drop_index(op.f("ix_catalog_media_catalog_item_id"), table_name="catalog_media")
    op.drop_table("catalog_media")
    op.execute("DROP TYPE IF EXISTS catalog_media_type")

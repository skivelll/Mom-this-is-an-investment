"""add attribute reference type

Revision ID: 2b1e4a9c8d31
Revises: 7f4c2d6b8f91
Create Date: 2026-06-26 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "2b1e4a9c8d31"
down_revision: str | Sequence[str] | None = "7f4c2d6b8f91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


reference_type_enum = postgresql.ENUM(
    "manufacturer",
    "publisher",
    "franchise",
    "character",
    "author",
    "series",
    name="reference_type",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "attribute_definitions",
        sa.Column("reference_type", reference_type_enum, nullable=True),
    )
    op.execute(
        """
        UPDATE attribute_definitions
        SET reference_type = CASE code
            WHEN 'manufacturer' THEN 'manufacturer'::reference_type
            WHEN 'publisher' THEN 'publisher'::reference_type
            WHEN 'franchise' THEN 'franchise'::reference_type
            WHEN 'character' THEN 'character'::reference_type
            WHEN 'author' THEN 'author'::reference_type
            WHEN 'writer' THEN 'author'::reference_type
            WHEN 'artist' THEN 'author'::reference_type
            WHEN 'series' THEN 'series'::reference_type
            ELSE NULL
        END
        WHERE value_type = 'reference'
        """
    )


def downgrade() -> None:
    op.drop_column("attribute_definitions", "reference_type")

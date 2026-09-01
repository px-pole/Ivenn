"""add in-app notifications

Revision ID: 8a91c52e740d
Revises: 37383c9bc227
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8a91c52e740d"
down_revision: Union[str, None] = "37383c9bc227"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("warranty_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("dedup_key", sa.String(length=200), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "dedup_key", name="uq_notifications_user_dedup_key"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)
    op.create_index(op.f("ix_notifications_warranty_id"), "notifications", ["warranty_id"], unique=False)
    op.create_index(op.f("ix_notifications_item_id"), "notifications", ["item_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_item_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_warranty_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")

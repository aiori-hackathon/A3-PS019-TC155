"""Add the workspace display name expected by the current user model.

Revision ID: b52e91c4f8ad
Revises: a7b40d5c911e
Create Date: 2026-10-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b52e91c4f8ad"
down_revision: Union[str, None] = "a7b40d5c911e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(length=160), nullable=True, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("users", "full_name")

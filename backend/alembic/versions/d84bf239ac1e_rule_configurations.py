"""Add per-workspace enabled class rules.

Revision ID: d84bf239ac1e
Revises: 83b0fade254b
Create Date: 2026-10-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d84bf239ac1e"
down_revision: Union[str, None] = "83b0fade254b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rule_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("enabled_classes", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index(op.f("ix_rule_configurations_organization_id"), "rule_configurations", ["organization_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_rule_configurations_organization_id"), table_name="rule_configurations")
    op.drop_table("rule_configurations")

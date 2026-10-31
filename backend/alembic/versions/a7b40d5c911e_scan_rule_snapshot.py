"""Record enabled rule classes on each scan.

Revision ID: a7b40d5c911e
Revises: d84bf239ac1e
Create Date: 2026-10-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a7b40d5c911e"
down_revision: Union[str, None] = "d84bf239ac1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "scans",
        sa.Column(
            "enabled_classes",
            sa.JSON(),
            nullable=False,
            server_default='["C1","C2","C3","C4","C5"]',
        ),
    )


def downgrade() -> None:
    op.drop_column("scans", "enabled_classes")

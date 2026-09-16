"""persist recommendation plans

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("history_signature", sa.String(length=64), nullable=False),
        sa.Column("plan_title", sa.String(length=128), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_recommendation_plans_user_id",
        "recommendation_plans",
        ["user_id"],
    )
    op.create_index(
        "ix_recommendation_plans_history_signature",
        "recommendation_plans",
        ["history_signature"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_plans_history_signature",
        table_name="recommendation_plans",
    )
    op.drop_index(
        "ix_recommendation_plans_user_id",
        table_name="recommendation_plans",
    )
    op.drop_table("recommendation_plans")

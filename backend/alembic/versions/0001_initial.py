"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-09-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nickname", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("text", sa.String(length=256), nullable=False),
        sa.Column("ipa", sa.String(length=128), nullable=False),
        sa.Column("audio_url", sa.String(length=512), nullable=True),
        sa.Column("target_phonemes", sa.JSON(), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("tip", sa.Text(), nullable=False),
    )
    op.create_table(
        "practice_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("fluency", sa.Float(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("error_phonemes", sa.JSON(), nullable=False),
        sa.Column("audio_path", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("practice_records")
    op.drop_table("lessons")
    op.drop_table("users")

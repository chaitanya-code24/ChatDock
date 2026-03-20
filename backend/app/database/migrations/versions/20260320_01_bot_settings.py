"""Add bot settings fields

Revision ID: 20260320_01
Revises: 20260313_01
Create Date: 2026-03-20 18:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260320_01"
down_revision: Union[str, Sequence[str], None] = "20260313_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("bots", sa.Column("tone", sa.String(length=20), nullable=False, server_default="professional"))
    op.add_column("bots", sa.Column("answer_length", sa.String(length=20), nullable=False, server_default="balanced"))
    op.add_column("bots", sa.Column("fallback_behavior", sa.String(length=20), nullable=False, server_default="strict"))
    op.add_column("bots", sa.Column("system_prompt", sa.Text(), nullable=True))
    op.add_column("bots", sa.Column("greeting_message", sa.Text(), nullable=True))
    op.add_column("bots", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "updated_at")
    op.drop_column("bots", "greeting_message")
    op.drop_column("bots", "system_prompt")
    op.drop_column("bots", "fallback_behavior")
    op.drop_column("bots", "answer_length")
    op.drop_column("bots", "tone")
    op.drop_column("bots", "archived")

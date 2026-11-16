"""Add task tracking fields to ai_responses.

Revision ID: 20261116_01
Revises:
Create Date: 2026-11-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261116_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable columns first so the migration also works when old rows
    # already exist. Existing rows receive deterministic legacy values below.
    op.add_column("ai_responses", sa.Column("user_id", sa.UUID(), nullable=True))
    op.add_column("ai_responses", sa.Column("task_id", sa.String(length=255), nullable=True))
    op.add_column("ai_responses", sa.Column("file_key", sa.String(length=512), nullable=True))
    op.add_column(
        "ai_responses",
        sa.Column("status", sa.String(length=32), nullable=True),
    )
    op.add_column("ai_responses", sa.Column("response", sa.Text(), nullable=True))
    op.add_column("ai_responses", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("ai_responses", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ai_responses", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        sa.text(
            "UPDATE ai_responses "
            "SET task_id = 'legacy-' || id::text, "
            "user_id = '00000000-0000-0000-0000-000000000000'::uuid, "
            "file_key = 'legacy/' || id::text, "
            "status = 'COMPLETED' "
            "WHERE task_id IS NULL"
        )
    )

    op.alter_column("ai_responses", "user_id", nullable=False)
    op.alter_column("ai_responses", "task_id", nullable=False)
    op.alter_column("ai_responses", "file_key", nullable=False)
    op.alter_column("ai_responses", "status", nullable=False)
    op.create_index("ix_ai_responses_user_id", "ai_responses", ["user_id"])
    op.create_index("ix_ai_responses_task_id", "ai_responses", ["task_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_ai_responses_task_id", table_name="ai_responses")
    op.drop_index("ix_ai_responses_user_id", table_name="ai_responses")
    for column in (
        "finished_at",
        "started_at",
        "error",
        "response",
        "status",
        "file_key",
        "task_id",
        "user_id",
    ):
        op.drop_column("ai_responses", column)

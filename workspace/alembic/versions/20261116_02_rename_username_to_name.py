"""Rename users.username to users.name.

The SQLAlchemy model uses ``name``, while the existing database schema was
created with ``username``.  Keep the migration safe for databases where the
column has already been corrected manually.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261116_02"
down_revision: Union[str, Sequence[str], None] = "20261116_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns("users")}


def upgrade() -> None:
    columns = _columns()
    if "username" in columns and "name" not in columns:
        op.alter_column("users", "username", new_column_name="name")


def downgrade() -> None:
    columns = _columns()
    if "name" in columns and "username" not in columns:
        op.alter_column("users", "name", new_column_name="username")

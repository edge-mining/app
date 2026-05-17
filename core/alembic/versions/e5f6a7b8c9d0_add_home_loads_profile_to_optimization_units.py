"""Add home_loads_profile to optimization_units

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-29 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("optimization_units") as batch_op:
        batch_op.add_column(sa.Column("home_loads_profile", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("optimization_units") as batch_op:
        batch_op.drop_column("home_loads_profile")

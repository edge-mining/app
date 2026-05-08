"""Add tuning and backtesting columns to load_consumption_models

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-25 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("load_consumption_models") as batch_op:
        batch_op.add_column(sa.Column("tuning_params", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("backtest_mae", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("backtest_rmse", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("backtest_folds", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("load_consumption_models") as batch_op:
        batch_op.drop_column("backtest_folds")
        batch_op.drop_column("backtest_rmse")
        batch_op.drop_column("backtest_mae")
        batch_op.drop_column("tuning_params")

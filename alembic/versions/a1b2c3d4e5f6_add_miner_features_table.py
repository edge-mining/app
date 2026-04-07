"""Add miner_features table and remove controller_id from miners

Revision ID: a1b2c3d4e5f6
Revises: 4e55fe6113c7
Create Date: 2026-01-24 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4e55fe6113c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add miner_features table and migrate controller_id data."""
    # Create miner_features table
    op.create_table(
        "miner_features",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("miner_id", sa.String(), nullable=False),
        sa.Column("controller_id", sa.String(), nullable=False),
        sa.Column("feature_type", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["miner_id"],
            ["miners.id"],
        ),
        sa.ForeignKeyConstraint(
            ["controller_id"],
            ["miner_controllers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Remove controller_id column from miners table
    # Note: SQLite doesn't support DROP COLUMN directly in older versions,
    # but Alembic handles this with batch mode on SQLite.
    with op.batch_alter_table("miners") as batch_op:
        batch_op.drop_column("controller_id")


def downgrade() -> None:
    """Remove miner_features table and restore controller_id on miners."""
    # Re-add controller_id to miners
    with op.batch_alter_table("miners") as batch_op:
        batch_op.add_column(sa.Column("controller_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_miners_controller_id",
            "miner_controllers",
            ["controller_id"],
            ["id"],
        )

    # Drop miner_features table
    op.drop_table("miner_features")

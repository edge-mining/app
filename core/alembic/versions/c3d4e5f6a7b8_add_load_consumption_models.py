"""Add load_consumption_models table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-22 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "load_consumption_models",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=True),
        sa.Column("adapter_type", sa.String(), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mae", sa.Float(), nullable=True),
        sa.Column("rmse", sa.Float(), nullable=True),
        sa.Column("samples_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("model_bytes", sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_load_consumption_models_id", "load_consumption_models", ["id"])
    op.create_index(
        "ix_load_consumption_models_active",
        "load_consumption_models",
        ["adapter_type", "device_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_load_consumption_models_active", table_name="load_consumption_models")
    op.drop_index("ix_load_consumption_models_id", table_name="load_consumption_models")
    op.drop_table("load_consumption_models")

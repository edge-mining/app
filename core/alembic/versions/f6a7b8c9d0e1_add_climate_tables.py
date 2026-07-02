"""Add climate tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-22 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "climate_zones",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("area_sqm", sa.Float(), nullable=False),
        sa.Column("climate_monitor_id", sa.String(), nullable=True),
    )

    op.create_table(
        "climate_monitors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("adapter_type", sa.String(), nullable=False),
        sa.Column("config", sa.String(), nullable=True),
        sa.Column("external_service_id", sa.String(), nullable=True),
    )

    with op.batch_alter_table("optimization_units") as batch_op:
        batch_op.add_column(sa.Column("climate_zone_ids", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("optimization_units") as batch_op:
        batch_op.drop_column("climate_zone_ids")

    op.drop_table("climate_monitors")
    op.drop_table("climate_zones")

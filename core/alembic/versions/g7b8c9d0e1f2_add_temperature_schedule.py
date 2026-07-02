"""Add temperature schedule to climate zones

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-22 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("climate_zones", sa.Column("temperature_schedule", sa.String(), nullable=True))
    op.add_column("climate_zones", sa.Column("hysteresis_celsius", sa.Float(), nullable=False, server_default="0.5"))
    op.add_column("climate_zones", sa.Column("default_target_temperature", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("climate_zones", "default_target_temperature")
    op.drop_column("climate_zones", "hysteresis_celsius")
    op.drop_column("climate_zones", "temperature_schedule")

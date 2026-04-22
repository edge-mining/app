"""Add energy_load_history_providers table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-22 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

import edge_mining.adapters.domain.home_load.tables
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add energy_load_history_providers table."""
    op.create_table(
        "energy_load_history_providers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("adapter_type", sa.String(), nullable=False),
        sa.Column(
            "config",
            edge_mining.adapters.domain.home_load.tables.EnergyLoadHistoryProviderConfigType(),
            nullable=True,
        ),
        sa.Column("external_service_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["external_service_id"],
            ["external_services.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_energy_load_history_providers_id"),
        "energy_load_history_providers",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove energy_load_history_providers table."""
    op.drop_index(
        op.f("ix_energy_load_history_providers_id"),
        table_name="energy_load_history_providers",
    )
    op.drop_table("energy_load_history_providers")

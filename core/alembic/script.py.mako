"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# Import custom types used in Edge Mining table definitions
import edge_mining.adapters.infrastructure.external_services.tables
import edge_mining.adapters.domain.energy.tables
import edge_mining.adapters.domain.forecast.tables
import edge_mining.adapters.domain.home_load.tables
import edge_mining.adapters.domain.miner.tables
import edge_mining.adapters.domain.notification.tables
import edge_mining.adapters.domain.performance.tables
import edge_mining.adapters.domain.policy.tables

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """Upgrade schema."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema."""
    ${downgrades if downgrades else "pass"}

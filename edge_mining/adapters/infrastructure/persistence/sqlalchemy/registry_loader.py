"""Registry loader for SQLAlchemy table definitions.

This module ensures all table definitions are imported and registered
with the shared mapper registry before create_all_tables() is called.

Import this module once before calling create_all_tables() to ensure
all domain tables are properly registered.
"""

# Import all table definitions to register them with the mapper registry
# The imports are used only for their side effects (table registration)
# so we can safely ignore unused import warnings

from edge_mining.adapters.domain.energy import tables as _energy_tables  # noqa: F401
from edge_mining.adapters.domain.forecast import tables as _forecast_tables  # noqa: F401
from edge_mining.adapters.domain.home_load import tables as _home_load_tables  # noqa: F401
from edge_mining.adapters.domain.miner import tables as _miner_tables  # noqa: F401
from edge_mining.adapters.domain.notification import tables as _notification_tables  # noqa: F401
from edge_mining.adapters.domain.optimization_unit import tables as _optimization_unit_tables  # noqa: F401
from edge_mining.adapters.domain.performance import tables as _performance_tables  # noqa: F401
from edge_mining.adapters.domain.policy import tables as _policy_tables  # noqa: F401
from edge_mining.adapters.domain.user import tables as _user_tables  # noqa: F401
from edge_mining.adapters.infrastructure.external_services import tables as _external_services_tables  # noqa: F401


def ensure_tables_registered() -> None:
    """Ensure all table definitions are registered.

    This function exists primarily for explicit documentation purposes.
    The actual registration happens when this module is imported.
    Call this function if you want to be explicit about the registration step.
    """
    pass  # Tables are registered on module import

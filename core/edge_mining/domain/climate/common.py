"""Collection of Common Objects for the Climate domain of the Edge Mining application."""

from edge_mining.domain.common import AdapterType


class ClimateMonitorAdapter(AdapterType):
    """Enum for the different climate monitor adapters."""

    DUMMY = "dummy"
    HOME_ASSISTANT_API = "home_assistant_api"

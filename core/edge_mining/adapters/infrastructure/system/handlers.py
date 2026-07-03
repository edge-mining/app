"""Event handlers that apply system configuration changes to ambient infrastructure."""

from edge_mining.application.interfaces import EventBusInterface, SunFactoryInterface
from edge_mining.domain.user.events import SystemConfigurationUpdated
from edge_mining.shared.logging.port import LoggerPort
from edge_mining.shared.timezone import set_timezone


class SystemConfigurationHandler:
    """Applies runtime system configuration changes to ambient infrastructure.

    Reacts to ``SystemConfigurationUpdated`` events by refreshing the application
    timezone and reconfiguring the Sun factory location, so that changes take
    effect without restarting the application.
    """

    def __init__(self, sun_factory: SunFactoryInterface, logger: LoggerPort) -> None:
        self._sun_factory = sun_factory
        self._logger = logger

    def subscribe(self, event_bus: EventBusInterface) -> None:
        """Register this handler on the event bus."""
        event_bus.subscribe(
            SystemConfigurationUpdated,
            self.on_system_configuration_updated,
            blocking=False,
        )

    async def on_system_configuration_updated(self, event: SystemConfigurationUpdated) -> None:
        """Apply the updated system configuration to the ambient infrastructure."""
        configuration = event.configuration
        if configuration is None:
            return

        self._logger.debug("Applying updated system configuration to ambient infrastructure.")

        set_timezone(configuration.timezone)
        self._sun_factory.reconfigure(
            latitude=configuration.latitude,
            longitude=configuration.longitude,
            timezone=configuration.timezone,
        )

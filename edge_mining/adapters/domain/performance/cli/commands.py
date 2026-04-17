"""CLI commands for the mining performance tracker domain."""

from typing import List, Optional

import click

from edge_mining.adapters.infrastructure.cli.utils import print_configuration
from edge_mining.adapters.utils import run_async_func
from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    ConfigurationServiceInterface,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.exceptions import (
    MiningPoolAuthError,
    MiningPoolResponseError,
    MiningPoolUnreachableError,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
    MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerOceanConfig,
)
from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig
from edge_mining.shared.logging.port import LoggerPort


def select_mining_performance_tracker_adapter() -> Optional[MiningPerformanceTrackerAdapter]:
    """Prompt the user to select a tracker adapter type."""
    click.echo("Select Mining Performance Tracker Adapter:")
    for idx, adapter in enumerate(MiningPerformanceTrackerAdapter):
        click.echo(f"{idx}. {adapter.name}")

    click.echo("")
    choice: str = click.prompt("Choose a Tracker", type=str)
    choice = choice.strip().lower()

    if not choice.isdigit() or int(choice) < 0 or int(choice) >= len(MiningPerformanceTrackerAdapter):
        click.echo(click.style("Invalid index. Aborting selection.", fg="red"))
        return None

    values = [a.value for a in MiningPerformanceTrackerAdapter]
    return MiningPerformanceTrackerAdapter(values[int(choice)])


def handle_tracker_dummy_config() -> MiningPerformanceTrackerConfig:
    """Prompt the dummy tracker message."""
    message: str = click.prompt(
        "Dummy message",
        type=str,
        default="This is a dummy performance tracker",
    )
    return MiningPerformanceTrackerDummyConfig(message=message)


def handle_tracker_ocean_config() -> MiningPerformanceTrackerConfig:
    """Prompt Ocean tracker configuration fields."""
    bitcoin_address: str = click.prompt("Bitcoin payout address", type=str)
    api_base_url: str = click.prompt(
        "Ocean API base URL",
        type=str,
        default="https://api.ocean.xyz",
    )
    request_timeout_seconds: int = click.prompt(
        "Request timeout (seconds)",
        type=int,
        default=10,
    )
    return MiningPerformanceTrackerOceanConfig(
        bitcoin_address=bitcoin_address,
        api_base_url=api_base_url,
        request_timeout_seconds=request_timeout_seconds,
    )


def handle_tracker_braiins_config() -> MiningPerformanceTrackerConfig:
    """Prompt Braiins Pool tracker configuration fields."""
    api_token: str = click.prompt("Braiins Pool API token", type=str, hide_input=True)
    api_base_url: str = click.prompt(
        "Braiins Pool API base URL",
        type=str,
        default="https://pool.braiins.com",
    )
    request_timeout_seconds: int = click.prompt(
        "Request timeout (seconds)",
        type=int,
        default=10,
    )
    return MiningPerformanceTrackerBraiinsPoolConfig(
        api_token=api_token,
        api_base_url=api_base_url,
        request_timeout_seconds=request_timeout_seconds,
    )


_TRACKER_CONFIG_HANDLERS = {
    MiningPerformanceTrackerAdapter.DUMMY: handle_tracker_dummy_config,
    MiningPerformanceTrackerAdapter.OCEAN: handle_tracker_ocean_config,
    MiningPerformanceTrackerAdapter.BRAIINS_POOL: handle_tracker_braiins_config,
}


def handle_tracker_configuration(
    adapter_type: MiningPerformanceTrackerAdapter,
) -> Optional[MiningPerformanceTrackerConfig]:
    """Dispatch to the matching configuration handler."""
    handler = _TRACKER_CONFIG_HANDLERS.get(adapter_type)
    if handler is None:
        click.echo(click.style("Unsupported tracker type selected. Aborting.", fg="red"))
        return None
    return handler()


def print_tracker_config(tracker: MiningPerformanceTracker) -> None:
    """Print the configuration of a tracker."""
    configuration_class = tracker.config.__class__.__name__ if tracker.config else "---"
    click.echo("| Configuration: " + click.style(f"{configuration_class}", fg="cyan"))
    if tracker.config:
        print_configuration(tracker.config.to_dict())


def print_tracker_details(tracker: MiningPerformanceTracker) -> None:
    """Print the details of a tracker."""
    click.echo("")
    click.echo("| Name: " + click.style(tracker.name, fg="blue"))
    click.echo("| ID: " + click.style(str(tracker.id), fg="yellow"))
    click.echo("| Adapter: " + click.style(tracker.adapter_type.name, fg="green"))
    external_service_id = str(tracker.external_service_id) if tracker.external_service_id else "None"
    click.echo("| External service: " + click.style(external_service_id, fg="magenta"))
    print_tracker_config(tracker)
    click.echo("")


def handle_add_mining_performance_tracker(
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> Optional[MiningPerformanceTracker]:
    """Menu flow to add a new mining performance tracker."""
    click.echo(click.style("\n--- Add Mining Performance Tracker ---", fg="yellow"))
    name: str = click.prompt("Name of the tracker", type=str)
    adapter_type: Optional[MiningPerformanceTrackerAdapter] = select_mining_performance_tracker_adapter()
    if adapter_type is None:
        click.echo(click.style("Invalid tracker type selected. Aborting.", fg="red"))
        return None

    config: Optional[MiningPerformanceTrackerConfig] = handle_tracker_configuration(adapter_type)
    if config is None:
        click.echo(click.style("Invalid configuration. Aborting.", fg="red"))
        return None

    added: Optional[MiningPerformanceTracker] = None
    try:
        added = run_async_func(
            configuration_service.add_mining_performance_tracker(
                name=name,
                adapter_type=adapter_type,
                config=config,
                external_service_id=None,
            )
        )
        click.echo(
            click.style(
                f"Mining performance tracker '{added.name}' (ID: {added.id}) successfully added.",
                fg="green",
            )
        )
    except Exception as e:
        logger.error(f"Error adding mining performance tracker: {e}")
        click.echo(click.style(f"Error adding mining performance tracker: {e}", fg="red"), err=True)
        added = None
    click.pause("Press any key to return to the menu...")
    return added


def handle_list_mining_performance_trackers(
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """List all configured trackers."""
    click.echo(click.style("\n--- Configured Mining Performance Trackers ---", fg="yellow"))
    trackers: List[MiningPerformanceTracker] = configuration_service.list_mining_performance_trackers()
    if not trackers:
        click.echo(click.style("No mining performance trackers configured.", fg="yellow"))
    else:
        for t in trackers:
            click.echo(
                "-> "
                + "Name: "
                + click.style(f"{t.name}, ", fg="blue")
                + "ID: "
                + click.style(f"{t.id}, ", fg="yellow")
                + "Type: "
                + click.style(f"{t.adapter_type.name}", fg="green")
            )
    click.echo("")
    click.pause("Press any key to return to the menu...")


def select_mining_performance_tracker(
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
    default_id: Optional[EntityId] = None,
) -> Optional[MiningPerformanceTracker]:
    """Prompt the user to pick one tracker from the configured list."""
    trackers: List[MiningPerformanceTracker] = configuration_service.list_mining_performance_trackers()

    click.echo(click.style("\n--- Select Mining Performance Tracker ---", fg="yellow"))
    if not trackers:
        click.echo(click.style("No mining performance trackers configured.", fg="yellow"))
        return None

    default_idx = ""
    for idx, t in enumerate(trackers):
        click.echo(
            f"{idx}. "
            + "Name: "
            + click.style(f"{t.name}, ", fg="blue")
            + "ID: "
            + click.style(f"{t.id}, ", fg="yellow")
            + "Type: "
            + click.style(f"{t.adapter_type.name}", fg="green")
        )
        if default_id and t.id == default_id:
            default_idx = str(idx)

    click.echo("\nb. Back to menu\n")
    raw: str = click.prompt("Choose a Tracker index", type=str, default=default_idx)
    raw = raw.strip().lower()
    if raw == "b":
        return None

    if not raw.isdigit() or int(raw) < 0 or int(raw) >= len(trackers):
        click.echo(click.style("Invalid index. Aborting selection.", fg="red"))
        return None

    return trackers[int(raw)]


def update_single_mining_performance_tracker(
    tracker: MiningPerformanceTracker,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> Optional[MiningPerformanceTracker]:
    """Update a single tracker."""
    click.echo(click.style("\n--- Update Mining Performance Tracker ---", fg="yellow"))
    new_name: str = click.prompt("New name of the tracker", type=str, default=tracker.name)

    change_config: bool = click.confirm("Change configuration", default=True, prompt_suffix="")
    new_config: Optional[MiningPerformanceTrackerConfig] = tracker.config
    if change_config:
        new_config = handle_tracker_configuration(tracker.adapter_type)
        if new_config is None:
            click.echo(click.style("Invalid configuration. Aborting.", fg="red"))
            return None

    if new_config is None:
        click.echo(click.style("Tracker configuration is required. Aborting.", fg="red"))
        return None

    updated: Optional[MiningPerformanceTracker] = None
    try:
        updated = run_async_func(
            configuration_service.update_mining_performance_tracker(
                tracker_id=tracker.id,
                name=new_name,
                config=new_config,
                external_service_id=tracker.external_service_id,
            )
        )
        click.echo(
            click.style(
                f"Mining performance tracker '{updated.name}' (ID: {updated.id}) successfully updated.",
                fg="green",
            )
        )
    except Exception as e:
        logger.error(f"Error updating mining performance tracker: {e}")
        click.echo(click.style(f"Error updating mining performance tracker: {e}", fg="red"), err=True)
        updated = None
    finally:
        click.pause("Press any key to return to the menu...")
    return updated


def delete_single_mining_performance_tracker(
    tracker: MiningPerformanceTracker,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> bool:
    """Delete a single tracker after confirmation."""
    confirm: bool = click.confirm(
        f"Are you sure you want to delete the tracker '{tracker.name}' (ID: {tracker.id})?",
        default=False,
        prompt_suffix="",
    )
    if not confirm:
        click.echo(click.style("Deletion cancelled.", fg="yellow"))
        return False

    try:
        removed = run_async_func(configuration_service.remove_mining_performance_tracker(tracker_id=tracker.id))
        logger.info(f"Mining performance tracker '{removed.name}' (ID: {removed.id}) successfully removed.")
        click.echo(
            click.style(
                f"Mining performance tracker '{removed.name}' (ID: {removed.id}) successfully removed.",
                fg="green",
            )
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting mining performance tracker: {e}")
        click.echo(click.style(f"Error deleting mining performance tracker: {e}", fg="red"), err=True)
        return False


def check_single_mining_performance_tracker(
    tracker: MiningPerformanceTracker,
    adapter_service: AdapterServiceInterface,
    logger: LoggerPort,
) -> bool:
    """Test reachability of a tracker by calling get_payout_schedule()."""
    click.echo(click.style("\n--- Test Mining Performance Tracker ---", fg="yellow"))
    try:
        port = run_async_func(adapter_service.get_mining_performance_tracker(tracker.id))
        if port is None:
            click.echo(click.style("Tracker adapter not available. Aborting test.", fg="red"))
            return False

        schedule = run_async_func(port.get_payout_schedule())
        if schedule is None:
            click.echo(click.style("Tracker returned no payout schedule.", fg="yellow"))
        else:
            click.echo(
                click.style(
                    f"Tracker reachable. Payout frequency: {schedule.frequency.value}, threshold: {schedule.threshold}",
                    fg="green",
                )
            )
        return True
    except MiningPoolAuthError as e:
        click.echo(click.style(f"Authentication failed: {e}", fg="red"), err=True)
    except MiningPoolUnreachableError as e:
        click.echo(click.style(f"Pool unreachable: {e}", fg="red"), err=True)
    except MiningPoolResponseError as e:
        click.echo(click.style(f"Pool returned invalid response: {e}", fg="red"), err=True)
    except Exception as e:
        logger.error(f"Error testing mining performance tracker: {e}")
        click.echo(click.style(f"Error testing mining performance tracker: {e}", fg="red"), err=True)
    return False


def manage_single_mining_performance_tracker_menu(
    tracker: MiningPerformanceTracker,
    configuration_service: ConfigurationServiceInterface,
    adapter_service: Optional[AdapterServiceInterface],
    logger: LoggerPort,
) -> str:
    """Menu for managing a single mining performance tracker."""
    while True:
        click.echo("\n" + click.style("--- MANAGE MINING PERFORMANCE TRACKER ---", fg="blue", bold=True))
        print_tracker_details(tracker)
        click.echo("1. Update Tracker")
        click.echo("2. Delete Tracker")
        if adapter_service is not None:
            click.echo("3. Test Tracker")
        click.echo("")
        click.echo("b. Back to tracker menu")
        click.echo("q. Close application")
        click.echo("-----------------")

        choice: str = click.prompt("Choose an option", type=str)
        choice = choice.strip().lower()
        click.clear()

        if choice == "1":
            updated_tracker = update_single_mining_performance_tracker(
                tracker=tracker,
                configuration_service=configuration_service,
                logger=logger,
            )
            tracker = updated_tracker or tracker
            continue
        if choice == "2":
            deleted = delete_single_mining_performance_tracker(
                tracker=tracker,
                configuration_service=configuration_service,
                logger=logger,
            )
            if deleted:
                return "b"
        elif choice == "3" and adapter_service is not None:
            check_single_mining_performance_tracker(
                tracker=tracker,
                adapter_service=adapter_service,
                logger=logger,
            )
            click.pause("Press any key to return to the menu...")
        elif choice == "b":
            break
        elif choice == "q":
            break
        else:
            click.echo(click.style("Invalid choice. Try again.", fg="red"))
            click.pause("Press any key to return to the menu...")

    return choice


def handle_manage_mining_performance_tracker(
    configuration_service: ConfigurationServiceInterface,
    adapter_service: Optional[AdapterServiceInterface],
    logger: LoggerPort,
) -> str:
    """Entry point to manage an existing tracker (select → manage menu)."""
    selected = select_mining_performance_tracker(configuration_service, logger)
    if selected is None:
        click.echo(click.style("No mining performance tracker selected. Aborting.", fg="red"))
        return "b"

    return manage_single_mining_performance_tracker_menu(
        tracker=selected,
        configuration_service=configuration_service,
        adapter_service=adapter_service,
        logger=logger,
    )


def mining_performance_tracker_menu(
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
    adapter_service: Optional[AdapterServiceInterface] = None,
) -> str:
    """Menu for managing Mining Performance Trackers."""
    while True:
        click.echo("\n" + click.style("--- MINING PERFORMANCE TRACKER MENU ---", fg="blue", bold=True))
        click.echo("1. Add Tracker")
        click.echo("2. List Trackers")
        click.echo("3. Manage Tracker")
        click.echo("")
        click.echo("b. Back to main menu")
        click.echo("q. Close application")
        click.echo("-----------------")

        choice: str = click.prompt("Choose an option", type=str)
        choice = choice.strip().lower()
        click.clear()

        if choice == "1":
            handle_add_mining_performance_tracker(configuration_service, logger)
        elif choice == "2":
            handle_list_mining_performance_trackers(configuration_service, logger)
        elif choice == "3":
            sub_choice = handle_manage_mining_performance_tracker(
                configuration_service=configuration_service,
                adapter_service=adapter_service,
                logger=logger,
            )
            if sub_choice == "q":
                choice = "q"
                break
        elif choice == "b":
            break
        elif choice == "q":
            break
        else:
            click.echo(click.style("Invalid choice. Try again.", fg="red"))
            click.pause("Press any key to return to the menu...")

    return choice

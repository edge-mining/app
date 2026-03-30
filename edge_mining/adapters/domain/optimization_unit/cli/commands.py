"""CLI commands for the Energy Optimization Unit domain."""

from typing import List, Optional, Union

import click

from edge_mining.adapters.domain.energy.cli.commands import print_energy_source_details, select_energy_source
from edge_mining.adapters.domain.miner.cli.commands import print_miner_details, select_miner
from edge_mining.adapters.domain.notification.cli.commands import print_notifier_details, select_notifier
from edge_mining.adapters.domain.policy.cli.commands import (
    print_optimization_policy_details,
    select_optimization_policy,
)
from edge_mining.application.interfaces import ConfigurationServiceInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy
from edge_mining.shared.logging.port import LoggerPort

from edge_mining.adapters.utils import run_async_func


def handle_add_optimization_unit(configuration_service: ConfigurationServiceInterface, logger: LoggerPort):
    """Menu to add a new optimization unit."""

    click.echo(click.style("\n--- Creates a new Energy Optimization Unit ---", fg="yellow"))

    name: str = click.prompt("Name of the energy optimization unit", type=str)
    description: str = click.prompt("Description (optional)", type=str, default="")

    # Select an energy source
    click.echo("")
    click.echo(click.style("What Energy Source do you want to use?", fg="yellow"))
    selected_energy_source: Optional[EnergySource] = select_energy_source(configuration_service, logger)
    if not selected_energy_source:
        click.echo(click.style("No energy source selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return

    # Select an optimization policy
    click.echo("")
    click.echo(click.style("What Optimization Policy do you want to use?", fg="yellow"))
    selected_policy: Optional[OptimizationPolicy] = select_optimization_policy(configuration_service)
    if not selected_policy:
        click.echo(click.style("No optimization policy selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return

    # Select target miners
    click.echo("")
    click.echo(click.style("What Target Miners do you want to control?", fg="yellow"))
    selected_miners: Union[Optional[Miner], List[Miner]] = select_miner(
        configuration_service=configuration_service, logger=logger, default_id=None, allow_multiple=True
    )
    if not selected_miners:
        click.echo(click.style("No target miners selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return
    if isinstance(selected_miners, Miner):
        selected_miners = [selected_miners]

    # Select notifiers
    click.echo("")
    click.echo(click.style("What Notifiers do you want to use?", fg="yellow"))
    selected_notifiers: Union[Optional[Notifier], List[Notifier]] = select_notifier(
        configuration_service=configuration_service,
        logger=logger,
        default_id=None,
        allow_multiple=True,
    )
    if isinstance(selected_notifiers, Notifier):
        selected_notifiers = [selected_notifiers]

    # To be implemented in the next release
    home_forecast_provider_id = None
    performance_tracker_id = None

    try:
        target_miner_ids = [m.id for m in selected_miners] if selected_miners else []
        notifier_ids = [n.id for n in selected_notifiers] if selected_notifiers else []

        created = run_async_func(
            configuration_service.create_optimization_unit(
                name=name,
                description=description if description else None,
                energy_source_id=selected_energy_source.id if selected_energy_source else None,
                target_miner_ids=target_miner_ids,
                policy_id=selected_policy.id if selected_policy else None,
                home_forecast_provider_id=home_forecast_provider_id,
                performance_tracker_id=performance_tracker_id,
                notifier_ids=notifier_ids,
            )
        )
        if not created:
            raise ValueError("Failed to create the optimization unit.")
        click.echo(
            click.style(
                f"Energy Optimization Unit '{created.name}' successfully created (ID: {created.id}).",
                fg="green",
            )
        )
    except Exception as e:
        logger.error(f"Error creating optimization unit: {e}")
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
    click.pause("Press any key to return to the menu...")


def list_optimization_units(
    configuration_service: ConfigurationServiceInterface,
) -> None:
    """List all configured optimization units."""
    units = configuration_service.list_optimization_units()
    if not units:
        click.echo(click.style("No optimization units configured.", fg="yellow"))
    else:
        for u in units:
            click.echo(
                "-> "
                + "Name: "
                + click.style(f"{u.name}, ", fg="blue")
                + "ID: "
                + click.style(f"{u.id}, ", fg="yellow")
                + "Description: "
                + click.style(f"{u.description if u.description else 'N/A'}, ", fg="cyan")
            )


def handle_list_optimization_units(
    configuration_service: ConfigurationServiceInterface,
) -> None:
    """Menu to list all configured optimization units."""
    click.echo(click.style("\n--- Configured Energy Optimization Units ---", fg="yellow"))

    list_optimization_units(configuration_service)

    click.pause("Press any key to return to the menu...")


def print_optimization_unit_details(
    optimization_unit: EnergyOptimizationUnit, configuration_service: ConfigurationServiceInterface
) -> None:
    """Print details of a specific optimization unit."""
    energy_source = (
        configuration_service.get_energy_source(optimization_unit.energy_source_id)
        if optimization_unit.energy_source_id
        else None
    )
    policy = configuration_service.get_policy(optimization_unit.policy_id) if optimization_unit.policy_id else None
    miners = (
        [configuration_service.get_miner(m_id) for m_id in optimization_unit.target_miner_ids]
        if optimization_unit.target_miner_ids
        else []
    )
    notifiers = (
        [configuration_service.get_notifier(n_id) for n_id in optimization_unit.notifier_ids]
        if optimization_unit.notifier_ids
        else []
    )

    click.echo("")
    click.echo("| Name: " + click.style(optimization_unit.name, fg="blue"))
    click.echo("| ID: " + click.style(optimization_unit.id, fg="yellow"))
    click.echo(
        "| Description: "
        + click.style(
            optimization_unit.description if optimization_unit.description else "N/A",
            fg="cyan",
        )
    )
    click.echo(
        "| Enabled: "
        + click.style(
            "Yes" if optimization_unit.is_enabled else "No", fg="green" if optimization_unit.is_enabled else "red"
        )
    )

    click.echo("")
    click.echo("> Energy Source Details:")
    if energy_source:
        print_energy_source_details(
            energy_source=energy_source,
            configuration_service=configuration_service,
            show_energy_monitor_details=False,
            show_forecast_provider_details=False,
        )
    else:
        click.echo(click.style("| No energy source configured.", fg="red"))

    click.echo("> Target Miners Details:")
    if miners:
        for miner_idx, miner in enumerate(miners):
            if miner:
                click.echo("|---- Miner " + str(miner_idx + 1) + " ----")
                print_miner_details(
                    miner=miner,
                    configuration_service=configuration_service,
                    show_controller_details=False,
                    show_external_service=False,
                )
                click.echo("--------------------")
    else:
        click.echo(click.style("| No target miners configured.", fg="red"))

    click.echo("> Optimization Policy Details:")
    if policy:
        print_optimization_policy_details(policy=policy, show_rule_details=False)
    else:
        click.echo(click.style("| No optimization policy configured.", fg="red"))

    click.echo("> Notifiers Details:")
    if notifiers:
        for notifier_idx, notifier in enumerate(notifiers):
            if notifier:
                click.echo("|---- Notifier " + str(notifier_idx + 1) + " ----")
                print_notifier_details(
                    notifier=notifier,
                    configuration_service=configuration_service,
                    show_external_service=False,
                    show_optimization_unit_list=False,
                )
                click.echo("--------------------")
    else:
        click.echo(click.style("| No notifiers configured.", fg="red"))


def handle_activate_optimization_unit(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
) -> None:
    """Activate an optimization unit."""
    if optimization_unit.is_enabled:
        click.echo(click.style("The optimization unit is already active.", fg="yellow"))
        click.pause("Press any key to return to the menu...")
        return

    try:
        run_async_func(configuration_service.activate_optimization_unit(optimization_unit.id))
        click.echo(click.style("Optimization unit activated successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error activating optimization unit: {e}", fg="red"))

    click.pause("Press any key to return to the menu...")


def handle_deactivate_optimization_unit(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
) -> None:
    """Deactivate an optimization unit."""
    if not optimization_unit.is_enabled:
        click.echo(click.style("The optimization unit is already inactive.", fg="yellow"))
        click.pause("Press any key to return to the menu...")
        return

    try:
        run_async_func(configuration_service.deactivate_optimization_unit(optimization_unit.id))
        click.echo(click.style("Optimization unit deactivated successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error deactivating optimization unit: {e}", fg="red"))

    click.pause("Press any key to return to the menu...")


def update_optimization_unit(
    optimization_unit: EnergyOptimizationUnit, configuration_service: ConfigurationServiceInterface, logger: LoggerPort
) -> Optional[EnergyOptimizationUnit]:
    """Update an optimization unit."""
    click.echo(click.style("\n--- Update Energy Optimization Unit ---", fg="yellow"))

    name: str = click.prompt(
        "Name of the energy optimization unit",
        type=str,
        default=optimization_unit.name,
    )
    description: str = click.prompt(
        "Description (optional)",
        type=str,
        default=optimization_unit.description if optimization_unit.description else "",
    )

    new_optimization_unit: EnergyOptimizationUnit = EnergyOptimizationUnit()
    new_optimization_unit.name = name
    new_optimization_unit.description = description
    new_optimization_unit.is_enabled = optimization_unit.is_enabled
    new_optimization_unit.energy_source_id = optimization_unit.energy_source_id
    new_optimization_unit.target_miner_ids = optimization_unit.target_miner_ids
    new_optimization_unit.policy_id = optimization_unit.policy_id
    new_optimization_unit.notifier_ids = optimization_unit.notifier_ids
    new_optimization_unit.home_forecast_provider_id = optimization_unit.home_forecast_provider_id
    new_optimization_unit.performance_tracker_id = optimization_unit.performance_tracker_id

    click.echo("\nDo you want to change the energy source?")
    change_energy_source: bool = click.confirm("Change energy source?", default=True, prompt_suffix="")
    if change_energy_source:
        selected_energy_source: Optional[EnergySource] = select_energy_source(configuration_service, logger)
        if selected_energy_source is None:
            click.echo(click.style("Invalid energy source selected. Aborting operation.", fg="red"), err=True)
            return None
        # Update energy source
        new_optimization_unit.energy_source_id = selected_energy_source.id

    click.echo("\nDo you want to change the optimization policy?")
    change_policy: bool = click.confirm("Change optimization policy?", default=True, prompt_suffix="")
    if change_policy:
        selected_policy: Optional[OptimizationPolicy] = select_optimization_policy(configuration_service)
        if selected_policy is None:
            click.echo(click.style("Invalid optimization policy selected. Aborting operation.", fg="red"), err=True)
            return None
        # Update policy
        new_optimization_unit.policy_id = selected_policy.id

    click.echo("\nDo you want to change the target miners?")
    change_miners: bool = click.confirm("Change target miners?", default=True, prompt_suffix="")
    if change_miners:
        selected_miners: Union[Optional[Miner], List[Miner]] = select_miner(
            configuration_service=configuration_service,
            logger=logger,
            default_id=None,
            allow_multiple=True,
        )
        if not selected_miners:
            click.echo(click.style("No target miners selected. Aborting operation.", fg="red"), err=True)
            return None
        if isinstance(selected_miners, Miner):
            selected_miners = [selected_miners]
        new_optimization_unit.target_miner_ids = [m.id for m in selected_miners]

    click.echo("\nDo you want to change the notifiers?")
    change_notifiers: bool = click.confirm("Change notifiers?", default=True, prompt_suffix="")
    if change_notifiers:
        selected_notifiers: Union[Optional[Notifier], List[Notifier]] = select_notifier(
            configuration_service=configuration_service,
            logger=logger,
            default_id=None,
            allow_multiple=True,
        )
        if isinstance(selected_notifiers, Notifier):
            selected_notifiers = [selected_notifiers]
        new_optimization_unit.notifier_ids = [n.id for n in selected_notifiers] if selected_notifiers else []

    # Home forecast provider and performance tracker updates will be implemented in the next release

    try:
        updated = run_async_func(
            configuration_service.update_optimization_unit(
                unit_id=optimization_unit.id,
                name=new_optimization_unit.name,
                description=new_optimization_unit.description,
                energy_source_id=new_optimization_unit.energy_source_id,
                target_miner_ids=new_optimization_unit.target_miner_ids,
                policy_id=new_optimization_unit.policy_id,
                home_forecast_provider_id=new_optimization_unit.home_forecast_provider_id,
                performance_tracker_id=new_optimization_unit.performance_tracker_id,
                notifier_ids=new_optimization_unit.notifier_ids,
                is_enabled=new_optimization_unit.is_enabled,
            )
        )
        click.echo(
            click.style(
                f"Energy Optimization Unit '{updated.name}' successfully updated.",
                fg="green",
            )
        )
    except Exception as e:
        updated = None
        logger.error(f"Error updating optimization unit: {e}")
        click.echo(click.style(f"Error updating optimization unit: {e}", fg="red"), err=True)
        return None
    finally:
        click.pause("Press any key to return to the menu...")

    return updated


def delete_single_optimization_unit(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
) -> bool:
    """Delete a single optimization unit."""
    confirm_delete: bool = click.confirm(
        f"Are you sure you want to delete the optimization unit '{optimization_unit.name}' "
        f"(ID: {optimization_unit.id})?",
        default=False,
        prompt_suffix="",
    )
    if not confirm_delete:
        click.echo(click.style("Deletion cancelled.", fg="yellow"))
        return False

    try:
        run_async_func(configuration_service.remove_optimization_unit(optimization_unit.id))
        click.echo(click.style("Optimization unit deleted successfully.", fg="green"))
        return True
    except Exception as e:
        click.echo(click.style(f"Error deleting optimization unit: {e}", fg="red"))
        return False


def manage_assign_energy_source(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Assign an energy source to an optimization unit."""
    click.echo(click.style("\n--- Assign Energy Source to Optimization Unit ---", fg="yellow"))

    selected_energy_source: Optional[EnergySource] = select_energy_source(configuration_service, logger)
    if not selected_energy_source:
        click.echo(click.style("No energy source selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return

    try:
        run_async_func(
            configuration_service.assign_energy_source_to_optimization_unit(
                unit_id=optimization_unit.id, energy_source_id=selected_energy_source.id
            )
        )
        click.echo(click.style(f"Energy source '{selected_energy_source.name}' assigned successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error assigning energy source: {e}")
        click.echo(click.style(f"Error assigning energy source: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_assign_optimization_policy(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
) -> None:
    """Assign an optimization policy to an optimization unit."""
    click.echo(click.style("\n--- Assign Optimization Policy to Optimization Unit ---", fg="yellow"))

    selected_policy: Optional[OptimizationPolicy] = select_optimization_policy(configuration_service)
    if not selected_policy:
        click.echo(click.style("No optimization policy selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return

    try:
        run_async_func(
            configuration_service.assign_policy_to_optimization_unit(
                unit_id=optimization_unit.id, policy_id=selected_policy.id
            )
        )
        click.echo(click.style(f"Optimization policy '{selected_policy.name}' assigned successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error assigning optimization policy: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_assign_target_miners(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Assign target miners to an optimization unit."""
    click.echo(click.style("\n--- Assign Target Miners to Optimization Unit ---", fg="yellow"))

    selected_miners: Union[Optional[Miner], List[Miner]] = select_miner(
        configuration_service=configuration_service, logger=logger, default_id=None, allow_multiple=True
    )
    if not selected_miners:
        click.echo(click.style("No target miners selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return
    if isinstance(selected_miners, Miner):
        selected_miners = [selected_miners]

    try:
        target_miner_ids = [m.id for m in selected_miners]
        run_async_func(
            configuration_service.assign_miners_to_optimization_unit(
                unit_id=optimization_unit.id, miner_ids=target_miner_ids
            )
        )
        click.echo(click.style(f"{len(selected_miners)} Target miners assigned successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error assigning target miners: {e}")
        click.echo(click.style(f"Error assigning target miners: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_add_target_miner(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Add a target miner to an optimization unit."""
    click.echo(click.style("\n--- Add Target Miner to Optimization Unit ---", fg="yellow"))

    selected_miner: Union[Optional[Miner], List[Miner]] = select_miner(
        configuration_service=configuration_service,
        logger=logger,
        default_id=None,
        allow_multiple=False,
        exclude_ids=optimization_unit.target_miner_ids,
    )
    if not selected_miner:
        click.echo(click.style("No target miner selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return
    if isinstance(selected_miner, list):
        selected_miner = selected_miner[0]

    # Check if the miner already exists in the optimization unit
    if selected_miner.id in optimization_unit.target_miner_ids:
        click.echo(
            click.style(
                f"Target miner '{selected_miner.name}' is already assigned to this optimization unit.", fg="red"
            )
        )
        click.pause("Press any key to return to the menu...")
        return

    try:
        run_async_func(
            configuration_service.add_miner_to_optimization_unit(
                unit_id=optimization_unit.id, miner_id=selected_miner.id
            )
        )
        click.echo(click.style(f"Target miner '{selected_miner.name}' added successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error adding target miner: {e}")
        click.echo(click.style(f"Error adding target miner: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_remove_target_miner(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Remove a target miner from an optimization unit."""
    click.echo(click.style("\n--- Remove Target Miner from Optimization Unit ---", fg="yellow"))

    if not optimization_unit.target_miner_ids:
        click.echo(click.style("No target miners assigned to this optimization unit.", fg="red"))
        click.pause("Press any key to return to the menu...")
        return

    selected_miner: Union[Optional[Miner], List[Miner]] = select_miner(
        configuration_service=configuration_service,
        logger=logger,
        default_id=None,
        allow_multiple=False,
        only_ids=optimization_unit.target_miner_ids,
    )
    if not selected_miner:
        click.echo(click.style("No target miner selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return
    if isinstance(selected_miner, list):
        selected_miner = selected_miner[0]

    try:
        run_async_func(
            configuration_service.remove_miner_from_optimization_unit(
                unit_id=optimization_unit.id, miner_id=selected_miner.id
            )
        )
        click.echo(click.style(f"Target miner '{selected_miner.name}' removed successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error removing target miner: {e}")
        click.echo(click.style(f"Error removing target miner: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_assign_notifiers(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Assign notifiers to an optimization unit."""
    click.echo(click.style("\n--- Assign Notifiers to Optimization Unit ---", fg="yellow"))

    selected_notifiers: Union[Optional[Notifier], List[Notifier]] = select_notifier(
        configuration_service=configuration_service,
        logger=logger,
        default_id=None,
        allow_multiple=True,
    )
    if isinstance(selected_notifiers, Notifier):
        selected_notifiers = [selected_notifiers]

    try:
        notifier_ids = [n.id for n in selected_notifiers] if selected_notifiers else []
        run_async_func(
            configuration_service.assign_notifiers_to_optimization_unit(
                unit_id=optimization_unit.id, notifier_ids=notifier_ids
            )
        )
        click.echo(click.style(f"{len(notifier_ids)} Notifiers assigned successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error assigning notifiers: {e}")
        click.echo(click.style(f"Error assigning notifiers: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_add_notifier(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Add a notifier to an optimization unit."""
    click.echo(click.style("\n--- Add Notifier to Optimization Unit ---", fg="yellow"))

    selected_notifier: Union[Optional[Notifier], List[Notifier]] = select_notifier(
        configuration_service=configuration_service,
        logger=logger,
        default_id=None,
        allow_multiple=False,
        exclude_ids=optimization_unit.notifier_ids,
    )
    if not selected_notifier:
        click.echo(click.style("No notifier selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return
    if isinstance(selected_notifier, list):
        selected_notifier = selected_notifier[0]

    try:
        run_async_func(
            configuration_service.add_notifier_to_optimization_unit(
                unit_id=optimization_unit.id, notifier_id=selected_notifier.id
            )
        )
        click.echo(click.style(f"Notifier '{selected_notifier.name}' added successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error adding notifier: {e}")
        click.echo(click.style(f"Error adding notifier: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_remove_notifier(
    optimization_unit: EnergyOptimizationUnit,
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> None:
    """Remove a notifier from an optimization unit."""
    click.echo(click.style("\n--- Remove Notifier from Optimization Unit ---", fg="yellow"))

    if not optimization_unit.notifier_ids:
        click.echo(click.style("No notifiers assigned to this optimization unit.", fg="red"))
        click.pause("Press any key to return to the menu...")
        return

    selected_notifier: Union[Optional[Notifier], List[Notifier]] = select_notifier(
        configuration_service=configuration_service,
        logger=logger,
        default_id=None,
        allow_multiple=False,
        only_ids=optimization_unit.notifier_ids,
    )
    if isinstance(selected_notifier, list):
        selected_notifier = selected_notifier[0]

    if not selected_notifier:
        click.echo(click.style("No notifier selected. Aborting operation.", fg="red"), err=True)
        click.pause("Press any key to return to the menu...")
        return

    try:
        run_async_func(
            configuration_service.remove_notifier_from_optimization_unit(
                unit_id=optimization_unit.id, notifier_id=selected_notifier.id
            )
        )
        click.echo(click.style(f"Notifier '{selected_notifier.name}' removed successfully.", fg="green"))
    except Exception as e:
        logger.error(f"Error removing notifier: {e}")
        click.echo(click.style(f"Error removing notifier: {e}", fg="red"))
    click.pause("Press any key to return to the menu...")


def manage_single_optimization_unit_menu(
    unit_id: EntityId, configuration_service: ConfigurationServiceInterface, logger: LoggerPort
) -> str:
    """Menu for managing a single optimization unit."""
    while True:
        # Refresh optimization unit data
        optimization_unit = configuration_service.get_optimization_unit(unit_id)
        if not optimization_unit:
            click.echo(click.style("Optimization unit not found. Returning to previous menu.", fg="red"))
            return "b"

        click.clear()
        click.echo(
            click.style(
                f"=== Manage Optimization Unit: {optimization_unit.name} ===",
                fg="yellow",
            )
        )

        print_optimization_unit_details(optimization_unit, configuration_service)

        click.echo("")
        click.echo("")

        click.echo("1. Activate optimization unit")
        click.echo("2. Deactivate optimization unit")
        click.echo("3. Update optimization unit")
        click.echo("4. Delete optimization unit")
        click.echo("")
        click.echo("5. Assign Energy Source")
        click.echo("6. Assign Optimization Policy")
        click.echo("7. Assign Target Miners")
        click.echo("8. Add a Target Miner")
        click.echo("9. Remove a Target Miner")
        click.echo("10. Assign Notifiers")
        click.echo("11. Add a Notifier")
        click.echo("12. Remove a Notifier")
        click.echo("")
        click.echo("b. Back to optimization unit menu")
        click.echo("q. Close application")
        click.echo("-----------------")

        choice: str = click.prompt("Choose an option", type=str, default="b")
        choice = choice.strip().lower()

        if choice == "1":
            handle_activate_optimization_unit(optimization_unit, configuration_service)
            continue
        elif choice == "2":
            handle_deactivate_optimization_unit(optimization_unit, configuration_service)
            continue
        elif choice == "3":
            updated_optimization_unit = update_optimization_unit(optimization_unit, configuration_service, logger)
            optimization_unit = updated_optimization_unit or optimization_unit
            continue
        elif choice == "4":
            delete_status = delete_single_optimization_unit(optimization_unit, configuration_service)
            if delete_status:
                return "b"
            continue
        elif choice == "5":
            manage_assign_energy_source(optimization_unit, configuration_service, logger)
            continue
        elif choice == "6":
            manage_assign_optimization_policy(optimization_unit, configuration_service)
            continue
        elif choice == "7":
            manage_assign_target_miners(optimization_unit, configuration_service, logger)
            continue
        elif choice == "8":
            manage_add_target_miner(optimization_unit, configuration_service, logger)
            continue
        elif choice == "9":
            manage_remove_target_miner(optimization_unit, configuration_service, logger)
            continue
        elif choice == "10":
            manage_assign_notifiers(optimization_unit, configuration_service, logger)
            continue
        elif choice == "11":
            manage_add_notifier(optimization_unit, configuration_service, logger)
            continue
        elif choice == "12":
            manage_remove_notifier(optimization_unit, configuration_service, logger)
            continue
        elif choice == "b":
            break
        elif choice == "q":
            break
        else:
            click.echo(click.style("Invalid choice. Try again.", fg="red"))
            click.pause("Press any key to return to the menu...")

    return choice


def select_optimization_unit(
    configuration_service: ConfigurationServiceInterface, logger: LoggerPort, default_id: Optional[EntityId] = None
) -> Optional[EnergyOptimizationUnit]:
    """Select an optimization unit."""
    click.echo(click.style("\n--- Select an Energy Optimization Unit ---", fg="yellow"))

    units = configuration_service.list_optimization_units()
    if not units:
        click.echo(click.style("No optimization units configured.", fg="red"))
        return None

    default_idx = ""
    for idx, unit in enumerate(units):
        click.echo(
            f"{idx}. "
            + "Name: "
            + click.style(f"{unit.name}, ", fg="blue")
            + "ID: "
            + click.style(f"{unit.id}, ", fg="yellow")
            + "Description: "
            + click.style(f"{unit.description if unit.description else 'N/A'}, ", fg="cyan")
            + "Enabled: "
            + click.style(f"{'Yes' if unit.is_enabled else 'No'}", fg="green" if unit.is_enabled else "red")
        )

        if default_id:
            if unit.id == default_id:
                default_idx = str(idx)

    click.echo("\nb. Back to menu\n")

    unit_idx: str = click.prompt("Choose an optimization unit index", type=str, default=default_idx)
    unit_idx = unit_idx.strip().lower()
    if unit_idx == "b":
        return None

    if not unit_idx.isdigit() or int(unit_idx) < 0 or int(unit_idx) >= len(units):
        click.echo(click.style("Invalid optimization unit index selected.", fg="red"))
        return None

    selected_unit = units[int(unit_idx)]
    return selected_unit


def handle_manage_optimization_unit(
    configuration_service: ConfigurationServiceInterface,
    logger: LoggerPort,
) -> str:
    """Menu to manage a specific optimization unit."""
    selected_optimization_unit = select_optimization_unit(configuration_service, logger)

    if not selected_optimization_unit:
        click.echo(click.style("No optimization unit selected. Aborting.", fg="red"))
        return "b"

    choice = manage_single_optimization_unit_menu(
        unit_id=selected_optimization_unit.id, configuration_service=configuration_service, logger=logger
    )

    return choice


def optimization_unit_menu(configuration_service: ConfigurationServiceInterface, logger: LoggerPort) -> str:
    """Menu for managing Optimization Units."""
    while True:
        click.echo("\n" + click.style("--- MENU ENERGY OPTIMIZATION UNIT ---", fg="yellow", bold=True))
        click.echo("1. Add an Energy Optimization Unit")
        click.echo("2. List all Energy Optimization Units")
        click.echo("3. Manage an Energy Optimization Unit")
        click.echo("")
        click.echo("b. Back to main menu")
        click.echo("q. Close application")
        click.echo("---------------------------------")

        choice: str = click.prompt("Choose an option", type=str)
        choice = choice.strip().lower()

        click.clear()

        if choice == "1":
            handle_add_optimization_unit(configuration_service=configuration_service, logger=logger)
        elif choice == "2":
            handle_list_optimization_units(configuration_service=configuration_service)
        elif choice == "3":
            sub_choice = handle_manage_optimization_unit(configuration_service=configuration_service, logger=logger)
            if sub_choice == "q":
                break
        elif choice == "b":
            break
        elif choice == "q":
            break
        else:
            click.echo(click.style("Invalid choice. Try again.", fg="red"))
            click.pause("Press any key to return to the menu...")

    return choice

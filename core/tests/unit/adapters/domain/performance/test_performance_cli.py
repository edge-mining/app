"""Smoke tests for the mining performance tracker CLI helpers."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from click.testing import CliRunner

from edge_mining.adapters.domain.performance.cli.commands import (
    delete_single_mining_performance_tracker,
    handle_add_mining_performance_tracker,
    handle_list_mining_performance_trackers,
    handle_tracker_braiins_config,
    handle_tracker_configuration,
    handle_tracker_dummy_config,
    handle_tracker_ocean_config,
    print_tracker_details,
    select_mining_performance_tracker_adapter,
    check_single_mining_performance_tracker,
    update_single_mining_performance_tracker,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.performance.common import (
    MiningPerformanceTrackerAdapter,
    PayoutFrequency,
    Satoshi,
)
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.exceptions import MiningPoolAuthError
from edge_mining.domain.performance.value_objects import PayoutSchedule
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
    MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerOceanConfig,
)


@pytest.fixture
def logger() -> MagicMock:
    """Return a mock logger port."""
    return MagicMock()


@pytest.fixture
def configuration_service() -> MagicMock:
    """Return a mock ConfigurationServiceInterface."""
    return MagicMock()


@pytest.fixture
def adapter_service() -> MagicMock:
    """Return a mock AdapterServiceInterface."""
    return MagicMock()


def _make_tracker(
    adapter_type: MiningPerformanceTrackerAdapter = MiningPerformanceTrackerAdapter.DUMMY,
) -> MiningPerformanceTracker:
    """Create a tracker fixture for tests."""
    if adapter_type == MiningPerformanceTrackerAdapter.OCEAN:
        config = MiningPerformanceTrackerOceanConfig(bitcoin_address="bc1qtest")
    elif adapter_type == MiningPerformanceTrackerAdapter.BRAIINS_POOL:
        config = MiningPerformanceTrackerBraiinsPoolConfig(api_token="tok")
    else:
        config = MiningPerformanceTrackerDummyConfig(message="hi")

    return MiningPerformanceTracker(
        id=EntityId(uuid.uuid4()),
        name=f"test-{adapter_type.value}",
        adapter_type=adapter_type,
        config=config,
    )


# -- Adapter selection --------------------------------------------------------


def test_select_adapter_returns_selected_enum() -> None:
    """Valid numeric input selects the matching adapter."""
    runner = CliRunner()
    result = runner.invoke(_wrap(select_mining_performance_tracker_adapter), input="1\n")
    assert result.exit_code == 0
    # The function itself returns the enum; CliRunner captures only stdout.
    # We verify side-effects instead by checking the echoed options.
    assert "OCEAN" in result.output or "DUMMY" in result.output


def test_select_adapter_rejects_out_of_range() -> None:
    """Invalid index prints an error and returns None (exit 0)."""
    runner = CliRunner()
    result = runner.invoke(_wrap(select_mining_performance_tracker_adapter), input="99\n")
    assert result.exit_code == 0
    assert "Invalid index" in result.output


# -- Configuration handlers ---------------------------------------------------


def test_dummy_config_handler_uses_default_message() -> None:
    """The dummy config handler yields a DummyConfig entity with entered message."""
    runner = CliRunner()
    result = runner.invoke(_wrap(handle_tracker_dummy_config), input="\n")
    assert result.exit_code == 0


def test_ocean_config_handler_builds_ocean_config() -> None:
    """The Ocean config handler builds an Ocean config with the entered values."""
    runner = CliRunner()
    result = runner.invoke(
        _wrap(handle_tracker_ocean_config),
        input="bc1qtest\n\n\n",
    )
    assert result.exit_code == 0
    assert "Bitcoin payout address" in result.output


def test_braiins_config_handler_builds_braiins_config() -> None:
    """The Braiins config handler builds a Braiins config with the entered token."""
    runner = CliRunner()
    result = runner.invoke(
        _wrap(handle_tracker_braiins_config),
        input="token\n\n\n",
    )
    assert result.exit_code == 0


def test_handle_tracker_configuration_dispatches_to_dummy() -> None:
    """handle_tracker_configuration returns a DummyConfig for the DUMMY adapter."""
    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_arg(handle_tracker_configuration, MiningPerformanceTrackerAdapter.DUMMY),
        input="\n",
    )
    assert result.exit_code == 0


# -- List / select / print ----------------------------------------------------


def test_handle_list_empty(configuration_service: MagicMock, logger: MagicMock) -> None:
    """Empty list path is exercised without errors."""
    configuration_service.list_mining_performance_trackers.return_value = []
    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_args(
            handle_list_mining_performance_trackers,
            configuration_service,
            logger,
        ),
        input="\n",
    )
    assert result.exit_code == 0
    assert "No mining performance trackers" in result.output


def test_handle_list_populated(configuration_service: MagicMock, logger: MagicMock) -> None:
    """Populated list prints every tracker."""
    trackers = [
        _make_tracker(MiningPerformanceTrackerAdapter.DUMMY),
        _make_tracker(MiningPerformanceTrackerAdapter.OCEAN),
    ]
    configuration_service.list_mining_performance_trackers.return_value = trackers
    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_args(
            handle_list_mining_performance_trackers,
            configuration_service,
            logger,
        ),
        input="\n",
    )
    assert result.exit_code == 0
    assert "DUMMY" in result.output
    assert "OCEAN" in result.output


def test_print_tracker_details_includes_config() -> None:
    """print_tracker_details prints name, ID, adapter and config class."""
    tracker = _make_tracker(MiningPerformanceTrackerAdapter.DUMMY)
    runner = CliRunner()
    result = runner.invoke(_wrap_with_arg(print_tracker_details, tracker))
    assert result.exit_code == 0
    assert tracker.name in result.output
    assert "MiningPerformanceTrackerDummyConfig" in result.output


# -- Add ----------------------------------------------------------------------


def test_handle_add_invokes_configuration_service(configuration_service: MagicMock, logger: MagicMock) -> None:
    """handle_add_mining_performance_tracker calls add on the service when config is valid."""
    added_tracker = _make_tracker(MiningPerformanceTrackerAdapter.DUMMY)
    configuration_service.add_mining_performance_tracker = AsyncMock(return_value=added_tracker)

    runner = CliRunner()
    # name, adapter choice 0 (DUMMY), dummy message default, then pause
    result = runner.invoke(
        _wrap_with_args(handle_add_mining_performance_tracker, configuration_service, logger),
        input="test\n0\n\n\n",
    )
    assert result.exit_code == 0
    configuration_service.add_mining_performance_tracker.assert_awaited_once()


# -- Update -------------------------------------------------------------------


def test_update_single_keeps_configuration_when_declined(configuration_service: MagicMock, logger: MagicMock) -> None:
    """Declining the configuration change still forwards the existing config."""
    tracker = _make_tracker(MiningPerformanceTrackerAdapter.DUMMY)
    configuration_service.update_mining_performance_tracker = AsyncMock(return_value=tracker)

    runner = CliRunner()
    # default name confirmed, "n" to skip config change, pause prompt accepts anything
    result = runner.invoke(
        _wrap_with_args(
            update_single_mining_performance_tracker,
            tracker,
            configuration_service,
            logger,
        ),
        input="\nn\n\n",
    )
    assert result.exit_code == 0
    configuration_service.update_mining_performance_tracker.assert_awaited_once()
    call_kwargs = configuration_service.update_mining_performance_tracker.await_args.kwargs
    assert call_kwargs["config"] is tracker.config


# -- Delete -------------------------------------------------------------------


def test_delete_single_cancels_on_negative_confirm(configuration_service: MagicMock, logger: MagicMock) -> None:
    """The delete helper cancels when the user declines confirmation."""
    tracker = _make_tracker()
    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_args(
            delete_single_mining_performance_tracker,
            tracker,
            configuration_service,
            logger,
        ),
        input="n\n",
    )
    assert result.exit_code == 0
    assert "Deletion cancelled" in result.output
    configuration_service.remove_mining_performance_tracker.assert_not_called()


def test_delete_single_invokes_service_on_confirm(configuration_service: MagicMock, logger: MagicMock) -> None:
    """Confirming deletion forwards the call to the configuration service."""
    tracker = _make_tracker()
    configuration_service.remove_mining_performance_tracker = AsyncMock(return_value=tracker)

    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_args(
            delete_single_mining_performance_tracker,
            tracker,
            configuration_service,
            logger,
        ),
        input="y\n",
    )
    assert result.exit_code == 0
    configuration_service.remove_mining_performance_tracker.assert_awaited_once()


# -- Test tracker -------------------------------------------------------------


def test_test_single_reports_reachable(adapter_service: MagicMock, logger: MagicMock) -> None:
    """When the port returns a payout schedule the helper reports reachability."""
    tracker = _make_tracker()
    port = MagicMock()
    port.get_payout_schedule = AsyncMock(
        return_value=PayoutSchedule(frequency=PayoutFrequency.THRESHOLD, threshold=Satoshi(100_000))
    )
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=port)

    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_args(
            check_single_mining_performance_tracker,
            tracker,
            adapter_service,
            logger,
        )
    )
    assert result.exit_code == 0
    assert "Tracker reachable" in result.output


def test_test_single_reports_auth_error(adapter_service: MagicMock, logger: MagicMock) -> None:
    """Auth errors from the pool are surfaced on stderr without aborting the CLI."""
    tracker = _make_tracker()
    port = MagicMock()
    port.get_payout_schedule = AsyncMock(side_effect=MiningPoolAuthError("bad token"))
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=port)

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(
        _wrap_with_args(
            check_single_mining_performance_tracker,
            tracker,
            adapter_service,
            logger,
        )
    )
    assert result.exit_code == 0
    assert "Authentication failed" in result.stderr


def test_test_single_when_port_missing(adapter_service: MagicMock, logger: MagicMock) -> None:
    """When no port can be resolved the helper reports the tracker as unavailable."""
    tracker = _make_tracker()
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=None)

    runner = CliRunner()
    result = runner.invoke(
        _wrap_with_args(
            check_single_mining_performance_tracker,
            tracker,
            adapter_service,
            logger,
        )
    )
    assert result.exit_code == 0
    assert "Tracker adapter not available" in result.output


# -- Helpers ------------------------------------------------------------------


def _wrap(fn):
    """Wrap a no-arg helper in a click.Command so CliRunner can invoke it."""
    import click

    @click.command()
    def _cmd():
        fn()

    return _cmd


def _wrap_with_arg(fn, arg):
    """Wrap a one-arg helper."""
    import click

    @click.command()
    def _cmd():
        fn(arg)

    return _cmd


def _wrap_with_args(fn, *args):
    """Wrap a multi-arg helper."""
    import click

    @click.command()
    def _cmd():
        fn(*args)

    return _cmd

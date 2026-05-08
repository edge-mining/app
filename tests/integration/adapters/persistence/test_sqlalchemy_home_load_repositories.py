"""Integration tests for SQLAlchemy Home Load repository."""

import pytest

from edge_mining.adapters.domain.home_load.repositories import SqlAlchemyEnergyLoadForecastProviderRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderDummyConfig


class TestSqlAlchemyEnergyLoadForecastProviderRepository:
    """Integration tests for SqlAlchemyEnergyLoadForecastProviderRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyEnergyLoadForecastProviderRepository:
        """Create a EnergyLoadForecastProvider repository instance."""
        return SqlAlchemyEnergyLoadForecastProviderRepository(db=sqlalchemy_repo)

    def test_add_and_get_energy_load_forecast_provider_with_enum_adapter(
        self, repository: SqlAlchemyEnergyLoadForecastProviderRepository
    ):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        provider = EnergyLoadForecastProvider(
            name="Home Forecast Test",
            adapter_type=EnergyLoadForecastProviderAdapter.DUMMY,
            config=EnergyLoadForecastProviderDummyConfig(load_power_max=650.0),
        )
        original_id = provider.id

        repository.add(provider)

        assert provider.adapter_type == EnergyLoadForecastProviderAdapter.DUMMY

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Home Forecast Test"
        assert retrieved.adapter_type == EnergyLoadForecastProviderAdapter.DUMMY
        assert isinstance(retrieved.config, EnergyLoadForecastProviderDummyConfig)

    def test_update_energy_load_forecast_provider_with_enum_adapter(
        self, repository: SqlAlchemyEnergyLoadForecastProviderRepository
    ):
        """Regression test: enum adapter_type must remain valid through update commit."""
        provider = EnergyLoadForecastProvider(
            name="Original Home Forecast",
            adapter_type=EnergyLoadForecastProviderAdapter.DUMMY,
            config=EnergyLoadForecastProviderDummyConfig(load_power_max=400.0),
        )
        repository.add(provider)

        provider.name = "Updated Home Forecast"
        provider.adapter_type = EnergyLoadForecastProviderAdapter.DUMMY
        repository.update(provider)

        assert provider.adapter_type == EnergyLoadForecastProviderAdapter.DUMMY

        retrieved = repository.get_by_id(provider.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Home Forecast"
        assert retrieved.adapter_type == EnergyLoadForecastProviderAdapter.DUMMY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Integration tests for SQLAlchemy Home Load repository."""

import pytest

from edge_mining.adapters.domain.home_load.repositories import SqlAlchemyHomeForecastProviderRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.home_load.common import HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider
from edge_mining.shared.adapter_configs.home_load import HomeForecastProviderDummyConfig


class TestSqlAlchemyHomeForecastProviderRepository:
    """Integration tests for SqlAlchemyHomeForecastProviderRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyHomeForecastProviderRepository:
        """Create a HomeForecastProvider repository instance."""
        return SqlAlchemyHomeForecastProviderRepository(db=sqlalchemy_repo)

    def test_add_and_get_home_forecast_provider_with_enum_adapter(
        self, repository: SqlAlchemyHomeForecastProviderRepository
    ):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        provider = HomeForecastProvider(
            name="Home Forecast Test",
            adapter_type=HomeForecastProviderAdapter.DUMMY,
            config=HomeForecastProviderDummyConfig(load_power_max=650.0),
        )
        original_id = provider.id

        repository.add(provider)

        assert provider.adapter_type == HomeForecastProviderAdapter.DUMMY

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Home Forecast Test"
        assert retrieved.adapter_type == HomeForecastProviderAdapter.DUMMY
        assert isinstance(retrieved.config, HomeForecastProviderDummyConfig)

    def test_update_home_forecast_provider_with_enum_adapter(self, repository: SqlAlchemyHomeForecastProviderRepository):
        """Regression test: enum adapter_type must remain valid through update commit."""
        provider = HomeForecastProvider(
            name="Original Home Forecast",
            adapter_type=HomeForecastProviderAdapter.DUMMY,
            config=HomeForecastProviderDummyConfig(load_power_max=400.0),
        )
        repository.add(provider)

        provider.name = "Updated Home Forecast"
        provider.adapter_type = HomeForecastProviderAdapter.DUMMY
        repository.update(provider)

        assert provider.adapter_type == HomeForecastProviderAdapter.DUMMY

        retrieved = repository.get_by_id(provider.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Home Forecast"
        assert retrieved.adapter_type == HomeForecastProviderAdapter.DUMMY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

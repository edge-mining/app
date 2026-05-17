"""Integration tests for SQLAlchemy Forecast repositories."""

import pytest

from edge_mining.adapters.domain.forecast.repositories import SqlAlchemyForecastProviderRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.shared.adapter_configs.forecast import ForecastProviderDummySolarConfig


class TestSqlAlchemyForecastProviderRepository:
    """Integration tests for SqlAlchemyForecastProviderRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyForecastProviderRepository:
        """Create a ForecastProvider repository instance."""
        return SqlAlchemyForecastProviderRepository(db=sqlalchemy_repo)

    def test_add_and_get_forecast_provider_with_enum_adapter(self, repository: SqlAlchemyForecastProviderRepository):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        provider = ForecastProvider(
            name="Forecast Test Provider",
            adapter_type=ForecastProviderAdapter.DUMMY_SOLAR,
            config=ForecastProviderDummySolarConfig(),
        )
        original_id = provider.id

        # This call used to fail with sqlite3.ProgrammingError when adapter_type was an enum instance.
        repository.add(provider)

        # Entity should still expose enum type after commit.
        assert provider.adapter_type == ForecastProviderAdapter.DUMMY_SOLAR

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Forecast Test Provider"
        assert retrieved.adapter_type == ForecastProviderAdapter.DUMMY_SOLAR
        assert isinstance(retrieved.config, ForecastProviderDummySolarConfig)

    def test_update_forecast_provider_with_enum_adapter(self, repository: SqlAlchemyForecastProviderRepository):
        """Regression test: enum adapter_type must remain valid through update commit."""
        provider = ForecastProvider(
            name="Original Forecast Provider",
            adapter_type=ForecastProviderAdapter.DUMMY_SOLAR,
            config=ForecastProviderDummySolarConfig(),
        )
        repository.add(provider)

        provider.name = "Updated Forecast Provider"
        provider.adapter_type = ForecastProviderAdapter.DUMMY_SOLAR
        repository.update(provider)

        # Entity should still expose enum type after update commit.
        assert provider.adapter_type == ForecastProviderAdapter.DUMMY_SOLAR

        retrieved = repository.get_by_id(provider.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Forecast Provider"
        assert retrieved.adapter_type == ForecastProviderAdapter.DUMMY_SOLAR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

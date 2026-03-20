"""Integration tests for SQLAlchemy External Service repository."""

import pytest

from edge_mining.adapters.infrastructure.external_services.repositories import SqlAlchemyExternalServiceRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.shared.adapter_configs.external_services import ExternalServiceHomeAssistantConfig
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService


class TestSqlAlchemyExternalServiceRepository:
    """Integration tests for SqlAlchemyExternalServiceRepository."""

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyExternalServiceRepository:
        """Create an ExternalService repository instance."""
        return SqlAlchemyExternalServiceRepository(db=sqlalchemy_repo)

    def test_add_and_get_external_service_with_enum_adapter(self, repository: SqlAlchemyExternalServiceRepository):
        """Regression test: enum adapter_type must persist without sqlite binding errors."""
        service = ExternalService(
            name="External Service Test",
            adapter_type=ExternalServiceAdapter.HOME_ASSISTANT_API,
            config=ExternalServiceHomeAssistantConfig(url="http://ha.local", token="token"),
        )
        original_id = service.id

        # This call used to fail with sqlite3.ProgrammingError when adapter_type was an enum instance.
        repository.add(service)

        # Entity should still expose enum type after commit.
        assert service.adapter_type == ExternalServiceAdapter.HOME_ASSISTANT_API

        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "External Service Test"
        assert retrieved.adapter_type == ExternalServiceAdapter.HOME_ASSISTANT_API
        assert isinstance(retrieved.config, ExternalServiceHomeAssistantConfig)

    def test_update_external_service_with_enum_adapter(self, repository: SqlAlchemyExternalServiceRepository):
        """Regression test: enum adapter_type must remain valid through update commit."""
        service = ExternalService(
            name="Original External Service",
            adapter_type=ExternalServiceAdapter.HOME_ASSISTANT_API,
            config=ExternalServiceHomeAssistantConfig(url="http://ha.local", token="token"),
        )
        repository.add(service)

        service.name = "Updated External Service"
        service.adapter_type = ExternalServiceAdapter.HOME_ASSISTANT_API
        repository.update(service)

        # Entity should still expose enum type after update commit.
        assert service.adapter_type == ExternalServiceAdapter.HOME_ASSISTANT_API

        retrieved = repository.get_by_id(service.id)
        assert retrieved is not None
        assert retrieved.name == "Updated External Service"
        assert retrieved.adapter_type == ExternalServiceAdapter.HOME_ASSISTANT_API


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
